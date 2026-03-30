from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.ml.training_data import SYNTHETIC_TRAINING_DATA

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
VECTORIZER_PATH = ARTIFACT_DIR / "tfidf_vectorizer.joblib"
MODEL_PATH = ARTIFACT_DIR / "logreg_model.joblib"


class TfidfConditionClassifier:
    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
            self._train_and_save()
        self.vectorizer: TfidfVectorizer = joblib.load(VECTORIZER_PATH)
        self.model: LogisticRegression = joblib.load(MODEL_PATH)

    def _train_and_save(self) -> None:
        texts, labels = zip(*SYNTHETIC_TRAINING_DATA)
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        x_train = vectorizer.fit_transform(texts)

        model = LogisticRegression(max_iter=1200, multi_class="multinomial")
        model.fit(x_train, labels)

        joblib.dump(vectorizer, VECTORIZER_PATH)
        joblib.dump(model, MODEL_PATH)

    def predict(self, text: str) -> Dict[str, object]:
        transformed = self.vectorizer.transform([text])
        probabilities = self.model.predict_proba(transformed)[0]
        pred_idx = int(np.argmax(probabilities))
        predicted = str(self.model.classes_[pred_idx])
        confidence = float(probabilities[pred_idx])

        class_probabilities = {
            str(condition): float(prob) for condition, prob in zip(self.model.classes_, probabilities)
        }

        keyword_contributions = self._keyword_contributions(transformed, pred_idx)
        top_keywords = list(keyword_contributions.keys())

        return {
            "predicted_condition": predicted,
            "confidence": confidence,
            "class_probabilities": class_probabilities,
            "top_keywords": top_keywords,
            "keyword_contributions": keyword_contributions,
        }

    def _keyword_contributions(self, transformed, class_index: int) -> Dict[str, float]:
        feature_names: np.ndarray = np.asarray(self.vectorizer.get_feature_names_out())
        coef_row = self.model.coef_[class_index]
        sparse = transformed.tocoo()

        contributions: List[tuple[str, float]] = []
        for idx, value in zip(sparse.col, sparse.data):
            contribution = float(value * coef_row[idx])
            if contribution > 0:
                contributions.append((str(feature_names[idx]), contribution))

        if not contributions:
            for idx, value in zip(sparse.col, sparse.data):
                contribution = float(abs(value * coef_row[idx]))
                contributions.append((str(feature_names[idx]), contribution))

        contributions.sort(key=lambda x: x[1], reverse=True)
        top = contributions[:6]
        return {keyword: round(score, 4) for keyword, score in top}
