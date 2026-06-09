# CreditLens AI - Model Comparison Report

**Feature set:** `bureau_balance`  
**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  
**Best model:** XGBoost

## Current run: `bureau_balance`

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7089 | 0.1745 | 0.6987 | 0.2793 | 0.7719 |
| Random Forest | 0.7615 | 0.1880 | 0.5887 | 0.2850 | 0.7506 |
| XGBoost * | 0.7380 | 0.1871 | 0.6715 | 0.2927 | 0.7765 |

## XGBoost ROC-AUC progression

| Feature set | ROC-AUC | Delta vs baseline |
|---|---|---|
| Baseline (application_train) | 0.7568 | +0.0000 |
| + bureau | 0.7621 | +0.0053 |
| + previous_application | 0.7676 | +0.0108 |
| + installments_payments | 0.7721 | +0.0153 |
| + credit_card_balance | 0.7742 | +0.0174 |
| + POS_CASH_balance | 0.7773 | +0.0205 |
| + bureau_balance | 0.7765 | +0.0197 |
