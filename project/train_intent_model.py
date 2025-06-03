import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

with open("intent_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
texts = [d["text"] for d in data]
labels = [d["intent"] for d in data]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)
model = LogisticRegression()
model.fit(X, labels)
with open("intent_model.pkl", "wb") as f:
    pickle.dump((vectorizer, model), f)

print("Intent sınıflandırma modeli eğitildi ve kaydedildi.")