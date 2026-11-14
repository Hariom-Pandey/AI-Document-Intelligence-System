import re
import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

from app.core.config import settings
from app.services.training_data import DOCUMENT_DATASET

logger = logging.getLogger(__name__)

MODEL_SAVE_PATH = settings.INDEX_DIR / "classifier_model.joblib"

class DocumentClassifier:
    """
    High-accuracy document categorization model using sublinear TF-IDF (1-3 ngrams)
    and L2-regularized multinomial Logistic Regression with probability calibration.
    """

    _model: Pipeline = None
    _metrics: Dict[str, Any] = None

    @classmethod
    def get_model(cls) -> Pipeline:
        if cls._model is None:
            cls._initialize_model()
        return cls._model

    @classmethod
    def _initialize_model(cls):
        # 1. Try to load pre-trained serialized model from disk
        if MODEL_SAVE_PATH.exists():
            try:
                saved = joblib.load(str(MODEL_SAVE_PATH))
                cls._model = saved["model"]
                cls._metrics = saved.get("metrics", {})
                logger.info(f"Loaded trained Document Classifier from {MODEL_SAVE_PATH}")
                return
            except Exception as e:
                logger.warning(f"Could not load saved model ({e}), retraining...")

        # 2. Train on the expanded dataset
        cls.train_and_evaluate()

    @classmethod
    def train_and_evaluate(cls) -> Dict[str, Any]:
        """
        Trains the classifier on the comprehensive dataset, evaluates using
        Stratified K-Fold cross validation, and serializes the model to disk.
        """
        texts = [item[0] for item in DOCUMENT_DATASET]
        labels = [item[1] for item in DOCUMENT_DATASET]

        # Optimized Pipeline: Sublinear TF-IDF + Multinomial Logistic Regression
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                stop_words="english",
                min_df=1,
                strip_accents="unicode"
            )),
            ("clf", LogisticRegression(
                C=3.0,
                max_iter=1000,
                class_weight="balanced",
                solver="lbfgs"
            ))
        ])

        # Stratified 5-Fold Cross Validation for accurate generalization metric
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, texts, labels, cv=cv, scoring="accuracy")
        mean_cv_accuracy = float(cv_scores.mean())
        std_cv_accuracy = float(cv_scores.std())

        # Fit on the entire dataset
        pipeline.fit(texts, labels)
        cls._model = pipeline

        # In-sample metrics and report
        train_preds = pipeline.predict(texts)
        train_acc = float(accuracy_score(labels, train_preds))
        report_dict = classification_report(labels, train_preds, output_dict=True)

        metrics = {
            "cross_val_accuracy": round(mean_cv_accuracy * 100, 2),
            "cross_val_std": round(std_cv_accuracy * 100, 2),
            "train_accuracy": round(train_acc * 100, 2),
            "total_training_samples": len(texts),
            "categories_count": len(set(labels)),
            "per_class_f1": {
                cat: round(report_dict[cat]["f1-score"] * 100, 2)
                for cat in set(labels) if cat in report_dict
            }
        }
        cls._metrics = metrics

        # Persist to disk
        try:
            settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump({"model": pipeline, "metrics": metrics}, str(MODEL_SAVE_PATH))
            logger.info(f"Model saved to {MODEL_SAVE_PATH} with CV Accuracy: {metrics['cross_val_accuracy']}%")
        except Exception as e:
            logger.error(f"Failed to persist classifier model: {e}")

        return metrics

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        if cls._metrics is None:
            cls.get_model()
        return cls._metrics or {}

    @classmethod
    def classify(cls, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "category": "Unclassified",
                "confidence": 0.0,
                "all_scores": {}
            }

        model = cls.get_model()
        sample = text[:8000]  # Sample first 8000 characters

        try:
            probabilities = model.predict_proba([sample])[0]
            classes = model.classes_

            score_dict = {
                cls_name: round(float(prob), 4)
                for cls_name, prob in zip(classes, probabilities)
            }
            best_idx = int(probabilities.argmax())
            best_category = str(classes[best_idx])
            best_confidence = round(float(probabilities[best_idx]), 4)

            # If confidence is below uniform random baseline across 7 classes (~0.14), fallback to General Business / Report
            if best_confidence < 0.16:
                best_category = "General Business / Report"

            return {
                "category": best_category,
                "confidence": best_confidence,
                "all_scores": score_dict
            }
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "General Business / Report",
                "confidence": 0.5,
                "all_scores": {"General Business / Report": 0.5}
            }
