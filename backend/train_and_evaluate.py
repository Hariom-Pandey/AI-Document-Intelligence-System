import os
import sys
from pathlib import Path

# Ensure backend directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.classifier import DocumentClassifier
from app.services.training_data import DOCUMENT_DATASET
from app.services.retriever import DocumentRetriever
from app.services.qa_service import QAService

def main():
    print("=" * 70)
    print("  AI DOCUMENT INTELLIGENCE SYSTEM — MODEL TRAINING & ACCURACY EVALUATION")
    print("=" * 70)

    # 1. Train and evaluate document classifier
    print(f"\n[1] Training Classifier on {len(DOCUMENT_DATASET)} Multi-Class Documents...")
    metrics = DocumentClassifier.train_and_evaluate()

    print(f"\n✓ Cross-Validation Accuracy (5-Fold Stratified): {metrics['cross_val_accuracy']}% (±{metrics['cross_val_std']}%)")
    print(f"✓ In-Sample Fit Accuracy:                         {metrics['train_accuracy']}%")
    print(f"✓ Total Domain Categories:                       {metrics['categories_count']}")
    
    print("\n[2] Per-Category F1 Performance Metrics:")
    for cat, f1 in metrics["per_class_f1"].items():
        bar = "█" * int(f1 // 5)
        print(f"  • {cat:<26}: {f1:>5.1f}% |{bar}")

    # 2. Test unseen real-world samples to verify generalization
    test_cases = [
        (
            "This Employment Agreement ('Agreement') is made between Tech Solutions Inc. and Employee. Employee agrees to confidentiality and intellectual property assignment covenants.",
            "Legal / Contract"
        ),
        (
            "COMMERCIAL TAX INVOICE #84920. Subtotal: $14,200.00, VAT (15%): $2,130.00, Total Amount Payable: $16,330.00. Payment terms: Wire transfer within 30 days.",
            "Financial / Invoice"
        ),
        (
            "The microservices deploy to an AWS EKS Kubernetes cluster via Docker containers. REST API endpoints handle JSON requests with JWT authorization headers.",
            "Technical / Engineering"
        ),
        (
            "Abstract: This empirical paper investigates neural self-attention mechanisms across five benchmark datasets using ANOVA statistical hypothesis testing (p < 0.01).",
            "Academic / Research"
        ),
        (
            "Patient is a 64-year-old female presenting with acute hypertension, elevated systolic blood pressure, and dyspnea. Prescribed Lisinopril 20mg PO daily.",
            "Medical / Healthcare"
        ),
        (
            "Curriculum Vitae: 7 years of full stack software development experience in Python, React, and PostgreSQL. B.S. in Computer Science. Led agile engineering team.",
            "Human Resources / Resume"
        ),
        (
            "Executive Summary: Q4 Strategic Business Proposal to expand enterprise sales into EMEA markets, targeting 18% market share expansion and $12M revenue growth.",
            "General Business / Report"
        )
    ]

    print("\n[3] Testing Real-World Generalization Across All Categories:")
    correct = 0
    for text, expected in test_cases:
        res = DocumentClassifier.classify(text)
        pred = res["category"]
        conf = res["confidence"]
        is_correct = (pred == expected)
        if is_correct:
            correct += 1
        mark = "✓ PASS" if is_correct else "✗ FAIL"
        print(f"  {mark} | Expected: {expected:<24} | Predicted: {pred:<24} | Conf: {conf*100:>5.1f}%")

    test_acc = (correct / len(test_cases)) * 100
    print(f"\n✓ Test Set Generalization Accuracy: {test_acc:.1f}% ({correct}/{len(test_cases)} correct)")
    print("\n" + "=" * 70)
    print("  TRAINING & EVALUATION COMPLETE: Model successfully persisted to disk.")
    print("=" * 70)

if __name__ == "__main__":
    main()

