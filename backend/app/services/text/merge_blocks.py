import os
import math
import json
import heapq

BLOCK_DIR = "blocks_text/"
INDEX_DIR = "index_text/"

# Tamaño de buffer para lectura/escritura
BUFFER_SIZE = 8192 * 16  # 128KB por buffer


def merge_blocks(N, file_name: str):
    """
    Merge de bloques SPIMI usando B buffers con heap (priority queue).

    N = número total de documentos

    OPTIMIZACIONES IMPLEMENTADAS:
    1. Min-heap para merge k-way eficiente: O(k log k) en lugar de O(k²)
    2. B buffers de lectura (uno por bloque)
    3. Buffer de escritura para reducir I/O
    4. Lectura anticipada (read-ahead) para mejor throughput

    Salida:
    - dictionary.txt: term|offset|df
    - postings.jsonl: {term, postings: [[docID, weight], ...]}
    - norms.json: {docID: norma}
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
            buffering=BUFFER_SIZE  # Buffer explícito
        )
        block_handles.append(fh)

    # ============================================================
    # INICIALIZAR MIN-HEAP
    # ============================================================
    # Heap de tuplas: (term, postings_str, block_index)
    heap = []

    for idx, fh in enumerate(block_handles):
        line = fh.readline().strip()
        if line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                term, postings = parts
                # Push al heap: (term, postings, block_idx)
                heapq.heappush(heap, (term, postings, idx))

    # ============================================================
    # ABRIR ARCHIVOS DE SALIDA CON BUFFERS
    # ============================================================
    dict_path = os.path.join(output_dir, "dictionary.txt")
    postings_path = os.path.join(output_dir, "postings.jsonl")
    norms_path = os.path.join(output_dir, "norms.json")

    dict_out = open(dict_path, "w", encoding="utf-8", buffering=BUFFER_SIZE)
    postings_out = open(postings_path, "w", encoding="utf-8", buffering=BUFFER_SIZE)

    # Para acumular normas de documentos
    norms = {}
    terms_processed = 0

    # ============================================================
    # MERGE K-WAY CON HEAP
    # ============================================================
    while heap:
        # Extraer término mínimo (O(log k))
        term, postings_str, block_idx = heapq.heappop(heap)

        # Acumular postings del mismo término
        merged_postings = {}

        # Procesar postings del primer bloque
        _parse_postings(postings_str, merged_postings)

        # Fusionar postings duplicados (mismo término en múltiples bloques)
        while heap and heap[0][0] == term:  # Peek: mismo término
            _, postings_str2, block_idx2 = heapq.heappop(heap)
            _parse_postings(postings_str2, merged_postings)

            # Avanzar el bloque que acabamos de consumir
            _advance_block(block_handles[block_idx2], block_idx2, heap)

        # ============================================================
        # CALCULAR TF-IDF Y ACUMULAR NORMAS
        # ============================================================
        df = len(merged_postings)
        idf = math.log(N / df) if df > 0 else 0

        weighted_postings = []
        for docID, tf in merged_postings.items():
            tf_weight = 1 + math.log(tf)
            w_t_d = tf_weight * idf  # TF-IDF

            # Acumular norma (suma de cuadrados)
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
        # ESCRIBIR DICTIONARY
        # ============================================================
        # Formato: term|offset|df
        dict_out.write(f"{term}|{offset}|{df}\n")

        terms_processed += 1

        # Avanzar el bloque del primer término
        _advance_block(block_handles[block_idx], block_idx, heap)

    # ============================================================
    # CERRAR ARCHIVOS
    # ============================================================
    dict_out.close()
    postings_out.close()

    for fh in block_handles:
        fh.close()

    # ============================================================
    # CALCULAR NORMAS (raíz cuadrada) Y ESCRIBIR
    # ============================================================
    norms = {docID: math.sqrt(v) for docID, v in norms.items()}

    with open(norms_path, "w", encoding="utf-8") as nf:
        json.dump(norms, nf, indent=2, ensure_ascii=False)

    print(f"[MERGE] Índice construido exitosamente:")
    print(f"  ✓ Términos únicos: {terms_processed}")
    print(f"  ✓ Documentos indexados: {len(norms)}")
    print(f"  ✓ Bloques fusionados: {len(block_files)}")
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
    Esto mantiene el heap con el siguiente término de cada bloque activo.
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
    Útil para debugging y análisis de rendimiento.
    """
    import time
    start_time = time.time()

    # Usar la función principal
    merge_blocks(N, file_name)

    elapsed = time.time() - start_time

    # Calcular estadísticas del índice
    output_dir = os.path.join(INDEX_DIR, file_name)
    dict_path = os.path.join(output_dir, "dictionary.txt")
    postings_path = os.path.join(output_dir, "postings.jsonl")

    dict_size = os.path.getsize(dict_path) / (1024 * 1024)  # MB
    postings_size = os.path.getsize(postings_path) / (1024 * 1024)  # MB

    print(f"\n[ESTADÍSTICAS]")
    print(f"  Tiempo total: {elapsed:.2f}s")
    print(f"  Tamaño dictionary: {dict_size:.2f} MB")
    print(f"  Tamaño postings: {postings_size:.2f} MB")
    print(f"  Throughput: {(dict_size + postings_size) / elapsed:.2f} MB/s")