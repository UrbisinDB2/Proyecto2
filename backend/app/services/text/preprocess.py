import re
import nltk
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords

# Descargar recursos de NLTK una sola vez
# Puedes mover esto a un init o a tu build_index para evitar que corra siempre
#TODO
# nltk.download("stopwords")

stemmer = SnowballStemmer("spanish")

stop = set(stopwords.words("spanish"))

RE_NON_ALPHANUM = re.compile(r"[^a-z0-9áéíóúñü]+")
RE_MULTI_SPACES = re.compile(r"\s+")

def preprocess(text: str):
    """
    Preprocesa un texto aplicando:
    - A minúsculas
    - Eliminación de signos
    - Tokenización basada en espacios
    - Eliminación de stopwords
    - Stemming Snowball (optimizado para español)

    Retorna:
        Lista de tokens procesados
    """

    # 1. Lowercase
    text = text.lower()

    # 2. Eliminar caracteres no alfanuméricos (mantiene tildes y ñ)
    text = RE_NON_ALPHANUM.sub(" ", text)

    # 3. Normalizar espacios
    text = RE_MULTI_SPACES.sub(" ", text).strip()

    # 4. Tokenizar
    tokens = text.split()

    # 5. Eliminar stopwords
    tokens = [t for t in tokens if t not in stop]

    # 6. Stemming
    tokens = [stemmer.stem(t) for t in tokens]

    return tokens
