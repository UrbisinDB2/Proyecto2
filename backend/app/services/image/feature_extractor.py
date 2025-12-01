import cv2
import numpy as np

class SIFTFeatureExtractor:
    def __init__(self, n_features=100):
        self.sift = cv2.SIFT_create(nfeatures=n_features)

    def extract(self, image_source):
        """
        Acepta ruta de archivo o bytes de imagen.
        Devuelve matriz de descriptores (N, 128).
        """
        try:
            if isinstance(image_source, str):
                img = cv2.imread(image_source)
            else:
                # Convertir bytes a imagen OpenCV
                nparr = np.frombuffer(image_source, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None: return None

            # Escala de grises
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Extracción de vectores característicos
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)
            return descriptors
            
        except Exception as e:
            print(f"Error en SIFT: {e}")
            return None