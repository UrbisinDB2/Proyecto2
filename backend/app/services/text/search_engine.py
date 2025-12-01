import os
import json
import math
from collections import defaultdict
from app.services.text.preprocess import preprocess

INDEX_DIR = "index_text/"

# Variables globales para cachear el índice
_dictionary = None
_norms = None
_doc_index = None
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


def load_doc_index(file_name: str):
    """
    Carga un índice de offset para acceso directo a documentos.
    Esto permite acceder a cualquier documento en O(1) en lugar de O(n).
    """
    global _doc_index

    # Verificar si el caché es válido para este archivo
    if _doc_index is not None:
        # El caché de doc_index debe verificarse contra _file_name global
        global _file_name
        if _file_name == file_name:
            return _doc_index

    docs_path = os.path.join(INDEX_DIR, file_name, "documents.jsonl")

    if not os.path.exists(docs_path):
        print(f"[ERROR] No existe el archivo de documentos: {docs_path}")
        return {}

    index = {}

    with open(docs_path, "r", encoding="utf-8") as f:
        while True:
            offset = f.tell()  # Guardar posición ANTES de leer
            line = f.readline()

            if not line:  # EOF
                break

            try:
                doc = json.loads(line)
                index[doc["docId"]] = offset
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[WARNING] Error parseando documento en offset {offset}: {e}")

    _doc_index = index
    return index


# ============================================================
# LECTURA DE POSTINGS (OPTIMIZADA)
# ============================================================

def load_postings_batch(terms, dictionary, file_name: str):
    """
    Carga postings de múltiples términos en una sola pasada.
    Esto reduce drásticamente las operaciones de I/O.

    Retorna: dict { term -> [[docID, weight], ...] }
    """
    if not terms:
        return {}

    # Filtrar términos que existen en el diccionario y ordenar por offset
    valid_terms = [(term, dictionary[term]) for term in terms if term in dictionary]

    if not valid_terms:
        return {}

    # Ordenar por offset para lectura secuencial eficiente
    valid_terms.sort(key=lambda x: x[1][0])

    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")
    results = {}

    with open(postings_path, "r", encoding="utf-8") as pf:
        for term, (offset, _) in valid_terms:
            pf.seek(offset)
            line = pf.readline()
            data = json.loads(line)
            results[term] = data["postings"]

    return results


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
# FUNCIÓN AUXILIAR PARA CARGAR DOCUMENTO (OPTIMIZADA)
# ============================================================

def load_doc(docId, file_name: str):
    """
    Lee documento usando índice de offsets para acceso directo.
    Complejidad: O(1) en lugar de O(n).
    """
    doc_index = load_doc_index(file_name)

    if not doc_index or docId not in doc_index:
        return None

    docs_path = os.path.join(INDEX_DIR, file_name, "documents.jsonl")

    try:
        with open(docs_path, "r", encoding="utf-8") as f:
            f.seek(doc_index[docId])
            line = f.readline()
            return json.loads(line)
    except (IOError, json.JSONDecodeError) as e:
        print(f"[ERROR] No se pudo cargar documento {docId}: {e}")
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
# SIMILITUD DE COSENO (OPTIMIZADA)
# ============================================================

def search_query(q, k=10, file_name="spotify_songs"):
    """
    Motor principal de búsqueda OPTIMIZADO.

    Entrada:
        q: string con la consulta
        k: top K resultados
        file_name: nombre del dataset indexado
    Salida:
        lista de documentos ordenados por score

    Optimizaciones implementadas:
    1. Carga batch de postings (reduce I/O)
    2. Índice de documentos para acceso O(1)
    3. Caché global de estructuras
    """

    # 1. Preprocesar query
    terms = preprocess(q)

    if not terms:
        return []

    # 2. Cargar diccionario y normas (con caché)
    dictionary = load_dictionary(file_name)
    norms = load_norms(file_name)

    if not dictionary or not norms:
        return []

    N = len(norms)  # cantidad de documentos en el índice

    # 3. TF-IDF de la query
    wq = compute_query_weights(terms, dictionary, N)

    if not wq:
        return []

    # 4. OPTIMIZACIÓN: Cargar todos los postings en batch
    try:
        postings_batch = load_postings_batch(wq.keys(), dictionary, file_name)
    except Exception as e:
        print(f"[ERROR] Error cargando postings: {e}")
        return []

    # 5. Acumular similitud parcial (producto punto)
    scores = defaultdict(float)

    for term, wq_t in wq.items():
        if term not in postings_batch:
            continue

        postings = postings_batch[term]

        for docID, w_t_d in postings:
            scores[docID] += wq_t * w_t_d  # producto punto

    # 6. Normalizar por norma del documento (similitud de coseno)
    for docID in scores:
        if docID in norms and norms[docID] != 0:
            scores[docID] /= norms[docID]

    # 7. Ordenar top-K
    results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = results[:k]

    # 8. OPTIMIZACIÓN: Cargar índice de documentos una sola vez
    load_doc_index(file_name)

    # 9. Formato de salida con detalles del documento
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


# ============================================================
# FUNCIÓN AUXILIAR PARA LIMPIAR CACHÉ (OPCIONAL)
# ============================================================

def clear_cache():
    """
    Limpia el caché global. Útil si cambias de dataset.
    """
    global _dictionary, _norms, _doc_index, _file_name
    _dictionary = None
    _norms = None
    _doc_index = None
    _file_name = None