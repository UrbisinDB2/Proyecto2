import os
import json
import math
from collections import defaultdict
from app.services.text.preprocess import preprocess

INDEX_DIR = "index_text/"


# ============================================================
# ACCESO DIRECTO AL DICCIONARIO (SIN CACHÉ COMPLETO)
# ============================================================

def get_term_info(term, file_name: str):
    """
    Busca un término específico en el diccionario SIN cargar todo en RAM.
    Retorna: (offset, df) o None si no existe.

    OPTIMIZACIÓN: El diccionario está ordenado alfabéticamente,
    pero esta versión hace búsqueda lineal (simple y confiable).
    Para datasets muy grandes, considerar búsqueda binaria.
    """
    dict_path = os.path.join(INDEX_DIR, file_name, "dictionary.txt")

    if not os.path.exists(dict_path):
        print(f"[ERROR] No existe el diccionario: {dict_path}")
        return None

    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 3:
                t, offset, df = parts
                if t == term:
                    return (int(offset), int(df))

    return None


def get_total_docs(file_name: str):
    """
    Obtiene el número total de documentos desde norms.json
    SIN cargar todas las normas en memoria.
    """
    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")

    if not os.path.exists(norms_path):
        print(f"[ERROR] No existe el archivo de normas: {norms_path}")
        return 0

    # Solo contar líneas sin parsear el JSON completo
    with open(norms_path, "r", encoding="utf-8") as f:
        content = f.read()
        norms = json.loads(content)
        return len(norms)


def get_doc_norm(docId, file_name: str):
    """
    Obtiene la norma de un documento específico.

    NOTA: Para evitar leer todo norms.json repetidamente,
    lo cargamos una sola vez al calcular scores.
    """
    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")

    with open(norms_path, "r", encoding="utf-8") as f:
        norms = json.load(f)
        return norms.get(docId, 0.0)


# ============================================================
# LECTURA SELECTIVA DE POSTINGS
# ============================================================

def load_postings_for_term(term, term_info, file_name: str):
    """
    Carga los postings de UN SOLO término.
    Retorna: [[docID, weight], ...]
    """
    if term_info is None:
        return []

    offset, _ = term_info
    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")

    try:
        with open(postings_path, "r", encoding="utf-8") as pf:
            pf.seek(offset)
            line = pf.readline()
            data = json.loads(line)
            return data["postings"]
    except Exception as e:
        print(f"[ERROR] Error cargando postings para '{term}': {e}")
        return []


def load_postings_batch_optimized(query_terms, file_name: str):
    """
    Carga postings SOLO de los términos de la query.

    OPTIMIZACIÓN:
    1. Obtiene info de términos uno por uno (sin caché del diccionario)
    2. Ordena por offset para lectura secuencial
    3. Lee postings en batch

    Retorna: dict { term -> [[docID, weight], ...] }
    """
    # 1. Obtener info de términos (sin cargar diccionario completo)
    term_infos = []
    for term in query_terms:
        info = get_term_info(term, file_name)
        if info:
            term_infos.append((term, info))

    if not term_infos:
        return {}

    # 2. Ordenar por offset para lectura secuencial
    term_infos.sort(key=lambda x: x[1][0])  # Ordenar por offset

    # 3. Leer postings
    results = {}
    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")

    with open(postings_path, "r", encoding="utf-8") as pf:
        for term, (offset, _) in term_infos:
            pf.seek(offset)
            line = pf.readline()
            data = json.loads(line)
            results[term] = data["postings"]

    return results


# ============================================================
# TF-IDF PARA LA QUERY (SIN CARGAR DICCIONARIO COMPLETO)
# ============================================================

def compute_query_weights_optimized(query_terms, N, file_name: str):
    """
    Calcula TF-IDF del vector de la query Y LO NORMALIZA.

    IMPORTANTE: La query también debe normalizarse para que
    la similitud de coseno esté en el rango [0, 1].

    return: dict( term -> weight_normalizado )
    """
    # TF de la query
    tf = defaultdict(int)
    for t in query_terms:
        tf[t] += 1

    # TF-IDF de la query (sin normalizar)
    wq = {}

    for term, freq in tf.items():
        # Buscar término en diccionario (sin cargar todo)
        term_info = get_term_info(term, file_name)

        if term_info is None:
            continue

        _, df = term_info
        idf = math.log(N / df) if df > 0 else 0
        tf_weight = 1 + math.log(freq)
        wq[term] = tf_weight * idf

    # ============================================================
    # NORMALIZAR EL VECTOR DE LA QUERY
    # ============================================================
    # Calcular norma: sqrt(sum(w_i^2))
    norm_q = math.sqrt(sum(w * w for w in wq.values()))

    # Normalizar cada peso
    if norm_q > 0:
        wq = {term: weight / norm_q for term, weight in wq.items()}

    return wq


# ============================================================
# ACCESO A DOCUMENTOS (OPTIMIZADO)
# ============================================================

