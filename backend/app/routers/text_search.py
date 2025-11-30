from fastapi import APIRouter
from app.services.text.search_engine import search_query

router = APIRouter()


@router.get("/")
def text_search(q: str, k: int = 10, file_name: str = "spotify_songs"):
    """
    Busca en el índice textual.

    Args:
        q: query de búsqueda
        k: número de resultados a retornar
        file_name: nombre del dataset indexado
    """
    return search_query(q, k, file_name)