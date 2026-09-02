from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models import ClassRoom, KnowledgeChunk, KnowledgeDocument, User
from app.retrieval import (
    bm25_search,
    index_document,
    rerank_search,
    resolve_parent_chunks,
    rrf_fuse,
    set_document_enabled,
    vector_search,
)


class FakeEmbedder:
    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.batch_sizes.append(len(texts))
        return [[float(len(text)), 1.0, 0.5] for text in texts]


class FakeCollection:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def delete(self, where: dict) -> None:
        self.items = {key: value for key, value in self.items.items() if value["metadata"].get("document_id") != where.get("document_id")}

    def upsert(self, ids, embeddings, documents, metadatas) -> None:
        for item_id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas):
            self.items[item_id] = {"embedding": embedding, "document": document, "metadata": metadata}

    def get(self, where: dict, include: list[str]) -> dict:
        matches = [(key, value) for key, value in self.items.items() if value["metadata"].get("document_id") == where.get("document_id")]
        return {"ids": [key for key, _ in matches], "metadatas": [value["metadata"] for _, value in matches]}

    def update(self, ids, metadatas) -> None:
        for item_id, metadata in zip(ids, metadatas):
            self.items[item_id]["metadata"] = metadata

    def query(self, query_embeddings, n_results, where, include) -> dict:
        class_id = where["$and"][0]["class_id"]["$eq"]
        enabled = where["$and"][1]["enabled"]["$eq"]
        matches = [value for value in self.items.values() if value["metadata"]["class_id"] == class_id and value["metadata"]["enabled"] == enabled][:n_results]
        return {"documents": [[item["document"] for item in matches]], "metadatas": [[item["metadata"] for item in matches]], "distances": [[0.1 + index * 0.01 for index, _ in enumerate(matches)]]}


class FakeReranker:
    def rerank(self, query: str, documents: list[str]) -> list[dict]:
        assert query == "团费怎么缴纳"
        return [{"index": 1, "score": 0.92}, {"index": 0, "score": 0.71}]


def create_index_fixture() -> tuple[int, int]:
    with SessionLocal() as db:
        classroom = db.scalar(select(ClassRoom).where(ClassRoom.name == "23级计算机科学与技术1班"))
        secretary = db.scalar(select(User).where(User.username == "secretary1"))
        document = KnowledgeDocument(
            class_id=classroom.id, author_id=secretary.id, filename="混合检索测试.txt", file_type="txt",
            file_hash=uuid4().hex + uuid4().hex, stored_path="test", status="done", enabled=True,
            parent_count=1, small_count=4, index_status="pending",
        )
        db.add(document); db.flush()
        parent = KnowledgeChunk(document_id=document.id, chunk_type="parent", content="团务测试父块", heading="测试", section_path="测试", page=1, char_count=6, order_index=1)
        db.add(parent); db.flush()
        texts = ["团费缴纳流程和截止要求", "主题团日活动策划", "入党申请书格式说明", "团员信息统计工作"]
        for index, text in enumerate(texts, start=2):
            db.add(KnowledgeChunk(document_id=document.id, parent_id=parent.id, chunk_type="small", content=text, heading="测试", section_path="测试", page=1, char_count=len(text), order_index=index))
        db.commit()
        return document.id, classroom.id


def cleanup(document_id: int) -> None:
    with SessionLocal() as db:
        chunks = db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id)).all()
        for chunk in chunks:
            db.delete(chunk)
        document = db.get(KnowledgeDocument, document_id)
        if document:
            db.delete(document)
        db.commit()


def test_embedding_index_bm25_and_rrf() -> None:
    document_id, class_id = create_index_fixture(); embedder = FakeEmbedder(); collection = FakeCollection()
    try:
        index_document(document_id, embedder=embedder, collection=collection)
        assert len(collection.items) == 4
        assert max(embedder.batch_sizes) <= 16
        with SessionLocal() as db:
            document = db.get(KnowledgeDocument, document_id)
            assert document.index_status == "indexed"
        keyword = bm25_search("团费缴纳", class_id)
        assert keyword and "团费缴纳" in keyword[0]["content"]
        vector = vector_search("团费缴纳", class_id, embedder=embedder, collection=collection)
        assert len(vector) == 4 and vector[0]["rank"] == 1
        fused = rrf_fuse(vector, keyword, k=60, top_k=3)
        assert fused[0]["vector_rank"] == 1
        assert fused[0]["bm25_rank"] == 1
        assert fused[0]["rrf_score"] > 0
        with SessionLocal() as db:
            document = db.get(KnowledgeDocument, document_id); document.enabled = False; db.commit()
        set_document_enabled(document_id, class_id, False, collection=collection)
        assert all(not value["metadata"]["enabled"] for value in collection.items.values())
        assert bm25_search("团费缴纳", class_id) == []
    finally:
        cleanup(document_id)


def test_rerank_selects_small_chunks_then_deduplicates_parents() -> None:
    document_id, class_id = create_index_fixture(); embedder = FakeEmbedder(); collection = FakeCollection()
    try:
        index_document(document_id, embedder=embedder, collection=collection)
        candidates = vector_search("团费怎么缴纳", class_id, embedder=embedder, collection=collection)[:2]
        reranked = rerank_search("团费怎么缴纳", candidates, reranker=FakeReranker(), top_k=2)
        assert reranked[0]["chunk_id"] == candidates[1]["chunk_id"]
        assert reranked[0]["rerank_score"] == 0.92
        parents = resolve_parent_chunks(reranked, class_id)
        assert len(parents) == 1
        assert parents[0]["source_label"] == "资料1"
        assert parents[0]["content"] == "团务测试父块"
    finally:
        cleanup(document_id)
