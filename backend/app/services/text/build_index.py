import csv
import nltk
from app.services.text.spimi import spimi_invert
from app.services.text.merge_blocks import merge_blocks
from app.services.text.documents import build_documents_jsonl
import os


def build_index(file: str, didx: int, tidx: int):
    """
    Lee el dataset CSV y ejecuta SPIMI para construir los bloques iniciales.
    El CSV debe tener:
        id, texto
    """
    docs = []

    csv_path = f"data/{file}.csv"

    nltk.download("stopwords")

    dname = ""
    tname = ""

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)

        header = next(reader)
        dname = header[didx]
        tname = header[tidx]

        for row in reader:
            docId, text = row[didx], row[tidx]
            docs.append((str(docId), text))

    print("[INDEX] Iniciando SPIMI…")
    spimi_invert(docs, file_name=file)
    print("[INDEX] Bloques SPIMI generados.")

    print("[BUILD] Mergeando bloques…")
    merge_blocks(N=len(docs), file_name=file)

    print("[BUILD] Creando documents.jsonl…")
    build_documents_jsonl(csv_path, dname, tname, file_name=file)

    print("[BUILD] Índice textual construido correctamente.")
