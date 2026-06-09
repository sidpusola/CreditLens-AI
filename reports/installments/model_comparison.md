# CreditLens AI - Model Comparison Report

**Feature set:** `installments`  
**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  
**Best model:** XGBoost

## Current run: `installments`

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7039 | 0.1720 | 0.6993 | 0.2760 | 0.7644 |
| Random Forest | 0.7484 | 0.1808 | 0.5992 | 0.2778 | 0.7463 |
| XGBoost * | 0.7318 | 0.1830 | 0.6705 | 0.2876 | 0.7721 |

## XGBoost ROC-AUC progression

| Feature set | ROC-AUC | Delta vs baseline |
|---|---|---|
| Baseline (application_train) | 0.7568 | +0.0000 |
| + bureau | 0.7621 | +0.0053 |
| + previous_application | 0.7676 | +0.0108 |
| + installments_payments | 0.7721 | +0.0153 |
