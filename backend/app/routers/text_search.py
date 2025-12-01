from fastapi import APIRouter
from app.services.text.search_engine import search_query
import time

router = APIRouter()

@router.get("/")
def text_search(q: str, k: int = 10, file_name: str = "spotify_songs"):
    start = time.time()  # inicio

    # Llamas a tu función de búsqueda
    results = search_query(q, k, file_name)

    end = time.time()  # fin
    execution_time = round((end - start) * 1000, 3)  # ms con 3 decimales

    return {
        "results": results,
        "execution_time": execution_time
    }
