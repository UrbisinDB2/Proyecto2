import os
import sys
from collections import defaultdict
from app.services.text.preprocess import preprocess

BLOCK_DIR = "blocks_text/"


def spimi_invert(docs, file_name: str, max_memory_mb=10):
    """
    Construye bloques SPIMI a partir de una lista de documentos.

    docs: lista de tuplas (docID, contenido_textual)
    file_name: nombre del dataset
    max_memory_mb: límite de memoria por bloque en MB (default: 10MB)

    IMPORTANTE: Este límite debe ajustarse según el tamaño del dataset:
    - Dataset pequeño (~1000 docs): 5-10 MB
    - Dataset mediano (~10k docs): 20-50 MB
    - Dataset grande (~100k docs): 100-200 MB
    """

    block_dir = os.path.join(BLOCK_DIR, file_name)
    if not os.path.exists(block_dir):
        os.makedirs(block_dir)

    block_id = 0
    term_dict = defaultdict(dict)

    # Convertir MB a bytes
    MEMORY_LIMIT = max_memory_mb * 1024 * 1024

    print(f"[SPIMI] Iniciando indexación con límite de {max_memory_mb} MB por bloque")
    print(f"[SPIMI] Total documentos: {len(list(docs)) if hasattr(docs, '__len__') else 'streaming'}")

    doc_count = 0

    for docID, text in docs:
        tokens = preprocess(text)

        # Contar frecuencias locales
        local_freqs = defaultdict(int)
        for t in tokens:
            local_freqs[t] += 1

        # Actualizar diccionario global
        for term, freq in local_freqs.items():
            if docID not in term_dict[term]:
                term_dict[term][docID] = 0
            term_dict[term][docID] += freq

        doc_count += 1

        # Estimar memoria usada (cada 100 documentos para eficiencia)
        if doc_count % 100 == 0:
            memory_estimate = estimate_memory(term_dict)

            # Debug: mostrar progreso
            if doc_count % 1000 == 0:
                print(
                    f"[SPIMI] Procesados {doc_count} docs, memoria estimada: {memory_estimate / (1024 * 1024):.2f} MB")

            # Verificar límite de memoria
            if memory_estimate >= MEMORY_LIMIT:
                print(f"[SPIMI] Límite alcanzado con {doc_count} docs, escribiendo bloque {block_id}...")
                write_block(term_dict, block_id, block_dir)
                term_dict = defaultdict(dict)
                block_id += 1
                doc_count = 0  # Reset contador

    # Último bloque (siempre habrá al menos uno)
    if term_dict:
        print(f"[SPIMI] Escribiendo último bloque {block_id}...")
        write_block(term_dict, block_id, block_dir)
        block_id += 1

    print(f"[SPIMI] ✓ Indexación completa: {block_id} bloque(s) creado(s)")
    return block_id


def estimate_memory(term_dict):
    """
    Estima la memoria usada por el diccionario de términos.

    Incluye:
    - Tamaño de los strings (términos y docIDs)
    - Overhead de estructuras de datos de Python
    - Integers (frecuencias)
    """
    total_bytes = 0

    for term, postings in term_dict.items():
        # Tamaño del término (string)
        total_bytes += sys.getsizeof(term)

        # Tamaño del diccionario de postings
        total_bytes += sys.getsizeof(postings)

        # Cada entrada en postings
        for docID, freq in postings.items():
            total_bytes += sys.getsizeof(docID)  # docID string
            total_bytes += sys.getsizeof(freq)  # frecuencia int

    # Overhead del defaultdict principal
    total_bytes += sys.getsizeof(term_dict)

    return total_bytes


