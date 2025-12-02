import os
import math
import json
import heapq

BLOCK_DIR = "blocks_text/"
INDEX_DIR = "index_text/"
BUFFER_SIZE = 8192 * 16  # 128KB por buffer


def merge_blocks(N, file_name: str):
    """
    Merge de bloques SPIMI usando B buffers con heap (priority queue).

    MODIFICACIÓN CLAVE:
    - El diccionario se escribe ordenado alfabéticamente
    - Esto permite búsquedas binarias posteriores (opcional)
    - Mejora la eficiencia de búsqueda lineal
    """

    output_dir = os.path.join(INDEX_DIR, file_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    block_path = os.path.join(BLOCK_DIR, file_name)

    if not os.path.exists(block_path):
        print(f"[ERROR] No existe el directorio de bloques: {block_path}")
        return

    block_files = sorted(
        [f for f in os.listdir(block_path) if f.endswith(".txt")]
    )

    if not block_files:
        print(f"[ERROR] No se encontraron bloques en: {block_path}")
        return

    print(f"[MERGE] Fusionando {len(block_files)} bloques usando heap de {len(block_files)} buffers")

    # ============================================================
    # ABRIR B BUFFERS (uno por bloque)
    # ============================================================
    block_handles = []
    for bf in block_files:
        fh = open(
            os.path.join(block_path, bf),
            "r",
            encoding="utf-8",
            buffering=BUFFER_SIZE
        )
        block_handles.append(fh)

    # ============================================================
    # INICIALIZAR MIN-HEAP
    # ============================================================
    heap = []

    for idx, fh in enumerate(block_handles):
        line = fh.readline().strip()
        if line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                term, postings = parts
                heapq.heappush(heap, (term, postings, idx))

    # ============================================================
    # ABRIR ARCHIVOS DE SALIDA CON BUFFERS
    # ============================================================
    dict_path = os.path.join(output_dir, "dictionary.txt")
    postings_path = os.path.join(output_dir, "postings.jsonl")
    norms_path = os.path.join(output_dir, "norms.json")

    dict_out = open(dict_path, "w", encoding="utf-8", buffering=BUFFER_SIZE)
    postings_out = open(postings_path, "w", encoding="utf-8", buffering=BUFFER_SIZE)

    norms = {}
    terms_processed = 0

    # ============================================================
    # ALMACENAR ENTRADAS DEL DICCIONARIO PARA ORDENAR
    # ============================================================
    dictionary_entries = []

    # ============================================================
    # MERGE K-WAY CON HEAP
    # ============================================================
    while heap:
        term, postings_str, block_idx = heapq.heappop(heap)

        merged_postings = {}
        _parse_postings(postings_str, merged_postings)

        while heap and heap[0][0] == term:
            _, postings_str2, block_idx2 = heapq.heappop(heap)
            _parse_postings(postings_str2, merged_postings)
            _advance_block(block_handles[block_idx2], block_idx2, heap)

        # ============================================================
        # CALCULAR TF-IDF Y ACUMULAR NORMAS
        # ============================================================
        df = len(merged_postings)
        idf = math.log(N / df) if df > 0 else 0

        weighted_postings = []
        for docID, tf in merged_postings.items():
            tf_weight = 1 + math.log(tf)
            w_t_d = tf_weight * idf

            norms[docID] = norms.get(docID, 0.0) + (w_t_d * w_t_d)

            weighted_postings.append([docID, w_t_d])

        # ============================================================
        # ESCRIBIR POSTINGS
        # ============================================================
        offset = postings_out.tell()
        json.dump(
            {"term": term, "postings": weighted_postings},
            postings_out,
            ensure_ascii=False
        )
        postings_out.write("\n")

        # ============================================================
        # GUARDAR ENTRADA DEL DICCIONARIO (para escribir ordenado después)
        # ============================================================
        dictionary_entries.append((term, offset, df))

        terms_processed += 1
        _advance_block(block_handles[block_idx], block_idx, heap)

    # ============================================================
    # CERRAR ARCHIVOS DE BLOQUES Y POSTINGS
    # ============================================================
    postings_out.close()

    for fh in block_handles:
        fh.close()

    # ============================================================
    # ESCRIBIR DICCIONARIO ORDENADO ALFABÉTICAMENTE
    # ============================================================
    # Los términos ya vienen ordenados del heap, pero garantizamos el orden
    dictionary_entries.sort(key=lambda x: x[0])

    for term, offset, df in dictionary_entries:
        dict_out.write(f"{term}|{offset}|{df}\n")

    dict_out.close()

    # ============================================================
    # CALCULAR NORMAS Y ESCRIBIR
    # ============================================================
    norms = {docID: math.sqrt(v) for docID, v in norms.items()}

    with open(norms_path, "w", encoding="utf-8") as nf:
        json.dump(norms, nf, indent=2, ensure_ascii=False)

    print(f"[MERGE] Índice construido exitosamente:")
    print(f"  ✓ Términos únicos: {terms_processed}")
    print(f"  ✓ Documentos indexados: {len(norms)}")
    print(f"  ✓ Bloques fusionados: {len(block_files)}")
    print(f"  ✓ Diccionario ordenado alfabéticamente")
    print(f"  → {dict_path}")
    print(f"  → {postings_path}")
    print(f"  → {norms_path}")


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _parse_postings(postings_str, merged_postings):
    """
    Parsea string de postings y acumula frecuencias.
    Formato: docID,freq;docID,freq;...
    """
    for pair in postings_str.split(";"):
        if pair:
            parts = pair.split(",")
            if len(parts) == 2:
                docID, freq = parts
                freq = int(freq)
                merged_postings[docID] = merged_postings.get(docID, 0) + freq


def _advance_block(file_handle, block_idx, heap):
    """
    Lee la siguiente línea del bloque y la inserta en el heap.
    """
    line = file_handle.readline().strip()
    if line:
        parts = line.split(":", 1)
        if len(parts) == 2:
            term, postings = parts
            heapq.heappush(heap, (term, postings, block_idx))


# ============================================================
# VERSIÓN CON ESTADÍSTICAS (OPCIONAL)
# ============================================================

def merge_blocks_with_stats(N, file_name: str):
    """
    Versión con estadísticas detalladas del merge.
    """
    import time
    start_time = time.time()

    merge_blocks(N, file_name)

    elapsed = time.time() - start_time

    output_dir = os.path.join(INDEX_DIR, file_name)
    dict_path = os.path.join(output_dir, "dictionary.txt")
    postings_path = os.path.join(output_dir, "postings.jsonl")

    dict_size = os.path.getsize(dict_path) / (1024 * 1024)
    postings_size = os.path.getsize(postings_path) / (1024 * 1024)

    print(f"\n[ESTADÍSTICAS]")
    print(f"  Tiempo total: {elapsed:.2f}s")
    print(f"  Tamaño dictionary: {dict_size:.2f} MB")
    print(f"  Tamaño postings: {postings_size:.2f} MB")
    print(f"  Throughput: {(dict_size + postings_size) / elapsed:.2f} MB/s")