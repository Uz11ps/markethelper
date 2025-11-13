import logging
import time
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import pdfplumber
from backend.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])
logger = logging.getLogger("ai_service")

@router.post("/texts")
async def add_text(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    if not text and not file:
        raise HTTPException(400, "Нужно передать либо text, либо PDF файл")

    if text:
        await ai_service.add_text(
            text,
            metadata={"source": "manual_input", "type": "text"}
        )
        return {"status": "ok", "mode": "text", "length": len(text)}

    if file:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(400, "Можно загружать только PDF файлы")

        try:
            total_chunks = 0
            with pdfplumber.open(file.file) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if not page_text:
                        continue

                    chunks = ai_service.chunk_text(page_text, chunk_size=1000, overlap=200)
                    logger.info(f"Страница {page_num}: {len(page_text)} символов → {len(chunks)} чанков")

                    for i, chunk in enumerate(chunks, start=1):
                        total_chunks += 1
                        await ai_service.add_text(
                            chunk,
                            metadata={
                                "source": file.filename,
                                "type": "pdf",
                                "page": page_num,
                                "chunk": i,
                            }
                        )

            if total_chunks == 0:
                raise HTTPException(400, "PDF пустой или не содержит текста")

            return {
                "status": "ok",
                "mode": "pdf",
                "filename": file.filename,
                "chunks": total_chunks,
            }

        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {str(e)}")
            raise HTTPException(500, f"Ошибка при обработке PDF: {str(e)}")

@router.get("/texts")
async def list_texts():
    """
    Получить список всех сохранённых текстов.
    """
    texts = await ai_service.list_texts()
    return texts


@router.delete("/texts/{text_id}")
async def delete_text(text_id: str):
    """
    Удалить текст по id.
    """
    ok = await ai_service.delete_text(text_id)
    if not ok:
        raise HTTPException(404, "text not found")
    return {"status": "deleted", "id": text_id}


@router.post("/query")
async def query_ai(data: dict):
    """
    Задать вопрос к базе знаний (через RAG).
    data = { "question": "вопрос пользователя" }
    """
    if "question" not in data:
        raise HTTPException(400, "question is required")

    start_time = time.time()
    logger.info(f"Запрос AI: {data['question']}")

    answer = await ai_service.query_ai(data["question"])

    elapsed = time.time() - start_time  # время обработки
    logger.info(f"Время обработки запроса: {elapsed:.3f} сек")

    return {
        "answer": answer,
        "time_seconds": elapsed  # можно возвращать пользователю
    }


@router.get("/health")
async def health_check():
    """
    Проверка, что сервис AI работает.
    """
    return {"status": "ok"}