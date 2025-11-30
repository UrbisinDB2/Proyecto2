from pydantic import BaseModel
from fastapi import APIRouter
from app.services.text.build_index import build_index

router = APIRouter()

class BuildRequest(BaseModel):
    file: str
    docIdIdx: int
    textColumnIdx: int

@router.post("/")
def build_text_index(req: BuildRequest):
    build_index(req.file, req.docIdIdx, req.textColumnIdx)

    return {"message": "Índice textual construido con éxito."}
