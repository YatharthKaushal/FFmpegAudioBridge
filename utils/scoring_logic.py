from unidecode import unidecode
from phonetics import metaphone
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def normalize(text):
    return unidecode(text.lower()).replace(",", "").replace(".", "").strip()

def exact_match(text_words, name_words):
    return all(name_word in text_words for name_word in name_words)

def phonetic_match(text_words, name_words):
    text_phonetics = [metaphone(word) for word in text_words]
    name_phonetics = [metaphone(word) for word in name_words]
    return any(name_phonetic in text_phonetics for name_phonetic in name_phonetics)

def fuzzy_component_match(text_words, name_words):
    scores = []
    for name_word in name_words:
        best_score = max(fuzz.ratio(name_word, text_word) for text_word in text_words)
        scores.append(best_score)
    return sum(scores) / len(scores)

def semantic_similarity_window(text, name):
    text_words = text.split()
    name_length = len(name.split())
    windows = [" ".join(text_words[i:i+name_length]) for i in range(len(text_words) - name_length + 1)]
    scores = []

    vectorizer = TfidfVectorizer().fit([name] + windows)
    name_vector = vectorizer.transform([name])

    for window in windows:
        window_vector = vectorizer.transform([window])
        similarity = cosine_similarity(name_vector, window_vector)[0][0] * 100
        scores.append(similarity)

    return max(scores) if scores else 0

def calculate_scores(text, name):
    normalized_text = normalize(text)
    text_words = normalized_text.split()
    normalized_name = normalize(name)
    name_words = normalized_name.split()

    exact = exact_match(text_words, name_words)
    phonetic = phonetic_match(text_words, name_words)
    fuzzy_score = fuzzy_component_match(text_words, name_words)
    semantic_score = semantic_similarity_window(" ".join(text_words), normalized_name)

    weights = {"phonetic": 50, "fuzzy": 40, "semantic": 10}
    total_score = (
        (100 if phonetic else 0) * weights["phonetic"] +
        fuzzy_score * weights["fuzzy"] +
        semantic_score * weights["semantic"]
    ) / sum(weights.values())

    return {
        "exact_match": int(exact),  # Convert boolean to integer
        "phonetic_match": int(phonetic),  # Convert boolean to integer
        "fuzzy_score": round(fuzzy_score, 2),
        # "semantic_similarity": round(semantic_score, 2),
        # "total_score": round(total_score, 2),
        # "match": total_score >= 80
    }
