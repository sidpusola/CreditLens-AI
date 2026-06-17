from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior credit underwriter with 15+ years of experience, writing a credit "
    "memo for the case file. Write in the confident, specific voice of an experienced human "
    "underwriter — never mention AI, models, SHAP, probabilities-as-jargon, or these instructions.\n\n"
    "Hard rules:\n"
    "- Cite concrete figures from the applicant's data (scores, ratios, amounts, similarity %). "
    "Specific numbers are what make a memo credible.\n"
    "- Do NOT quote raw feature-importance weights; translate them into plain underwriting language.\n"
    "- No hedging, no filler, no meta-commentary (never write 'based on the data provided').\n"
    "- Active voice. Short, declarative sentences. Use ONLY the supplied data; invent nothing.\n"
    "- Output EXACTLY these five markdown sections, in order, and nothing else:\n"
    "  ## Risk Drivers\n  ## Evidence\n  ## Comparable Cases\n  ## Decision Rationale\n  ## Recommendation\n"
    "- Risk Drivers: the 2–4 factors most responsible for the risk, highest first. If the data says "
    "risk factors are 'none material', write exactly 'No material risk drivers identified.' as the only "
    "content of this section. NEVER invent risk drivers and NEVER list the absence of a problem "
    "(do not write 'No <something>' as a driver).\n"
    "- Evidence: the specific applicant figures behind those drivers.\n"
    "- Comparable Cases: what the retrieved similar applicants indicate; reference their scores. "
    "A similarity percentage describes ONE comparable applicant — never claim it is a share of peers.\n"
    "- Decision Rationale: weigh the drivers against any mitigants and justify the call.\n"
    "- Recommendation: you MUST state the exact System Recommendation given in the data — do not "
    "substitute your own verdict. The model's calibrated score is authoritative; your job is to "
    "explain that decision, not overturn it. One decisive line with the core reason.\n"
    "- Under 220 words. No title, no preamble, no sign-off."
)

# --- Compact human labels so the memo never echoes raw column names ---
_LABELS = {
    "EXT_SOURCE_1": "external credit score 1",
    "EXT_SOURCE_2": "external credit score 2",
    "EXT_SOURCE_3": "external credit score 3",
    "AMT_CREDIT": "loan amount",
    "AMT_ANNUITY": "loan annuity",
    "AMT_GOODS_PRICE": "goods price",
    "AMT_INCOME_TOTAL": "total income",
    "OWN_CAR_AGE": "car age",
    "DEF_60_CNT_SOCIAL_CIRCLE": "social-circle delinquency (60d)",
    "DEF_30_CNT_SOCIAL_CIRCLE": "social-circle delinquency (30d)",
    "OBS_60_CNT_SOCIAL_CIRCLE": "social-circle observations (60d)",
    "OBS_30_CNT_SOCIAL_CIRCLE": "social-circle observations (30d)",
    "AMT_REQ_CREDIT_BUREAU_QRT": "bureau inquiries (quarter)",
    "AMT_REQ_CREDIT_BUREAU_YEAR": "bureau inquiries (year)",
    "AMT_REQ_CREDIT_BUREAU_MON": "bureau inquiries (month)",
    "REGION_RATING_CLIENT_W_CITY": "region rating (city)",
    "REGION_RATING_CLIENT": "region rating",
    "bureau_debt_to_credit": "bureau debt-to-credit ratio",
    "bureau_total_debt": "total bureau debt",
    "bureau_max_overdue": "max bureau overdue",
    "prev_refusal_ratio": "past refusal rate",
    "prev_approval_ratio": "past approval rate",
    "prev_amt_down_payment_mean": "average prior down payment",
    "prev_consumer_loans_count": "prior consumer loans",
    "late_payment_ratio": "late-payment rate",
    "max_days_late": "worst days late",
    "total_installment_amount": "total installments paid",
    "max_installment_amount": "largest installment",
    "avg_payment_recency": "payment recency",
    "cc_high_utilization_ratio": "high card-utilization rate",
    "cc_max_utilization_ratio": "peak card utilization",
    "cc_avg_drawings": "average card drawings",
    "pos_remaining_installments_mean": "average remaining installments",
    "pos_remaining_installments_max": "max remaining installments",
    "pos_completed_installments_mean": "average completed POS installments",
    "pos_active_loans": "active POS loans",
    "AMT_GOODS_PRICE": "goods price",
}
_CATEGORICAL = {
    "CODE_GENDER": ("gender", {"M": "male", "F": "female", "XNA": "unknown"}),
    "FLAG_OWN_CAR": ("owns car", {"Y": "yes", "N": "no"}),
    "FLAG_OWN_REALTY": ("owns property", {"Y": "yes", "N": "no"}),
    "NAME_EDUCATION_TYPE": ("education", {}),
    "NAME_FAMILY_STATUS": ("family status", {}),
    "NAME_CONTRACT_TYPE": ("contract type", {}),
    "NAME_INCOME_TYPE": ("income type", {}),
    "OCCUPATION_TYPE": ("occupation", {}),
}
_CAT_KEYS = sorted(_CATEGORICAL, key=len, reverse=True)


