import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("DATA_DIR", BACKEND_DIR / "data"))
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}")
    jwt_secret: str = os.getenv("JWT_SECRET", "local-development-change-me")
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "12"))
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    modelscope_api_token: str = os.getenv("MODELSCOPE_API_TOKEN", "").strip()
    modelscope_base_url: str = os.getenv("MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn/v1").rstrip("/")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower()
    embedding_model: str = os.getenv("EMBEDDING_MODEL", os.getenv("MODELSCOPE_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"))
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", os.getenv("MODELSCOPE_EMBEDDING_BATCH_SIZE", "16")))
    embedding_retries: int = int(os.getenv("EMBEDDING_RETRIES", os.getenv("MODELSCOPE_EMBEDDING_RETRIES", "3")))
    rerank_model: str = os.getenv("MODELSCOPE_RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
    rag_enabled: bool = os.getenv("RAG_ENABLED", "true").lower() == "true"
    whisper_enabled: bool = os.getenv("WHISPER_ENABLED", "true").lower() == "true"
    whisper_model: str = os.getenv("WHISPER_MODEL", "small")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    rag_final_top_k: int = int(os.getenv("RAG_FINAL_TOP_K", "3"))
    rag_recall_top_k: int = int(os.getenv("RAG_RECALL_TOP_K", "50"))
    rag_rrf_k: int = int(os.getenv("RAG_RRF_K", "60"))
    rag_fusion_top_k: int = int(os.getenv("RAG_FUSION_TOP_K", "20"))

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def converted_dir(self) -> Path:
        return self.data_dir / "converted"

    @property
    def chroma_dir(self) -> Path:
        return Path(os.getenv("CHROMA_PERSIST_DIR", self.data_dir / "chroma"))

    @property
    def indexes_dir(self) -> Path:
        return self.data_dir / "indexes"

    @property
    def models_dir(self) -> Path:
        return Path(os.getenv("LOCAL_MODEL_CACHE_DIR", self.data_dir / "models"))

    @property
    def tessdata_dir(self) -> Path:
        return Path(os.getenv("TESSDATA_DIR", self.data_dir / "tessdata"))


settings = Settings()


def ensure_data_directories() -> None:
    for path in (
        settings.data_dir,
        settings.converted_dir,
        settings.chroma_dir,
        settings.indexes_dir,
        settings.models_dir,
        settings.uploads_dir / "notices",
        settings.uploads_dir / "submissions",
        settings.uploads_dir / "meetings",
        settings.uploads_dir / "knowledge",
        settings.tessdata_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def secure_filename_suffix() -> str:
    return secrets.token_hex(8)
