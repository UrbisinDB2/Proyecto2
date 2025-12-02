import time
import os
import joblib
import numpy as np
import faiss
from tabulate import tabulate
from collections import defaultdict

# --- CONFIGURACIÓN ---
MODELS_DIR = "data/fashion/models"
# Ajustamos N para ver la curva
N_VALUES = [1000, 2000, 4000, 8000, 16000, 32000, 44000]
K_NEIGHBORS = 8
NUM_QUERIES = 5 

def build_mini_inverted_index(histograms_slice, idf, n_docs):
    """
    Construye las estructuras en RAM para simular tu motor (Offline).
    Esto NO se mide en el tiempo de búsqueda.
    """
    dense_vectors = [] # Para secuencial
    inverted_index = defaultdict(list) # Para invertido
    norms = [] # Para ambos
    ids_map = [] # Para mapear índice i -> img_id
    
    keys = list(histograms_slice.keys())
    
    for i, img_id in enumerate(keys):
        ids_map.append(img_id)
        hist = histograms_slice[img_id]
        
        # Vector real y norma
        vec = hist * idf
        norm = np.linalg.norm(vec)
        norms.append(norm)
        dense_vectors.append(vec)
        
        # Llenar postings
        for word_idx, val in enumerate(hist):
            if val > 0:
                weight = val * idf[word_idx]
                inverted_index[word_idx].append((i, weight))
                
    return dense_vectors, inverted_index, norms

def search_sequential_strict(query_vec, db_vectors, norms, k=8):
    """Simulación de tu _search_sequential (Fuerza Bruta Lineal)"""
    norm_q = np.linalg.norm(query_vec)
    scores = []
    
    # Bucle explícito documento por documento (O(N))
    for i, vec_db in enumerate(db_vectors):
        # Producto punto
        dot = np.dot(query_vec, vec_db)
        norm_d = norms[i]
        
        score = 0
        if norm_d > 0:
            score = dot / (norm_q * norm_d)
        scores.append(score)
            
    # Ordenar final (O(N log N))
    # Usamos sort simple para simular carga
    scores.sort(reverse=True)
    return scores[:k]

def search_inverted_strict(query_vec, inverted_index, norms, k=8):
    """Simulación de _search_inverted (Acceso Esparso)"""
    norm_q = np.linalg.norm(query_vec)
    scores = defaultdict(float)
    
    # 1. Solo iteramos las palabras que existen en la query
    query_indices = np.where(query_vec > 0)[0]
    
    for word_idx in query_indices:
        q_val = query_vec[word_idx]
        if word_idx in inverted_index:
            # 2. Iteramos solo los documentos relevantes
            for doc_idx, doc_weight in inverted_index[word_idx]:
                scores[doc_idx] += q_val * doc_weight
                
    # 3. Normalización y selección
    final_candidates = []
    for i, dot in scores.items():
        norm_d = norms[i]
        if norm_d > 0:
            final = dot / (norm_q * norm_d)
            final_candidates.append(final)
            
    # Ordenar top K 
    final_candidates.sort(reverse=True)
    return final_candidates[:k]

def run_benchmark():
    print("--- CARGANDO DATOS COMPLETOS (Espere...) ---")
    try:
        histograms_full = joblib.load(os.path.join(MODELS_DIR, "histograms.pkl"))
        idf = joblib.load(os.path.join(MODELS_DIR, "idf_weights.pkl"))
        all_ids = list(histograms_full.keys())
        
        # Matriz completa para Faiss
        print("Generando matriz base...")
        matrix_list = []
        for img_id in all_ids:
            matrix_list.append(histograms_full[img_id] * idf)
        X_full = np.array(matrix_list).astype('float32')
        print(f"Total datos disponibles: {len(all_ids)}")
        
    except Exception as e:
        print(f"Error cargando: {e}")
        return

    results_table = []
    query_vec = X_full[3] # Usamos una imagen como query

    print(f"\n--- INICIANDO BENCHMARK (K={K_NEIGHBORS}) ---")
    
    for N in N_VALUES:
        if N > len(all_ids): break
        
        print(f"Procesando N={N}...", end=" ", flush=True)
        
        # 1. Preparar las estructuras en RAM para este N
        ids_slice = all_ids[:N]
        hist_slice = {i: histograms_full[i] for i in ids_slice}
        
        # Construimos el mini motor para el test
        db_vecs, inv_idx, norms = build_mini_inverted_index(hist_slice, idf, N)
        
        # ------------------------------------------------
        # TEST 1: SECUENCIAL
        # ------------------------------------------------
        start = time.time()
        for _ in range(NUM_QUERIES):
            search_sequential_strict(query_vec, db_vecs, norms, K_NEIGHBORS)
        time_seq = (time.time() - start) / NUM_QUERIES

        # ------------------------------------------------
        # TEST 2: INDEXADO 
        # ------------------------------------------------
        start = time.time()
        for _ in range(NUM_QUERIES):
            search_inverted_strict(query_vec, inv_idx, norms, K_NEIGHBORS)
        time_inv = (time.time() - start) / NUM_QUERIES

        # ------------------------------------------------
        # TEST 3: Faiss 
        # ------------------------------------------------
        index_flat = faiss.IndexFlatIP(X_full.shape[1])
        index_flat.add(X_full[:N]) # Añadimos solo N
        start = time.time()
        for _ in range(NUM_QUERIES):
            index_flat.search(np.array([query_vec]), K_NEIGHBORS)
        time_pg = (time.time() - start) / NUM_QUERIES
        
        results_table.append([
            f"N={N}", 
            f"{time_seq*1000:.2f}", 
            f"{time_inv*1000:.2f}",
            f"{time_pg*1000:.2f}"
        ])

    print("\nResultados (Tiempo en ms):")
    headers = ["Tamaño N", "KNN-Secuencial (Py)", "KNN-Indexado (Py)", "KNN-Faiss"]
    print(tabulate(results_table, headers=headers, tablefmt="github"))

if __name__ == "__main__":
    run_benchmark()