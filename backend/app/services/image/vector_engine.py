import os
import joblib
import numpy as np
import heapq
import pandas as pd
from app.services.image.feature_extractor import SIFTFeatureExtractor

class ImageSearchEngine:
    def __init__(self, models_dir="data/fashion/models",data_dir="data/fashion"):
        # Inicializamos SIFT
        self.extractor = SIFTFeatureExtractor(n_features=100)
        
        print(f"Cargando modelos desde {models_dir}")
        try:
            # Cargamos los 4 archivos esenciales
            self.kmeans = joblib.load(os.path.join(models_dir, "codebook.pkl"))
            self.histograms = joblib.load(os.path.join(models_dir, "histograms.pkl"))
            self.inverted_index = joblib.load(os.path.join(models_dir, "inverted_index.pkl"))
            self.idf = joblib.load(os.path.join(models_dir, "idf_weights.pkl"))
            self.norms = joblib.load(os.path.join(models_dir, "norms.pkl"))        

            print("Cargando metadata...")
            df = pd.read_csv(os.path.join(data_dir, "styles.csv"), on_bad_lines='skip')
            df['id'] = df['id'].astype(str)
            self.meta_lookup = df.set_index('id').to_dict(orient='index')             

            self.k_clusters = self.kmeans.n_clusters
            print("Motor Multimedia: Listo para buscar.")
        except Exception as e:
            print(f"Error cargando índices: {e}")

    def _query_to_vector(self, image_source):
        """Convierte imagen de consulta a vector TF-IDF ponderado"""
        # Extraer SIFT
        des = self.extractor.extract(image_source)
        if des is None: return None
        
        # Predecir palabras visuales
        visual_words = self.kmeans.predict(des.astype(np.float64))
        
        # Histograma
        hist, _ = np.histogram(visual_words, bins=range(self.k_clusters + 1))
        
        # TF Normalizado
        total = np.sum(hist)
        tf = hist / total if total > 0 else hist
        
        # Aplicar TF-IDF
        tfidf_vector = tf * self.idf
        return tfidf_vector

    def search(self, image_source, k=8, method="inverted"):
        """
        Método unificado de búsqueda
        """
        if method == "secuencial":
            return self._search_sequential(image_source, k)
        else:
            return self._search_inverted(image_source, k)

    def _search_sequential(self, image_source, k):
        """
        KNN Secuencial: Compara contra TODOS los histogramas.
        Usa Heap para optimizar Top-K.
        """        
        query_vec = self._query_to_vector(image_source)
        if query_vec is None: return []

        heap = []
        norm_q = np.linalg.norm(query_vec)
        
        for img_id, db_hist in self.histograms.items():
            db_vec = db_hist * self.idf

            norm_db = self.norms.get(img_id, 0)
            
            if norm_db == 0 or norm_q == 0: 
                sim = 0
            else:
                sim = np.dot(query_vec, db_vec) / (norm_q * norm_db)
            
            if len(heap) < k:
                heapq.heappush(heap, (sim, img_id))
            else:
                if sim > heap[0][0]:
                    heapq.heapreplace(heap, (sim, img_id))
        
        return self._format_results(sorted(heap, key=lambda x: x[0], reverse=True))

    def _search_inverted(self, image_source, k):
        """
        KNN con Indexación Invertida
        Solo busca en las listas de las palabras visuales que aparecen en la query.
        """        
        query_vec = self._query_to_vector(image_source)
        if query_vec is None: return []

        norm_q = np.linalg.norm(query_vec)
        scores = {} 
        
        # Iteramos solo sobre las palabras visuales presentes en la query
        for word_idx, query_weight in enumerate(query_vec):
            if query_weight > 0 and word_idx in self.inverted_index:
                
                # Lista de imagenes que tienen esta palabra
                posting_list = self.inverted_index[word_idx]
                
                for img_id, doc_weight in posting_list:
                    if img_id not in scores: scores[img_id] = 0
                    # Acumulamos: peso_query * peso_documento
                    scores[img_id] += query_weight * doc_weight 

        # Normalización Final 
        final_results = []
        for img_id, dot_product in scores.items():
            norm_d = self.norms.get(img_id, 0)
            
            if norm_q * norm_d > 0:
                final_score = dot_product / (norm_q * norm_d)
            else:
                final_score = 0
            
            # Descartar scores muy bajos
            if final_score > 0.001:
                final_results.append((img_id, final_score))
                    
        # Ordenar
        top_k = sorted(final_results, key=lambda x: x[1], reverse=True)[:k]
        return self._format_results(top_k)
    
    def _format_results(self, raw_results):
        """Ayuda a formatear la salida con metadata"""
        formatted = []
        for item in raw_results:
            # Detectamos si viene de heap (score, id) o inverted (id, score)
            if isinstance(item, tuple):
                if isinstance(item[0], str): img_id, score = item
                else: score, img_id = item
            else:
                img_id, score = item['id'], item['score']

            clean_id = img_id.replace(".jpg", "")
            meta = self.meta_lookup.get(clean_id, {})
            
            formatted.append({
                "id": img_id,
                "score": float(score),
                "title": meta.get("productDisplayName", "Sin título"),
                "gender": meta.get("gender", ""),
                "year": meta.get("year", ""),
                "url": f"http://127.0.0.1:8000/static/{img_id}" 
            })
        return formatted    
    
