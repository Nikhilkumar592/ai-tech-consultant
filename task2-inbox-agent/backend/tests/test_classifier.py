"""Tests for email classifier."""
import pytest
from app.classifier import classify_email


def test_classify_spam():
    res = classify_email(
        "Monetize traffic with automated Bitcoin trading bot",
        "Sign up at http://bit-scam-link.ru/bonus and receive $50 free credit.",
    )
    assert res["category"] == "spam"
    assert res["is_spam"] is True


def test_classify_escalation_legal():
    res = classify_email(
        "LEGAL NOTICE: Formal DMCA Takedown and Preservation Order",
        "Under 17 U.S.C. 512(c) remove infringing assets immediately or face lawsuit.",
    )
    assert res["category"] == "escalation"
    assert res["priority"] == "P1"
    assert res["urgency"] == "critical"


def test_classify_escalation_security():
    res = classify_email(
        "SQL injection vulnerability discovered in search parameter",
        "Encoded single-quotes cause database syntax dump in headers.",
    )
    assert res["category"] == "escalation"
    assert res["urgency"] == "critical"


def test_classify_billing():
    res = classify_email(
        "Double charged for Annual Premium License",
        "I was charged twice $950 on my credit card. Please refund immediately.",
    )
    assert res["category"] == "billing"
    assert res["urgency"] in ["high", "medium"]


def test_classify_technical_support():
    res = classify_email(
        "Stripe webhook failing with 400 error",
        "Connecting Stripe live keys following your documentation returned 400 Bad Request.",
    )
    assert res["category"] == "technical_support"


def test_classify_general_inquiry():
    res = classify_email(
        "How do member reviews work?",
        "Can visitors leave star ratings without registering an account?",
    )
    assert res["category"] == "general_inquiry"
    assert res["urgency"] == "low"
