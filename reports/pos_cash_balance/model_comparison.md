# CreditLens AI - Model Comparison Report

**Feature set:** `pos_cash`  
**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  
**Best model:** XGBoost

## Current run: `pos_cash`

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7090 | 0.1745 | 0.6983 | 0.2792 | 0.7717 |
| Random Forest | 0.7615 | 0.1886 | 0.5921 | 0.2861 | 0.7522 |
| XGBoost * | 0.7380 | 0.1869 | 0.6701 | 0.2923 | 0.7773 |

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
