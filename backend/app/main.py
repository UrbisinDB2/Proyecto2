from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import text_build, text_search, image_search
#from app.routers import image_search

app = FastAPI(
    title="Mini Multimodal DB",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", name="root")
async def root():
    return JSONResponse(status_code=200, content="Hello from Mini Multimodal DB")

app.include_router(text_build.router, prefix="/index")
app.include_router(text_search.router, prefix="/search")
app.include_router(image_search.router, prefix="/image", tags=["Image Search"])
app.mount("/static", StaticFiles(directory="data/fashion/images"), name="static")