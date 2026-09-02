import asyncio
import json
from collections import Counter

import pytest

from evaluation.run_ragas import (
    CATEGORY_COUNTS,
    CONFIGS,
    EvaluationError,
    evaluate,
    load_dataset,
    ready_dataset,
    write_reports,
)


def test_gold_dataset_has_required_30_question_distribution() -> None:
    items = load_dataset()
    assert len(items) == 30
    assert Counter(item["category"] for item in items) == Counter(CATEGORY_COUNTS)
    assert len({item["id"] for item in items}) == 30


def test_full_evaluation_rejects_unfinished_gold_dataset() -> None:
    with pytest.raises(EvaluationError, match="30题全部ready"):
        ready_dataset(load_dataset())


class FakeAnswerClient:
    async def complete(self, messages):
        return "根据资料，测试答案。"


class FakeScorer:
    async def score(self, question, answer, contexts, reference):
        return {"faithfulness": 0.9, "answer_relevancy": 0.8, "context_precision": 0.75, "context_recall": 0.76}


def test_evaluation_compares_four_configs_and_writes_three_reports(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("evaluation.run_ragas.retrieve_contexts", lambda question, class_id, config: [{"content": f"{config.name}资料", "filename": "测试.pdf", "page": 1}])
    item = {"id": "F01", "category": "事实题", "question": "测试问题", "reference_answer": "标准答案", "reference_contexts": [], "ready": True}
    rows = asyncio.run(evaluate([item], 1, FakeScorer(), FakeAnswerClient()))
    assert len(rows) == len(CONFIGS)
    assert {row["config"] for row in rows} == {config.name for config in CONFIGS}
    paths = write_reports(rows, tmp_path)
    assert all(path.is_file() for path in paths)
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    assert len(payload["summary"]) == 4
    assert "RAGAS测评报告" in paths[2].read_text(encoding="utf-8")
