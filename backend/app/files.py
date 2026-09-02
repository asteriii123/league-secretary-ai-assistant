from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.config import settings


MAX_NOTICE_FILE_SIZE = 20 * 1024 * 1024
NOTICE_SUFFIXES = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png"}
NOTICE_MIME_TYPES = {
    "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg", "image/png", "application/octet-stream",
}


def save_notice_attachment(upload: UploadFile) -> tuple[str, str]:
    original_name = Path(upload.filename or "附件").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in NOTICE_SUFFIXES or upload.content_type not in NOTICE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="附件仅支持PDF、Word、Excel和常见图片")
    target_dir = settings.uploads_dir / "notices"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{suffix}"
    size = 0
    with target.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_NOTICE_FILE_SIZE:
                output.close(); target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="附件不能超过20MB")
            output.write(chunk)
    return str(target), original_name


def delete_notice_attachment(path: str | None) -> None:
    if not path:
        return
    target = Path(path).resolve()
    allowed_dir = (settings.uploads_dir / "notices").resolve()
    if allowed_dir not in target.parents:
        return
    target.unlink(missing_ok=True)


def save_submission_attachment(upload: UploadFile) -> tuple[str, str]:
    original_name = Path(upload.filename or "材料").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in NOTICE_SUFFIXES or upload.content_type not in NOTICE_MIME_TYPES:
        raise HTTPException(status_code=400, detail="材料仅支持PDF、Word、Excel和常见图片")
    target_dir = settings.uploads_dir / "submissions"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{suffix}"
    size = 0
    with target.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_NOTICE_FILE_SIZE:
                output.close(); target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="材料不能超过20MB")
            output.write(chunk)
    return str(target), original_name


def delete_submission_attachment(path: str | None) -> None:
    if not path:
        return
    target = Path(path).resolve()
    allowed_dir = (settings.uploads_dir / "submissions").resolve()
    if allowed_dir in target.parents:
        target.unlink(missing_ok=True)
