from __future__ import annotations

import io
import re
import zipfile

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader

from ..config import settings
from ..models import Clause

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_upload(filename: str, content_type: str | None, data: bytes) -> str:
    safe_name = (filename or "document").strip()
    lower = safe_name.lower()
    extension = next((ext for ext in ALLOWED_EXTENSIONS if lower.endswith(ext)), "")
    if not extension:
        raise HTTPException(400, "Only PDF, DOCX, and TXT files are supported.")
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if (
        content_type
        and content_type not in ALLOWED_MIME_TYPES
        and content_type not in {"application/octet-stream", ""}
    ):
        raise HTTPException(400, "The uploaded file type is not supported.")
    if extension == ".pdf" and not data.startswith(b"%PDF"):
        raise HTTPException(400, "The uploaded PDF is invalid.")
    if extension == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if "[Content_Types].xml" not in archive.namelist():
                    raise HTTPException(400, "The uploaded DOCX file is invalid.")
        except zipfile.BadZipFile as exc:
            raise HTTPException(400, "The uploaded DOCX file is invalid.") from exc
    return extension


def extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > settings.max_pages:
            raise HTTPException(
                413,
                f"PDF has too many pages. Maximum is {settings.max_pages}.",
            )
        pages: list[str] = []
        for number, page in enumerate(reader.pages, 1):
            page_text = clean_text(page.extract_text() or "")
            if page_text:
                pages.append(f"[PAGE {number}]\n{page_text}")
        return "\n\n".join(pages)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, "The PDF could not be read.") from exc


def extract_docx(data: bytes) -> str:
    try:
        document = Document(io.BytesIO(data))
        paragraphs = [clean_text(p.text) for p in document.paragraphs]
        return "\n".join(p for p in paragraphs if p)
    except Exception as exc:
        raise HTTPException(400, "The DOCX file could not be read.") from exc


def extract_text(filename: str, data: bytes) -> str:
    extension = "." + filename.lower().rsplit(".", 1)[-1]
    if extension == ".pdf":
        return extract_pdf(data)
    if extension == ".docx":
        return extract_docx(data)
    if extension == ".txt":
        try:
            return clean_text(data.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise HTTPException(400, "The text file must be UTF-8 encoded.") from exc
    raise HTTPException(400, "Only PDF, DOCX, and TXT files are supported.")


def split_clauses(text: str) -> list[Clause]:
    page: int | None = None
    clauses: list[Clause] = []
    current: list[str] = []
    counter = 1

    def flush() -> None:
        nonlocal counter, current
        value = clean_text(" ".join(current))
        if value:
            clauses.append(Clause(id=f"C{counter}", text=value, page=page))
            counter += 1
        current = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        page_match = re.fullmatch(r"\[PAGE (\d+)\]", line, re.I)
        if page_match:
            flush()
            page = int(page_match.group(1))
            continue
        if re.match(
            r"^(?:\d+(?:\.\d+)*[.)]|clause\s+\d+|section\s+\d+|article\s+\d+)",
            line,
            re.I,
        ):
            flush()
        if line:
            current.append(line)
    flush()

    if not clauses and text.strip():
        clauses = [Clause(id="C1", text=clean_text(text), page=None)]
    return clauses
