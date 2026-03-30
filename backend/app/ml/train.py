from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from app.ml.training_data import SYNTHETIC_TRAINING_DATA

ARTIFACT_DIR = Path(__file__).resolve().parent / 'artifacts'
VECTORIZER_PATH = ARTIFACT_DIR / 'tfidf_vectorizer.joblib'
MODEL_PATH = ARTIFACT_DIR / 'logreg_model.joblib'


def main() -> None:
    texts, labels = zip(*SYNTHETIC_TRAINING_DATA)

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    model = LogisticRegression(max_iter=1200, multi_class='multinomial')
    model.fit(x_train_vec, y_train)

    predictions = model.predict(x_test_vec)
    print(classification_report(y_test, predictions))

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model, MODEL_PATH)
    print(f'Saved vectorizer to {VECTORIZER_PATH}')
    print(f'Saved model to {MODEL_PATH}')


if __name__ == '__main__':
    main()
