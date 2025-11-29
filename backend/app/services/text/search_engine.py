import os
import json
import math
from collections import defaultdict
from app.services.text.preprocess import preprocess
from app.services.text.index_utils import load_doc, get_snippet

INDEX_DIR = "../../../index_text/"
DICT_PATH = os.path.join(INDEX_DIR, "dictionary.txt")
POSTINGS_PATH = os.path.join(INDEX_DIR, "postings.jsonl")
NORMS_PATH = os.path.join(INDEX_DIR, "norms.json")


# ============================================================
# CARGA DE DICCIONARIO Y NORMAS
# ============================================================

def load_dictionary():
    """
    Carga el diccionario en memoria:
    term -> (offset, num_postings)
    """
    dic = {}
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            term, offset, length = line.strip().split("|")
            dic[term] = (int(offset), int(length))
    return dic


def load_norms():
    """
    Carga normas del archivo norms.json
    docID -> norma
    """
    with open(NORMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# LECTURA DE POSTINGS
# ============================================================

def load_postings(term, dictionary):
    """
    Recupera postings desde postings.jsonl usando offset.
    Retorna lista de [docID, weight].
    """
    if term not in dictionary:
        return []

    offset, _ = dictionary[term]

    with open(POSTINGS_PATH, "r", encoding="utf-8") as pf:
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
        idf = math.log(N / df)
        tf_weight = 1 + math.log(freq)
        wq[term] = tf_weight * idf

    return wq


# ============================================================
# SIMILITUD DE COSENO
# ============================================================

def search_query(q, k=10):
    """
    Motor principal de búsqueda.
    Entrada:
        q: string con la consulta
        k: top K resultados
    Salida:
        lista de documentos ordenados por score
    """

    # 1. Preprocesar query
    terms = preprocess(q)

    # 2. Cargar diccionario y normas
    dictionary = load_dictionary()
    norms = load_norms()
    N = len(norms)  # cantidad de documentos en el índice

    # 3. TF-IDF de la query
    wq = compute_query_weights(terms, dictionary, N)

    # 4. Acumular similitud parcial
    scores = defaultdict(float)

    for term, wq_t in wq.items():
        postings = load_postings(term, dictionary)

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
    for trackId, score in results:

        doc = load_doc(trackId)
        if doc is None:
            continue

        snippet = get_snippet(doc["lyrics"], terms)

        final_results.append({
            "trackId": trackId,
            "score": float(score),
            "name": doc.get("name"),
            "artist": doc.get("artist"),
            "snippet": snippet
        })

    return final_results