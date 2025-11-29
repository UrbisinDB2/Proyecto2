import csv
from app.services.text.spimi import spimi_invert
from app.services.text.merge_blocks import merge_blocks

DATASET_PATH = "../../../data/spotify_songs.csv"

def build_index():
    """
    Lee el dataset CSV y ejecuta SPIMI para construir los bloques iniciales.
    El CSV debe tener:
        id, texto
    """
    docs = []

    with open(DATASET_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Saltar cabecera

        for row in reader:
            docID, text = row[0], row[3]
            docs.append((str(docID), text))

    print("[INDEX] Iniciando SPIMI…")
    spimi_invert(docs)
    print("[INDEX] Bloques SPIMI generados.")

    print("[BUILD] Mergeando bloques…")
    merge_blocks(N=len(docs))

    print("[BUILD] Índice textual construido correctamente.")

build_index()