def build_doc_index_optimized(file_name: str):
    """
    Construye índice de offsets para documentos.

    NOTA: Este índice es pequeño (solo offsets),
    no carga el contenido de los documentos.
    """
    docs_path = os.path.join(INDEX_DIR, file_name, "documents.jsonl")

    if not os.path.exists(docs_path):
        return {}

    index = {}

    with open(docs_path, "r", encoding="utf-8") as f:
        while True:
            offset = f.tell()
            line = f.readline()

            if not line:
                break

            try:
                doc = json.loads(line)
                index[doc["docId"]] = offset
            except (json.JSONDecodeError, KeyError):
                continue

    return index


def load_doc_optimized(docId, doc_index, file_name: str):
    """
    Carga UN documento específico usando el índice de offsets.
    """
    if not doc_index or docId not in doc_index:
        return None

    docs_path = os.path.join(INDEX_DIR, file_name, "documents.jsonl")

    try:
        with open(docs_path, "r", encoding="utf-8") as f:
            f.seek(doc_index[docId])
            line = f.readline()
            return json.loads(line)
    except Exception as e:
        print(f"[ERROR] Error cargando documento {docId}: {e}")
        return None


def get_snippet(text, query_terms, window=40):
    """
    Genera snippet del texto con contexto de los términos de búsqueda.
    """
    if not text:
        return ""

    words = text.split()

    for i, w in enumerate(words):
        if any(term in w.lower() for term in query_terms):
            start = max(0, i - window)
            end = min(len(words), i + window)
            snippet = " ".join(words[start:end])
            return snippet if len(snippet) > 0 else " ".join(words[:window])

    return " ".join(words[:window])


# ============================================================
# MOTOR DE BÚSQUEDA OPTIMIZADO (SIN CACHÉ EN RAM)
# ============================================================

def search_query(q, k=10, file_name="spotify_songs"):
    """
    Motor principal de búsqueda COMPLETAMENTE OPTIMIZADO.

    CAMBIOS CLAVE:
    1. ❌ NO carga diccionario completo
    2. ❌ NO carga todas las normas
    3. ✅ Solo accede a datos necesarios para la query
    4. ✅ Usa índice de documentos (pequeño, solo offsets)

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

    # 2. Obtener número total de documentos (lectura mínima)
    N = get_total_docs(file_name)

    if N == 0:
        print("[ERROR] No se pudo determinar el tamaño del corpus")
        return []

    # 3. Calcular TF-IDF de la query (sin cargar diccionario completo)
    wq = compute_query_weights_optimized(terms, N, file_name)

    if not wq:
        return []

    # 4. Cargar postings SOLO de términos de la query
    try:
        postings_batch = load_postings_batch_optimized(wq.keys(), file_name)
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
            scores[docID] += wq_t * w_t_d

    # 6. Cargar normas SOLO UNA VEZ (necesario para normalización)
    # NOTA: Las normas son pequeñas comparadas con postings,
    # pero si el dataset es MUY grande, podrías optimizar esto también
    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")
    with open(norms_path, "r", encoding="utf-8") as f:
        norms = json.load(f)

    # 7. Normalizar por norma del documento (similitud de coseno)
    for docID in scores:
        if docID in norms and norms[docID] != 0:
            scores[docID] /= norms[docID]
        else:
            # Si un documento no tiene norma, su score es 0
            scores[docID] = 0.0

    # 8. Asegurar que los scores estén en [0, 1]
    # (Esto es redundante si la normalización es correcta, pero es una verificación)
    for docID in scores:
        scores[docID] = max(0.0, min(1.0, scores[docID]))

    # 8. Ordenar top-K
    results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = results[:k]

    # 9. Construir índice de documentos (pequeño, solo offsets)
    doc_index = build_doc_index_optimized(file_name)

    # 10. Cargar detalles SOLO de los top-K documentos
    final_results = []
    for docId, score in results:
        doc = load_doc_optimized(docId, doc_index, file_name)

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
# FUNCIÓN PARA ESTADÍSTICAS (OPCIONAL)
# ============================================================

def print_memory_usage(file_name: str):
    """
    Muestra estadísticas del índice sin cargar todo en memoria.
    """
    dict_path = os.path.join(INDEX_DIR, file_name, "dictionary.txt")
    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")
    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")

    if os.path.exists(dict_path):
        dict_size = os.path.getsize(dict_path) / (1024 * 1024)
        print(f"  Dictionary: {dict_size:.2f} MB")

    if os.path.exists(postings_path):
        postings_size = os.path.getsize(postings_path) / (1024 * 1024)
        print(f"  Postings: {postings_size:.2f} MB")

    if os.path.exists(norms_path):
        norms_size = os.path.getsize(norms_path) / (1024 * 1024)
        print(f"  Norms: {norms_size:.2f} MB")

        # Contar documentos sin cargar todo
        with open(norms_path, "r", encoding="utf-8") as f:
            norms = json.load(f)
            print(f"  Total documents: {len(norms)}")