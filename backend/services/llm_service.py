from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Dict, List

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior credit underwriter at a retail lender. You write concise, "
    "professional underwriting reports. Use ONLY the data provided — never invent "
    "figures, applicant details, or policies. Be objective and decisive. "
    "Structure the report with these sections: Summary, Key Risk Drivers, "
    "Mitigating Factors, Comparison to Precedent, and Recommendation. "
    "Keep it under 250 words. Do not include a preamble or sign-off."
)


class LLMUnavailable(RuntimeError):
    """Raised when the local LLM (Ollama) cannot be reached."""


def _prettify(name: str) -> str:
    return name.replace("_", " ")


def build_prompt(
    prediction: Dict,
    explanation: Dict,
    features: Dict,
    similar: List[Dict],
) -> str:
    """Assemble the RAG context block that grounds the report."""
    lines: List[str] = []
    lines.append("APPLICANT ASSESSMENT")
    lines.append(f"- Risk score: {prediction['risk_score']}/100")
    lines.append(f"- Default probability: {prediction['default_probability'] * 100:.1f}%")
    lines.append(f"- Risk category: {prediction['risk_category']}")

    if features:
        shown = ", ".join(f"{_prettify(k)}={v}" for k, v in list(features.items())[:12])
        lines.append(f"- Applicant inputs: {shown}")

    risk = explanation.get("top_risk_factors", [])
    if risk:
        lines.append("\nTOP RISK FACTORS (push toward default):")
        for f in risk:
            lines.append(f"- {_prettify(f['feature'])} (impact +{f['impact']:.3f})")

    prot = explanation.get("top_protective_factors", [])
    if prot:
        lines.append("\nTOP PROTECTIVE FACTORS (reduce default risk):")
        for f in prot:
            lines.append(f"- {_prettify(f['feature'])} (impact {f['impact']:.3f})")

    # RAG: retrieved precedent
    if similar:
        lines.append("\nSIMILAR PAST APPLICANTS (retrieved by feature similarity):")
        for s in similar:
            lines.append(
                f"- {s['similarity'] * 100:.0f}% similar: scored {s['risk_score']}/100 ({s['risk_category']})"
            )
    else:
        lines.append("\nSIMILAR PAST APPLICANTS: none on record.")

    lines.append("\nWrite the underwriting report based strictly on the above. /no_think")
    return "\n".join(lines)


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
    ) -> str:
        prompt = build_prompt(prediction, explanation, features, similar)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,  # Qwen3 is a thinking model; disable for clean report text
            "options": {"temperature": 0.4},
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
        # Qwen3 is a reasoning model — strip its chain-of-thought. Handles both a full
        # <think>...</think> block and the case where only the closing tag is emitted.
        content = re.sub(r"^.*?</think>", "", content, flags=re.DOTALL)
        content = re.sub(r"</?think>", "", content).strip()
        return content


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService()