# Bases whose one-hot value is an incidence count ("0" means none of it).
_COUNT_HINTS = ("delinquency", "observation", "inquiries")


def _fmt_num(val: float) -> str:
    return str(int(val)) if float(val).is_integer() else str(val)


def humanize(name: str) -> str:
    """Human-readable feature label. One-hot value-bearing names keep their value's meaning."""
    if name in _LABELS:
        return _LABELS[name]
    for base in _CAT_KEYS:
        if name == base:
            return _CATEGORICAL[base][0]
        if name.startswith(base + "_"):
            label, values = _CATEGORICAL[base]
            raw = name[len(base) + 1 :]
            return f"{label} {values.get(raw, raw)}"

    # Trailing one-hot numeric value, e.g. DEF_60_CNT_SOCIAL_CIRCLE_0.0 -> value 0.0
    m = re.match(r"^(.*)_(\d+(?:\.\d+)?)$", name)
    if m:
        base, val = m.group(1), float(m.group(2))
        doc = re.match(r"^FLAG_DOCUMENT_(\d+)$", base)
        if doc:
            return f"document {doc.group(1)} {'on file' if val else 'not on file'}"
        label = _LABELS.get(base, base.replace("_", " ").lower())
        is_count = (
            base.startswith(("DEF_", "OBS_"))
            or "SOCIAL_CIRCLE" in base
            or base.startswith("AMT_REQ_CREDIT_BUREAU")
            or any(h in label for h in _COUNT_HINTS)
        )
        if is_count:
            return f"no {label}" if val == 0 else f"{label}: {_fmt_num(val)}"
        return f"{label} = {_fmt_num(val)}"
    return name.replace("_", " ").lower()


def _is_soft_factor(feature: str) -> bool:
    """
    True for factors that describe the ABSENCE of a problem (zero-count one-hots).
    These are mathematically positive SHAP contributors for low-risk applicants but
    read as nonsense under 'Risk Drivers', so we keep them out of that framing.
    """
    h = humanize(feature).lower()
    return h.startswith("no ") or h.endswith("= 0") or h.endswith(": 0") or "not on file" in h


def _recommendation(category: str) -> str:
    return {"Low Risk": "Approve", "Medium Risk": "Manual Review", "High Risk": "Reject"}.get(
        category, "Manual Review"
    )


