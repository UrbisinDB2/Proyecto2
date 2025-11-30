import os
import json
import math
from collections import defaultdict
from app.services.text.preprocess import preprocess

INDEX_DIR = "index_text/"

# Variables globales para cachear el índice
_dictionary = None
_norms = None
_file_name = None


# ============================================================
# CARGA DE DICCIONARIO Y NORMAS
# ============================================================

def load_dictionary(file_name: str):
    """
    Carga el diccionario en memoria:
    term -> (offset, num_postings)
    """
    global _dictionary, _file_name

    # Si ya está cargado para este archivo, retornar caché
    if _dictionary is not None and _file_name == file_name:
        return _dictionary

    dict_path = os.path.join(INDEX_DIR, file_name, "dictionary.txt")

    if not os.path.exists(dict_path):
        print(f"[ERROR] No existe el diccionario: {dict_path}")
        return {}

    dic = {}
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 3:
                term, offset, length = parts
                dic[term] = (int(offset), int(length))

    _dictionary = dic
    _file_name = file_name
    return dic


def load_norms(file_name: str):
    """
    Carga normas del archivo norms.json
    docID -> norma
    """
    global _norms, _file_name

    # Si ya está cargado para este archivo, retornar caché
    if _norms is not None and _file_name == file_name:
        return _norms

    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")

    if not os.path.exists(norms_path):
        print(f"[ERROR] No existe el archivo de normas: {norms_path}")
        return {}

    with open(norms_path, "r", encoding="utf-8") as f:
        norms = json.load(f)

    _norms = norms
    return norms


# ============================================================
# LECTURA DE POSTINGS
# ============================================================

def load_postings(term, dictionary, file_name: str):
    """
    Recupera postings desde postings.jsonl usando offset.
    Retorna lista de [docID, weight].
    """
    if term not in dictionary:
        return []

    offset, _ = dictionary[term]

    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")

    with open(postings_path, "r", encoding="utf-8") as pf:
        pf.seek(offset)
        line = pf.readline()
        data = json.loads(line)

    return data["postings"]  # [["docID", weight], ...]


# ============================================================
# TF-IDF para la Query
# ============================================================

def compute_query_weights(query_terms, dictionary, N):
    """
    Calcula TF-IDF del vector de la query.
    return: dict( term -> weight )
    """

    # TF de la query
    tf = defaultdict(int)
    for t in query_terms:
        tf[t] += 1

    # TF-IDF de la query
    wq = {}

    for term, freq in tf.items():
        if term not in dictionary:
            continue

        _, df = dictionary[term]
        idf = math.log(N / df) if df > 0 else 0
        tf_weight = 1 + math.log(freq)
        wq[term] = tf_weight * idf

    return wq


# ============================================================
# FUNCIÓN AUXILIAR PARA CARGAR DOCUMENTO
# ============================================================

def load_doc(docId, file_name: str):
    """
    Lee documents.jsonl secuencialmente y encuentra el docID.
    """
    docs_path = os.path.join(INDEX_DIR, file_name, "documents.jsonl")

    if not os.path.exists(docs_path):
        return None

    with open(docs_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if doc["docId"] == docId:
                return doc
    return None


def get_snippet(text, query_terms, window=40):
    """
    Toma el texto completo y devuelve un snippet
    que contenga la primera aparición de un término de la query.
    """
    if not text:
        return ""

    words = text.split()

    # buscar primer match
    for i, w in enumerate(words):
        if any(term in w.lower() for term in query_terms):
            start = max(0, i - window)
            end = min(len(words), i + window)
            snippet = " ".join(words[start:end])
            return snippet if len(snippet) > 0 else " ".join(words[:window])

    # fallback
    return " ".join(words[:window])


# ============================================================
# SIMILITUD DE COSENO
# ============================================================

def search_query(q, k=10, file_name="spotify_songs"):
    """
    Motor principal de búsqueda.
    Entrada:
        q: string con la consulta
        k: top K resultados
        file_name: nombre del dataset indexado
    Salida:
        lista de documentos ordenados por score
    """

    # 1. Preprocesar query
    terms = preprocess(q)

    if not terms:
        return []

    # 2. Cargar diccionario y normas
    dictionary = load_dictionary(file_name)
    norms = load_norms(file_name)

    if not dictionary or not norms:
        return []

    N = len(norms)  # cantidad de documentos en el índice

    # 3. TF-IDF de la query
    wq = compute_query_weights(terms, dictionary, N)

    # 4. Acumular similitud parcial
    scores = defaultdict(float)

    for term, wq_t in wq.items():
        postings = load_postings(term, dictionary, file_name)

        for docID, w_t_d in postings:
            scores[docID] += wq_t * w_t_d  # producto punto

    # 5. Normalizar por norma del documento
    for docID in scores:
        if docID in norms and norms[docID] != 0:
            scores[docID] /= norms[docID]

    # 6. Ordenar top-K
    results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = results[:k]

    # 7. Formato de salida
    final_results = []
    for docId, score in results:

        doc = load_doc(docId, file_name)
        if doc is None:
            continue

        snippet = get_snippet(doc.get("text", ""), terms)

        final_results.append({
            "docId": docId,
            "score": float(score),
            "name": doc.get("name"),
            "snippet": snippet
        })

    return final_results