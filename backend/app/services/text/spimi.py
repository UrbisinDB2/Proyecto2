import os
from collections import defaultdict
from app.services.text.preprocess import preprocess

BLOCK_DIR = "blocks_text/"
BLOCK_TOKEN_LIMIT = 200000


def spimi_invert(docs, file_name: str):
    """
    Construye bloques SPIMI a partir de una lista de documentos.
    docs: lista de tuplas (docID, contenido_textual)
    """

    if not os.path.exists(BLOCK_DIR + file_name):
        os.makedirs(BLOCK_DIR + file_name)

    block_id = 0
    term_dict = defaultdict(dict)
    token_count = 0

    for docID, text in docs:
        tokens = preprocess(text)

        for t in tokens:
            if docID not in term_dict[t]:
                term_dict[t][docID] = 0
            term_dict[t][docID] += 1

            token_count += 1

            # Cuando la memoria llega al límite → escribir bloque SPIMI
            if token_count >= BLOCK_TOKEN_LIMIT:
                write_block(term_dict, block_id, file_name)
                term_dict = defaultdict(dict)
                block_id += 1
                token_count = 0

    # Último bloque
    write_block(term_dict, block_id, file_name)


def write_block(term_dict, block_id, file_name):
    """
    Escribe un bloque SPIMI al disco en formato:
        termino:docID,freq;docID,freq;...
    """
    block_path = os.path.join(BLOCK_DIR + file_name, f"block_{block_id}.txt")

    # Orden lexicográfico obligatorio para el merge final
    sorted_terms = sorted(term_dict.keys())

    with open(block_path, "w", encoding="utf-8") as f:
        for term in sorted_terms:
            postings = term_dict[term]

            # Formato docID,freq;docID,freq;...
            postings_str = ";".join(f"{d},{freq}" for d, freq in postings.items())

            f.write(f"{term}:{postings_str}\n")

    print(f"[SPIMI] Escribió bloque {block_id} con {len(sorted_terms)} términos.")