def write_block(term_dict, block_id, block_dir):
    """
    Escribe un bloque SPIMI al disco con buffering optimizado.
    Formato: termino:docID,freq;docID,freq;...
    """
    block_path = os.path.join(block_dir, f"block_{block_id}.txt")

    # Ordenar términos lexicográficamente (OBLIGATORIO para merge)
    sorted_terms = sorted(term_dict.keys())

    # Buffer grande para escritura eficiente
    with open(block_path, "w", encoding="utf-8", buffering=8192 * 8) as f:
        lines = []
        buffer_size = 0
        FLUSH_THRESHOLD = 1024 * 1024  # 1MB buffer

        for term in sorted_terms:
            postings = term_dict[term]

            # Ordenar postings por docID (mejor compresión en merge)
            sorted_postings = sorted(postings.items())
            postings_str = ";".join(f"{d},{freq}" for d, freq in sorted_postings)

            line = f"{term}:{postings_str}\n"
            lines.append(line)
            buffer_size += len(line)

            # Flush periódico
            if buffer_size >= FLUSH_THRESHOLD:
                f.writelines(lines)
                lines = []
                buffer_size = 0

        # Escribir residuo
        if lines:
            f.writelines(lines)

    num_terms = len(sorted_terms)
    num_postings = sum(len(postings) for postings in term_dict.values())

    print(f"[SPIMI] ✓ Bloque {block_id}: {num_terms} términos, {num_postings} postings")


# ============================================================
# VERSIÓN ALTERNATIVA: LÍMITE POR NÚMERO DE DOCUMENTOS
# ============================================================

def spimi_invert_by_docs(docs, file_name: str, docs_per_block=5000):
    """
    Versión que crea bloques cada N documentos (más predecible).

    Útil cuando:
    - Los documentos son de tamaño similar
    - Quieres control explícito del número de bloques
    - Prefieres simplicidad sobre optimización de memoria
    """

    block_dir = os.path.join(BLOCK_DIR, file_name)
    if not os.path.exists(block_dir):
        os.makedirs(block_dir)

    block_id = 0
    term_dict = defaultdict(dict)
    doc_count = 0

    print(f"[SPIMI] Creando bloques cada {docs_per_block} documentos")

    for docID, text in docs:
        tokens = preprocess(text)

        local_freqs = defaultdict(int)
        for t in tokens:
            local_freqs[t] += 1

        for term, freq in local_freqs.items():
            if docID not in term_dict[term]:
                term_dict[term][docID] = 0
            term_dict[term][docID] += freq

        doc_count += 1

        # Escribir bloque cada N documentos
        if doc_count >= docs_per_block:
            write_block(term_dict, block_id, block_dir)
            term_dict = defaultdict(dict)
            block_id += 1
            doc_count = 0

    # Último bloque
    if term_dict:
        write_block(term_dict, block_id, block_dir)
        block_id += 1

    print(f"[SPIMI] ✓ Indexación completa: {block_id} bloque(s) creado(s)")
    return block_id


# ============================================================
# FUNCIÓN PARA CALCULAR NÚMERO ÓPTIMO DE BLOQUES
# ============================================================

def calculate_optimal_blocks(total_docs, available_ram_mb=512):
    """
    Calcula configuración óptima de bloques según recursos.

    Regla general: usar ~50% de RAM para construcción de bloques
    """
    # RAM para construcción de bloques (50% del total)
    block_ram = available_ram_mb * 0.5

    # Estimar tamaño por documento (basado en experiencia)
    # Documentos de texto típicos: ~10-50 KB en índice
    bytes_per_doc = 30 * 1024  # 30 KB promedio

    docs_per_block = int((block_ram * 1024 * 1024) / bytes_per_doc)
    num_blocks = (total_docs // docs_per_block) + 1

    print(f"\n[CONFIGURACIÓN RECOMENDADA]")
    print(f"  Total documentos: {total_docs}")
    print(f"  RAM disponible: {available_ram_mb} MB")
    print(f"  Documentos por bloque: {docs_per_block}")
    print(f"  Número de bloques: {num_blocks}")
    print(f"  RAM por bloque: {block_ram / num_blocks:.1f} MB")

    return docs_per_block, num_blocks