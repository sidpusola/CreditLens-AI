# CreditLens AI - Model Comparison Report

**Feature set:** `credit_card`  
**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  
**Best model:** XGBoost

## Current run: `credit_card`

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7074 | 0.1736 | 0.6979 | 0.2780 | 0.7673 |
| Random Forest | 0.7541 | 0.1838 | 0.5948 | 0.2808 | 0.7499 |
| XGBoost * | 0.7330 | 0.1846 | 0.6749 | 0.2899 | 0.7742 |

## XGBoost ROC-AUC progression

| Feature set | ROC-AUC | Delta vs baseline |
|---|---|---|
| Baseline (application_train) | 0.7568 | +0.0000 |
| + bureau | 0.7621 | +0.0053 |
| + previous_application | 0.7676 | +0.0108 |
| + installments_payments | 0.7721 | +0.0153 |
| + credit_card_balance | 0.7742 | +0.0174 |
