import os
import math
import json

BLOCK_DIR = "blocks_text/"
INDEX_DIR = "index_text/"


def merge_blocks(N, file_name: str):
    """
    N = número total de documentos
    Este merge:
    - fusiona todos los postings
    - calcula DF, IDF
    - calcula TF-IDF
    - calcula normas por documento
    - escribe:
        dictionary.txt
        postings.jsonl
        norms.json
    """

    if not os.path.exists(INDEX_DIR + file_name):
        os.makedirs(INDEX_DIR + file_name)

    # Abrir todos los bloques ordenados
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

    print(f"[MERGE] Encontrados {len(block_files)} bloques para fusionar")

    block_iters = []
    for bf in block_files:
        block_iters.append(open(os.path.join(block_path, bf), "r", encoding="utf-8"))

    # Leer primer término de cada bloque
    current_lines = []
    for idx, f in enumerate(block_iters):
        line = f.readline().strip()
        if line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                term, postings = parts
                current_lines.append((term, postings, idx))

    # Orden inicial por término
    current_lines.sort(key=lambda x: x[0])

    # Archivo final
    dict_path = os.path.join(INDEX_DIR, file_name, "dictionary.txt")
    postings_path = os.path.join(INDEX_DIR, file_name, "postings.jsonl")
    norms_path = os.path.join(INDEX_DIR, file_name, "norms.json")

    dictionary_out = open(dict_path, "w", encoding="utf-8")
    postings_out = open(postings_path, "w", encoding="utf-8")

    # Para normas de documentos
    norms = {}

    terms_processed = 0

    # Merge k-way
    while current_lines:

        # Tomar el menor término lexicográfico
        term, postings_raw, source_idx = current_lines.pop(0)

        # Fusionar postings del mismo término (si varios bloques tienen el mismo término)
        merged_postings = {}

        # Procesar postings del primer bloque
        for pair in postings_raw.split(";"):
            if pair:
                parts = pair.split(",")
                if len(parts) == 2:
                    docID, freq = parts
                    freq = int(freq)
                    merged_postings[docID] = merged_postings.get(docID, 0) + freq

        # Revisar si siguientes líneas tienen el mismo término
        i = 0
        while i < len(current_lines) and current_lines[i][0] == term:
            _, postings_raw2, idx2 = current_lines.pop(i)
            for pair in postings_raw2.split(";"):
                if pair:
                    parts = pair.split(",")
                    if len(parts) == 2:
                        docID, freq = parts
                        freq = int(freq)
                        merged_postings[docID] = merged_postings.get(docID, 0) + freq

        # ---- Calcular DF e IDF ----
        df = len(merged_postings)
        idf = math.log(N / df) if df > 0 else 0

        # ---- Calcular TF-IDF + acumular norma ----
        weighted_postings = []
        for docID, tf in merged_postings.items():
            tf_weight = 1 + math.log(tf)
            w_t_d = tf_weight * idf  # TF-IDF

            # Acumular norma
            norms[docID] = norms.get(docID, 0) + (w_t_d * w_t_d)

            weighted_postings.append([docID, w_t_d])

        # ---- Escribir en postings.jsonl ----
        offset = postings_out.tell()  # pos actual en el archivo
        json.dump({"term": term, "postings": weighted_postings}, postings_out, ensure_ascii=False)
        postings_out.write("\n")

        # ---- Registrar en dictionary ----
        # Formato: term|offset|num_postings
        dictionary_out.write(f"{term}|{offset}|{len(weighted_postings)}\n")

        terms_processed += 1

        # ---- Avanzar la línea en el bloque del que vino el término ----
        next_line = block_iters[source_idx].readline().strip()
        if next_line:
            parts = next_line.split(":", 1)
            if len(parts) == 2:
                t2, p2 = parts
                # Insertar en orden lexicográfico en current_lines
                inserted = False
                for j in range(len(current_lines)):
                    if t2 < current_lines[j][0]:
                        current_lines.insert(j, (t2, p2, source_idx))
                        inserted = True
                        break
                if not inserted:
                    current_lines.append((t2, p2, source_idx))

        # Reordenar por término
        current_lines.sort(key=lambda x: x[0])

    # Cerrar postings y dictionary
    dictionary_out.close()
    postings_out.close()

    # Cerrar todos los bloques
    for f in block_iters:
        f.close()

    # ---- Calcular raíces de las normas y escribir norms.json ----
    norms = {docID: math.sqrt(v) for docID, v in norms.items()}

    with open(norms_path, "w", encoding="utf-8") as nf:
        json.dump(norms, nf, indent=2, ensure_ascii=False)

    print(f"[MERGE] Índice final construido correctamente:")
    print(f" - Términos procesados: {terms_processed}")
    print(f" - Documentos con normas: {len(norms)}")
    print(f" - {dict_path}")
    print(f" - {postings_path}")
    print(f" - {norms_path}")