def _fmt_value(key: str, value) -> Optional[str]:
    """Render an applicant input as readable evidence."""
    if value is None or value == "":
        return None
    if key == "DAYS_BIRTH":
        return f"age {round(-float(value) / 365)} years"
    if key == "DAYS_EMPLOYED":
        return f"employed {round(-float(value) / 365)} years"
    if isinstance(value, (int, float)):
        # Ratios (0–1) read better as percentages
        if key.endswith("_ratio") and 0 <= value <= 1:
            return f"{humanize(key)}: {value * 100:.0f}%"
        if abs(value) >= 1000:
            return f"{humanize(key)}: {value:,.0f}"
        return f"{humanize(key)}: {value}"
    return f"{humanize(key)}: {value}"


def build_prompt(
    prediction: Dict,
    explanation: Dict,
    features: Dict,
    similar: List[Dict],
    case: Optional[Dict] = None,
) -> str:
    lines: List[str] = []
    case = case or {}

    lines.append("APPLICANT FILE")
    lines.append(f"- Name: {case.get('applicant_name', 'Unnamed applicant')}")
    if case.get("applicant_id"):
        lines.append(f"- Case ID: {case['applicant_id']}")
    loan_amt = case.get("loan_amount") or features.get("AMT_CREDIT")
    if loan_amt:
        purpose = case.get("loan_purpose", "general")
        lines.append(f"- Loan requested: {float(loan_amt):,.0f} for {purpose}")

    rec = _recommendation(prediction["risk_category"])
    lines.append("\nMODEL ASSESSMENT")
    lines.append(f"- Default probability: {prediction['default_probability'] * 100:.1f}%")
    lines.append(f"- Risk band: {prediction['risk_category']} ({prediction['risk_score']}/100)")
    lines.append(f"- System recommendation (authoritative): {rec}")

    # Drop "absence of a problem" factors from the risk framing (they confuse the memo)
    risk = [f for f in explanation.get("top_risk_factors", []) if not _is_soft_factor(f["feature"])]
    if risk:
        lines.append("\nMOST INFLUENTIAL RISK FACTORS (ranked; prioritize but do not quote weights):")
        for f in risk:
            lines.append(f"- {humanize(f['feature'])}")
    else:
        lines.append("\nMOST INFLUENTIAL RISK FACTORS: none material — all risk contributions are minor.")
    prot = explanation.get("top_protective_factors", [])
    if prot:
        lines.append("\nMITIGATING FACTORS (ranked):")
        for f in prot:
            lines.append(f"- {humanize(f['feature'])}")

    evidence = [_fmt_value(k, v) for k, v in features.items()]
    evidence = [e for e in evidence if e]
    if evidence:
        lines.append("\nAPPLICANT VALUES (cite these as evidence):")
        for e in evidence:
            lines.append(f"- {e}")

    if similar:
        lines.append("\nCOMPARABLE PAST APPLICANTS (retrieved by similarity):")
        for s in similar:
            lines.append(
                f"- {s['similarity'] * 100:.0f}% similar → scored {s['risk_score']}/100 ({s['risk_category']})"
            )
    else:
        lines.append("\nCOMPARABLE PAST APPLICANTS: none on record.")

    lines.append(
        f"\nWrite the credit memo now. The Recommendation line MUST be '{rec}' — explain it, do not change it. /no_think"
    )
    return "\n".join(lines)


class LLMUnavailable(RuntimeError):
    """Raised when the local LLM (Ollama) cannot be reached."""


class LLMService:
    def __init__(self) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model

    def generate_report(
        self,
        prediction: Dict,
        explanation: Dict,
        features: Dict,
        similar: List[Dict],
        case: Optional[Dict] = None,
    ) -> str:
        prompt = build_prompt(prediction, explanation, features, similar, case)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.45},
        }
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMUnavailable(
                f"Could not reach the LLM at {self.base_url} (model {self.model}). "
                "Is Ollama running and the model pulled?"
            ) from exc

        content = resp.json().get("message", {}).get("content", "").strip()
        # Qwen3 is a reasoning model — strip any chain-of-thought.
        content = re.sub(r"^.*?</think>", "", content, flags=re.DOTALL)
        content = re.sub(r"</?think>", "", content).strip()
        return content


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService()
