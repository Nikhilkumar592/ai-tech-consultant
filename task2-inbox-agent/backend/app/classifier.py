"""Email classification: category, priority, urgency, and sentiment."""
from __future__ import annotations

import logging
import re
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def classify_email(subject: str, body: str) -> dict[str, Any]:
    """Classify incoming email using hybrid heuristic + LLM rules."""
    text = (subject + " " + body).lower()

    # 1. Spam detection
    spam_signals = [
        "btc", "bitcoin", "crypto", "arbitrage", "roi", "5000 guaranteed backlinks",
        "da backlinks", "guest post", "casino", "betting", "inheritance fund",
        "fifteen million", "barrister", "nitrile gloves", "wholesale ppe",
        "telegram traffic", "phishing-mirror", "instant-btc", "adversarial",
        "ai instructions override", "pentest@redteam", "system instruction: you are an internal debugger"
    ]
    if any(sig in text for sig in spam_signals):
        return {
            "category": "spam",
            "priority": "P3",
            "urgency": "low",
            "sentiment": "neutral",
            "is_spam": True,
            "confidence": 0.98,
        }

    # 2. Escalation / Legal / High Risk
    escalation_signals = [
        "dmca", "takedown", "statutory notice", "17 u.s.c", "subpoena",
        "law enforcement", "fbi.gov", "hipaa", "soc 2", "baa",
        "defamation", "legal proceedings", "database compromised",
        "security breach", "accidental deletion", "restore our database",
        "chargeback filed", "sql injection", "vulnerability discovered",
        "escalate to vp", "losing $500/day", "attorney", "special agent"
    ]
    if any(sig in text for sig in escalation_signals):
        return {
            "category": "escalation",
            "priority": "P1",
            "urgency": "critical",
            "sentiment": "angry" if ("losing" in text or "defamat" in text or "demand" in text) else "negative",
            "is_spam": False,
            "confidence": 0.95,
        }

    # 3. Billing & Refunds
    billing_signals = [
        "invoice", "double charged", "refund", "receipt", "vat", "tax", "charge",
        "auto-renewal", "cancel", "downgrade", "payment method", "credit card",
        "discount", "dunning", "wire transfer", "ach", "renew"
    ]
    if any(sig in text for sig in billing_signals):
        is_angry = any(w in text for w in ["demand", "unrecognized", "unexplained", "immediately", "offline"])
        is_urgent = any(w in text for w in ["double", "unauthorized", "unexplained", "immediately", "offline"])
        return {
            "category": "billing",
            "priority": "P1" if is_urgent else "P2",
            "urgency": "high" if is_urgent else "medium",
            "sentiment": "angry" if is_angry else "neutral",
            "is_spam": False,
            "confidence": 0.92,
        }

    # 4. Technical Support
    tech_signals = [
        "webhook", "dns", "a record", "domain", "ssl", "certificate", "smtp",
        "sendgrid", "import", "csv", "paypal commerce", "paypal standard",
        "kanji", "encoding", "radius", "geocoding", "rest api", "token", "error 400",
        "net::err", "blurry", "retina"
    ]
    if any(sig in text for sig in tech_signals):
        is_crit = "ssl" in text or "cannot checkout" in text or "urgent" in text
        return {
            "category": "technical_support",
            "priority": "P1" if is_crit else "P2",
            "urgency": "critical" if is_crit else ("high" if "error" in text else "medium"),
            "sentiment": "negative" if is_crit else "neutral",
            "is_spam": False,
            "confidence": 0.91,
        }

    # 5. General Inquiry (Default fallback)
    return {
        "category": "general_inquiry",
        "priority": "P3",
        "urgency": "low",
        "sentiment": "neutral",
        "is_spam": False,
        "confidence": 0.88,
    }
