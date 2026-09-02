from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import require_secretary
from app.models import User
from app.retrieval import RetrievalError, retrieve_with_rerank


router = APIRouter(prefix="/api/rag", tags=["RAG"])


class SearchPayload(BaseModel):
    query: str = Field(min_length=2, max_length=1000)


@router.post("/search/debug")
def search_debug(payload: SearchPayload, user: User = Depends(require_secretary)) -> dict:
    try:
        return retrieve_with_rerank(payload.query.strip(), user.class_id)
    except RetrievalError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
