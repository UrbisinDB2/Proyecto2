from fastapi import APIRouter
from app.services.text.search_engine import search_query

router = APIRouter()

@router.get("/")
def text_search(q: str, k: int = 10):
    return search_query(q, k)
