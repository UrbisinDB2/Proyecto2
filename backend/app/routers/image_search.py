from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.image.vector_engine import ImageSearchEngine

router = APIRouter()

# --- INSTANCIA GLOBAL ---
# Se carga UNA sola vez cuando inicias el servidor.
print("Cargando Motor Multimedia en memoria")
try:
    engine = ImageSearchEngine()
except Exception as e:
    print(f"Error cargando motor: {e}")
    engine = None

@router.post("/")
async def search_image(
    file: UploadFile = File(...), 
    k: int = 8
):
    """
    Busca imágenes similares.
    - file: Imagen a buscar (Body form-data)
    - k: Número de resultados (Query param, default 8)
    """
    if engine is None:
        raise HTTPException(status_code=500, detail="El motor no está activo. Revisa los logs del servidor.")

    try:
        # Leer imagen
        content = await file.read()
        
        # Buscar (Usando el método invertido)
        results = engine.search(content, k=k, method="inverted")
        
        return {"results": results}
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))