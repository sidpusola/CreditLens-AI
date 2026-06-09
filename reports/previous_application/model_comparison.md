# CreditLens AI - Model Comparison Report

**Feature set:** `prev_app`  
**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  
**Best model:** XGBoost

## Current run: `prev_app`

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6965 | 0.1665 | 0.6888 | 0.2681 | 0.7589 |
| Random Forest | 0.7397 | 0.1762 | 0.6052 | 0.2730 | 0.7395 |
| XGBoost * | 0.7265 | 0.1807 | 0.6757 | 0.2851 | 0.7676 |

## XGBoost ROC-AUC progression

| Feature set | ROC-AUC | Delta vs baseline |
|---|---|---|
| Baseline (application_train) | 0.7568 | +0.0000 |
| + bureau | 0.7621 | +0.0053 |
| + previous_application | 0.7676 | +0.0108 |
