import json

DOCS_PATH = "../../../index_text/documents.jsonl"

def load_doc(trackId):
    """
    Lee documents.jsonl secuencialmente y encuentra el docID.
    Si quieres optimizar, luego puedes usar un índice auxiliar.
    """
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if doc["id"] == trackId:
                return doc
    return None

def get_snippet(text, query_terms, window=40):
    """
    Toma el texto completo de la canción y devuelve un snippet
    que contenga la primera aparición de un término de la query.
    """
    words = text.split()

    # buscar primer match
    for i, w in enumerate(words):
        if any(term in w.lower() for term in query_terms):
            start = max(0, i - window)
            end = min(len(words), i + window)
            return " ".join(words[start:end])

    # fallback
    return " ".join(words[:window])
