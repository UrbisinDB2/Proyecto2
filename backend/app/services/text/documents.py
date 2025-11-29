import os
import json
import csv

DOCS_PATH = "../../../index_text/documents.jsonl"

def build_documents_jsonl(csv_path="../../../data/spotify_songs.csv"):
    """
    Convierte tu CSV original en un JSONL:
    {"docID":..., "text":..., "title":..., "artist":...}
    """

    out = open(DOCS_PATH, "w", encoding="utf-8")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Adaptar a tu CSV real
            doc = {
                "id": row["track_id"],
                "lyrics": row["lyrics"],
                "name": row.get("track_name", None),
                "artist": row.get("track_artist", None)
            }
            json.dump(doc, out, ensure_ascii=False)
            out.write("\n")

    out.close()
    print("[DOCS] Archivo documents.jsonl generado.")
