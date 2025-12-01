import os
import joblib
import numpy as np
import heapq
from app.services.image.feature_extractor import SIFTFeatureExtractor

class ImageSearchEngine:
    def __init__(self, models_dir="data/fashion/models"):
        # Inicializamos SIFT
        self.extractor = SIFTFeatureExtractor(n_features=100)
        
        print(f"Cargando modelos desde {models_dir}")
        try:
            # Cargamos los 4 archivos esenciales
            self.kmeans = joblib.load(os.path.join(models_dir, "codebook.pkl"))
            self.histograms = joblib.load(os.path.join(models_dir, "histograms.pkl"))
            self.inverted_index = joblib.load(os.path.join(models_dir, "inverted_index.pkl"))
            self.idf = joblib.load(os.path.join(models_dir, "idf_weights.pkl"))
            
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
            # Reconstruimos el vector DB usando el IDF guardado
            db_vec = db_hist * self.idf 
            norm_db = np.linalg.norm(db_vec)
            
            if norm_db == 0 or norm_q == 0: 
                sim = 0
            else:
                sim = np.dot(query_vec, db_vec) / (norm_q * norm_db)
            
            if len(heap) < k:
                heapq.heappush(heap, (sim, img_id))
            else:
                if sim > heap[0][0]:
                    heapq.heapreplace(heap, (sim, img_id))
        
        results = sorted(heap, key=lambda x: x[0], reverse=True)
        return [{"id": rid, "score": float(sc)} for sc, rid in results]

    def _search_inverted(self, image_source, k):
        """
        KNN con Indexación Invertida
        Solo busca en las listas de las palabras visuales que aparecen en la query.
        """        
        des = self.extractor.extract(image_source)
        if des is None: return []

        visual_words = self.kmeans.predict(des.astype(np.float64))
        unique_words = set(visual_words)
        
        scores = {}
        
        for word in unique_words:
            if word in self.inverted_index:
                posting_list = self.inverted_index[word]
                for img_id, weight in posting_list:
                    if img_id not in scores: scores[img_id] = 0
                    scores[img_id] += weight 
                    
        top_k = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [{"id": rid, "score": float(sc)} for rid, sc in top_k]