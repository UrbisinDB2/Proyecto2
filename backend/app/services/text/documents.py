import os
import json
import csv

DOCS_PATH = "index_text/"

def build_documents_jsonl(csv_path, dname: str, tname: str, file_name: str):
    """
    Convierte tu CSV original en un JSONL:
    {"docID":..., "text":..., "title":..., "artist":...}
    """

    out = open(DOCS_PATH + file_name + "/documents.jsonl", "w", encoding="utf-8")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Adaptar a tu CSV real
            doc = {
                "docId": row[dname],
                "text": row[tname],
                "name": row.get("track_name", None)
            }
            json.dump(doc, out, ensure_ascii=False)
            out.write("\n")

    out.close()
    print("[DOCS] Archivo documents.jsonl generado.")
