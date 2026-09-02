"""运行第九阶段RAGAS对比测评。

用法：python -m evaluation.run_ragas --class-id 1
首次可用 --validate-only 检查30题模板，不调用任何API。
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from app.ai import DeepSeekClient
from app.config import settings
from app.retrieval import hybrid_search, rerank_search, resolve_parent_chunks, vector_search


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "gold_dataset.json"
CATEGORY_COUNTS = {"事实题": 10, "流程或材料题": 8, "跨段落题": 5, "相似政策辨析题": 4, "知识库无答案题": 3}
THRESHOLDS = {"faithfulness": 0.85, "answer_relevancy": 0.80, "context_precision": 0.75, "context_recall": 0.75}


class EvaluationError(Exception):
    pass


@dataclass(frozen=True)
class EvaluationConfig:
    name: str
    label: str
    mode: str
    top_k: int


CONFIGS = (
    EvaluationConfig("vector_small_top3", "仅向量检索＋小块回答（top-3）", "vector_small", 3),
    EvaluationConfig("vector_parent_top3", "Small-to-Big＋仅向量召回（top-3）", "vector_parent", 3),
    EvaluationConfig("full_top3", "Small-to-Big＋混合召回＋Rerank（top-3）", "full", 3),
    EvaluationConfig("full_top5", "Small-to-Big＋混合召回＋Rerank（top-5）", "full", 5),
)


def load_dataset(path: Path = DEFAULT_DATASET) -> list[dict[str, Any]]:
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"无法读取金标集：{path}") from exc
    if not isinstance(items, list) or len(items) != 30:
        raise EvaluationError("金标集必须正好包含30题")
    if Counter(item.get("category") for item in items) != Counter(CATEGORY_COUNTS):
        raise EvaluationError("金标集分类数量必须为10/8/5/4/3")
    ids = [item.get("id") for item in items]
    if len(set(ids)) != len(ids):
        raise EvaluationError("金标集题目ID不能重复")
    required = {"id", "category", "question", "reference_answer", "reference_contexts", "ready"}
    for item in items:
        if not required.issubset(item) or not str(item["question"]).strip():
            raise EvaluationError(f"题目{item.get('id', '未知')}字段不完整")
        if item["ready"] and not str(item["reference_answer"]).strip():
            raise EvaluationError(f"题目{item['id']}已标记ready但没有标准答案")
    return items


def ready_dataset(items: list[dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
    ready = [item for item in items if item["ready"]]
    if limit:
        if not ready:
            raise EvaluationError("没有已完成的金标题，请先填写标准答案并将ready改为true")
        return ready[:limit]
    if len(ready) != 30:
        raise EvaluationError(f"完整测评需要30题全部ready，当前完成{len(ready)}题；试跑可使用--limit")
    return ready


def retrieve_contexts(question: str, class_id: int, config: EvaluationConfig) -> list[dict[str, Any]]:
    if config.mode == "vector_small":
        return vector_search(question, class_id, top_k=config.top_k)
    if config.mode == "vector_parent":
        smalls = vector_search(question, class_id, top_k=config.top_k)
        return resolve_parent_chunks(smalls, class_id)
    recalled = hybrid_search(question, class_id)
    reranked = rerank_search(question, recalled["rrf"], top_k=config.top_k)
    return resolve_parent_chunks(reranked, class_id)


def answer_prompt(contexts: list[dict[str, Any]]) -> str:
    rules = (
        "你是高校团务知识库测评助手。只根据给出的资料回答确定性问题，不得虚构；"
        "资料不足时必须明确回答‘知识库依据不足’，不得猜测。回答使用简洁中文。"
    )
    if not contexts:
        return rules + "\n当前没有检索到资料。"
    blocks = [f"[资料{index}] {item.get('filename', '未知文件')} 第{item.get('page', 1)}页\n{item['content']}" for index, item in enumerate(contexts, 1)]
    return rules + "\n\n" + "\n\n".join(blocks)


class RagasScorer:
    """按需导入RAGAS，保证日常启动不依赖测评环境。"""

    def __init__(self) -> None:
        if not settings.deepseek_api_key or not settings.modelscope_api_token:
            raise EvaluationError("运行RAGAS需要DEEPSEEK_API_KEY和MODELSCOPE_API_TOKEN")
        try:
            from openai import AsyncOpenAI
            from ragas.embeddings.base import embedding_factory
            from ragas.llms import llm_factory
            from ragas.metrics.collections import AnswerRelevancy, ContextPrecisionWithReference, ContextRecall, Faithfulness
        except ImportError as exc:
            raise EvaluationError("尚未安装测评依赖，请执行 pip install -r requirements-eval.txt") from exc
        llm_client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        embedding_client = AsyncOpenAI(api_key=settings.modelscope_api_token, base_url=settings.modelscope_base_url)
        llm = llm_factory(settings.deepseek_model, client=llm_client)
        embeddings = embedding_factory("openai", model=settings.embedding_model, client=embedding_client)
        self.metrics = {
            "faithfulness": Faithfulness(llm=llm),
            "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
            "context_precision": ContextPrecisionWithReference(llm=llm),
            "context_recall": ContextRecall(llm=llm),
        }

    async def score(self, question: str, answer: str, contexts: list[str], reference: str) -> dict[str, float]:
        if not contexts:
            return {name: 0.0 for name in self.metrics}
        calls = {
            "faithfulness": self.metrics["faithfulness"].ascore(user_input=question, response=answer, retrieved_contexts=contexts),
            "answer_relevancy": self.metrics["answer_relevancy"].ascore(user_input=question, response=answer),
            "context_precision": self.metrics["context_precision"].ascore(user_input=question, reference=reference, retrieved_contexts=contexts),
            "context_recall": self.metrics["context_recall"].ascore(user_input=question, reference=reference, retrieved_contexts=contexts),
        }
        results = await asyncio.gather(*calls.values())
        return {name: round(float(result.value), 6) for name, result in zip(calls, results)}


async def evaluate(items: list[dict[str, Any]], class_id: int, scorer: Any, answer_client: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for number, item in enumerate(items, 1):
            print(f"[{config.name}] {number}/{len(items)} {item['id']}")
            retrieved = retrieve_contexts(item["question"], class_id, config)
            contexts = [context["content"] for context in retrieved]
            answer = await answer_client.complete([
                {"role": "system", "content": answer_prompt(retrieved)},
                {"role": "user", "content": item["question"]},
            ])
            scores = await scorer.score(item["question"], answer, contexts, item["reference_answer"])
            rows.append({
                "config": config.name, "config_label": config.label, "top_k": config.top_k,
                "question_id": item["id"], "category": item["category"], "question": item["question"],
                "reference_answer": item["reference_answer"], "answer": answer,
                "retrieved_contexts": contexts, **scores,
                "no_answer_ok": not (
                    item["category"] == "知识库无答案题"
                    and ("[资料" in answer or "知识库依据不足" not in answer)
                ),
            })
    return rows


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for config in CONFIGS:
        selected = [row for row in rows if row["config"] == config.name]
        if not selected:
            continue
        summary = {"config": config.name, "config_label": config.label, "count": len(selected)}
        for metric in THRESHOLDS:
            summary[metric] = round(mean(float(row[metric]) for row in selected), 6)
            summary[f"{metric}_passed"] = summary[metric] >= THRESHOLDS[metric]
        summary["no_answer_passed"] = all(row["no_answer_ok"] for row in selected)
        output.append(summary)
    return output


def conclusions(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {item["config"]: item for item in summaries}
    full = by_name.get("full_top3")
    baselines = [by_name.get("vector_small_top3"), by_name.get("vector_parent_top3")]
    full_beats_baselines = bool(full and all(
        baseline and all(full[metric] > baseline[metric] for metric in THRESHOLDS)
        for baseline in baselines
    ))
    top3 = by_name.get("full_top3"); top5 = by_name.get("full_top5")
    top_k_recommendation = 3
    if top3 and top5:
        top3_average = mean(top3[metric] for metric in THRESHOLDS)
        top5_average = mean(top5[metric] for metric in THRESHOLDS)
        top_k_recommendation = 5 if top5_average > top3_average else 3
    return {
        "full_top3_beats_both_baselines_on_all_metrics": full_beats_baselines,
        "recommended_top_k": top_k_recommendation,
        "thresholds_passed": bool(full and all(full[f"{metric}_passed"] for metric in THRESHOLDS)),
        "no_answer_passed": bool(full and full["no_answer_passed"]),
    }


def write_reports(rows: list[dict[str, Any]], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    summaries = summarize(rows)
    result_conclusions = conclusions(summaries)
    json_path = output_dir / f"ragas-{stamp}.json"
    csv_path = output_dir / f"ragas-{stamp}.csv"
    md_path = output_dir / f"ragas-{stamp}.md"
    json_path.write_text(json.dumps({"generated_at": stamp, "summary": summaries, "conclusions": result_conclusions, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    csv_fields = [key for key in rows[0] if key != "retrieved_contexts"] + ["retrieved_contexts"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=csv_fields); writer.writeheader()
        for row in rows:
            writer.writerow({**row, "retrieved_contexts": json.dumps(row["retrieved_contexts"], ensure_ascii=False)})
    lines = ["# RAGAS测评报告", "", f"生成时间：{stamp}", "", "| 方案 | 题数 | 忠实度 | 答案相关性 | 上下文精度 | 上下文召回率 | 无答案检查 |", "|---|---:|---:|---:|---:|---:|---|"]
    for item in summaries:
        lines.append(f"| {item['config_label']} | {item['count']} | {item['faithfulness']:.3f} | {item['answer_relevancy']:.3f} | {item['context_precision']:.3f} | {item['context_recall']:.3f} | {'通过' if item['no_answer_passed'] else '失败'} |")
    lines.extend([
        "", "## 自动结论", "",
        f"- 完整top-3在四项指标上均优于两个基线：{'是' if result_conclusions['full_top3_beats_both_baselines_on_all_metrics'] else '否'}",
        f"- 完整top-3达到全部目标阈值：{'是' if result_conclusions['thresholds_passed'] else '否'}",
        f"- 无答案题未伪造引用：{'是' if result_conclusions['no_answer_passed'] else '否'}",
        f"- 根据四项指标平均分建议top-k：{result_conclusions['recommended_top_k']}",
        "", "目标：Faithfulness≥0.85、Answer Relevance≥0.80、Context Precision≥0.75、Context Recall≥0.75。",
        "", "工具只生成测评结论，不会自动修改系统默认top-k。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, csv_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="团支书AI助手RAGAS离线测评")
    parser.add_argument("--class-id", type=int, default=1, help="要测评的班级ID")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=settings.data_dir / "evaluations")
    parser.add_argument("--limit", type=int, help="仅试跑前N道ready题；完整报告请勿使用")
    parser.add_argument("--validate-only", action="store_true", help="只检查30题结构，不调用API")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = load_dataset(args.dataset)
        if args.validate_only:
            print(f"金标集结构正确：30题，已完成{sum(bool(item['ready']) for item in items)}题")
            return 0
        selected = ready_dataset(items, args.limit)
        rows = asyncio.run(evaluate(selected, args.class_id, RagasScorer(), DeepSeekClient()))
        paths = write_reports(rows, args.output_dir)
        print("测评完成：" + "、".join(str(path) for path in paths))
        return 0
    except EvaluationError as exc:
        print(f"测评未运行：{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
