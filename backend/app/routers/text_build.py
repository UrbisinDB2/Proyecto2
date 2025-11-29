from fastapi import APIRouter
from app.services.text.build_index import build_index

router = APIRouter()

@router.post("/")
def build_text_index():
    build_index()
    return {"message": "Índice textual construido con éxito."}
