import csv
from app.services.text.spimi import spimi_invert
from app.services.text.merge_blocks import merge_blocks
from app.services.text.documents import build_documents_jsonl
import os
print(os.getcwd())


DATASET_PATH = "data/spotify_songs.csv"

def build_index():
    """
    Lee el dataset CSV y ejecuta SPIMI para construir los bloques iniciales.
    El CSV debe tener:
        id, texto
    """
    docs = []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Saltar cabecera

        for row in reader:
            trackID, lyrics = row[0], row[3]
            docs.append((str(trackID), lyrics))

    print("[INDEX] Iniciando SPIMI…")
    spimi_invert(docs)
    print("[INDEX] Bloques SPIMI generados.")

    print("[BUILD] Mergeando bloques…")
    merge_blocks(N=len(docs))

    print("[BUILD] Creando documents.jsonl…")
    build_documents_jsonl(DATASET_PATH)

    print("[BUILD] Índice textual construido correctamente.")
