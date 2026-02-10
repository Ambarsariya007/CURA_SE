import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load dataset
df = pd.read_csv("ML_MODEL/Symptom2Disease.csv")
df.columns = df.columns.str.strip().str.lower()

if "unnamed: 0" in df.columns:
    df.drop(columns=["unnamed: 0"], inplace=True)

X_text = df["text"]
y = df["label"]

# Encode labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# TF-IDF
tfidf = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words="english"
)
X = tfidf.fit_transform(X_text)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# Random Forest (BEST config)
rf_model = RandomForestClassifier(
    n_estimators=400,
    max_depth=None,
    max_features="sqrt",
    n_jobs=-1,
    random_state=42
)

rf_model.fit(X_train, y_train)

# Evaluate
acc = accuracy_score(y_test, rf_model.predict(X_test))
print(f"✅ Random Forest Accuracy: {acc:.4f}")

# 🔥 SAVE EVERYTHING
joblib.dump(rf_model, "rf_symptom_disease.pkl")
joblib.dump(tfidf, "tfidf.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")

print("✅ Files saved:")
print(" - rf_symptom_disease.pkl")
print(" - tfidf.pkl")
print(" - label_encoder.pkl")
