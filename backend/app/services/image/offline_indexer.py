import os
import glob
import numpy as np
import joblib
import random
from sklearn.cluster import MiniBatchKMeans
from tqdm import tqdm
from app.services.image.feature_extractor import SIFTFeatureExtractor

# CONFIGURACIÓN
DATA_DIR = "data/fashion/images"  
OUTPUT_DIR = "data/fashion/models"
K_CLUSTERS = 1000
SAMPLE_SIZE_FOR_TRAINING = 3000 

def run_indexing():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    extractor = SIFTFeatureExtractor(n_features=100)
    
    # Obtener lista de todas las imágenes
    print("Leyendo lista de archivos...")
    all_image_paths = glob.glob(os.path.join(DATA_DIR, "*.jpg"))
    print(f"Total de imágenes encontradas: {len(all_image_paths)}")
    
    if len(all_image_paths) == 0:
        print("No se encontraron imágenes en la carpeta indicada")
        return

    # FASE 1: Construir el Codebook
    codebook_path = os.path.join(OUTPUT_DIR, "codebook.pkl")
    
    # Verificamos si ya existe para no re-entrenar
    if not os.path.exists(codebook_path):
        print(f"FASE 1: Entrenando Diccionario Visual con muestra de {SAMPLE_SIZE_FOR_TRAINING}")
        
        # Tomamos una muestra aleatoria
        random.shuffle(all_image_paths)
        training_paths = all_image_paths[:SAMPLE_SIZE_FOR_TRAINING]
        
        all_descriptors = []
        
        for path in tqdm(training_paths, desc="Extrayendo SIFT (Train)"):
            des = extractor.extract(path)
            if des is not None:
                all_descriptors.append(des.astype(np.float64))

        if len(all_descriptors) == 0:
            print("Error: No se pudieron extraer descriptores.")
            return

        # Apilar vectores
        stacked_descriptors = np.vstack(all_descriptors)
        print(f"Total descriptores para K-Means: {stacked_descriptors.shape}")
        
        # Entrenar K-Means
        print(f"Ejecutando K-Means ({K_CLUSTERS} clusters)")
        kmeans = MiniBatchKMeans(n_clusters=K_CLUSTERS, batch_size=1000, n_init='auto')
        kmeans.fit(stacked_descriptors.astype(np.float64))        
        
        # Guardar Codebook
        joblib.dump(kmeans, codebook_path)
        print("Codebook guardado.")
    else:
        print("FASE 1: Codebook ya existe, cargando")
        kmeans = joblib.load(codebook_path)

    # FASE 2: Indexación (Procesar las 44k imágenes)
    print(f"FASE 2: Indexando TODAS las {len(all_image_paths)} imágenes")
    
    inverted_index = {} 
    histograms = {}     
    doc_freq = np.zeros(K_CLUSTERS) 
    N = len(all_image_paths)

    # Aquí iteramos sobre 'all_image_paths'
    for path in tqdm(all_image_paths, desc="Generando Histogramas"):
        img_id = os.path.basename(path) 
        
        # Extraer SIFT
        des = extractor.extract(path)
        
        if des is None: 
            histograms[img_id] = np.zeros(K_CLUSTERS)
            continue
        
        # Predecir palabras visuales
        visual_words = kmeans.predict(des.astype(np.float64))
        
        # Crear Histograma
        hist, _ = np.histogram(visual_words, bins=range(K_CLUSTERS + 1))
        
        # Normalizar (TF)
        total_words = np.sum(hist)
        tf_hist = hist / total_words if total_words > 0 else hist
        
        histograms[img_id] = tf_hist
        
        # Calcular DF (Document Frequency) para luego hacer IDF
        unique_words_in_img = set(visual_words)
        for word in unique_words_in_img:
            doc_freq[word] += 1
            
        # Llenar Índice Invertido (Preliminar)
        for word_idx, tf_val in enumerate(tf_hist):
            if tf_val > 0:
                if word_idx not in inverted_index: inverted_index[word_idx] = []
                inverted_index[word_idx].append([img_id, tf_val])

    # FASE 3: Aplicar IDF y guardar
    print("\nCalculando pesos TF-IDF finales")
    
    # Calcular IDF global (Sumar 1 para evitar división por cero)
    idf = np.log(N / (doc_freq + 1))
    
    final_inverted_index = {}
    norms = {}

    # Recorremos los histogramas para calcular normas y pesos finales
    for img_id, hist in tqdm(histograms.items(), desc="Optimizando Datos"):
        # Reconstruimos el vector TF-IDF
        vec_tfidf = hist * idf
        
        # Calculamos la norma
        norms[img_id] = np.linalg.norm(vec_tfidf)
        
        # Guardamos en el índice invertido el peso ya multiplicado por IDF
        for word_idx, tf_val in enumerate(hist):
            if tf_val > 0:
                weighted_score = tf_val * idf[word_idx]
                if word_idx not in final_inverted_index: final_inverted_index[word_idx] = []
                final_inverted_index[word_idx].append([img_id, weighted_score])    

    print("Guardando archivos en disco")
    joblib.dump(histograms, os.path.join(OUTPUT_DIR, "histograms.pkl"))
    joblib.dump(final_inverted_index, os.path.join(OUTPUT_DIR, "inverted_index.pkl"))
    joblib.dump(idf, os.path.join(OUTPUT_DIR, "idf_weights.pkl"))
    joblib.dump(norms, os.path.join(OUTPUT_DIR, "norms.pkl"))
    
    print("Proceso Terminado, Base de datos multimedia lista")

if __name__ == "__main__":
    run_indexing()