"""Tests for Feasibility Agent."""
import pytest
from agents.feasibility import FeasibilityAgent


def test_feasibility_agent_classification():
    agent = FeasibilityAgent()
    requirements = [
        {"id": "R1", "title": "Three Tiered Membership Plans"},
        {"id": "R2", "title": "Stripe Recurring Payment Integration"},
        {"id": "R3", "title": "Custom Branded Map Cluster Widget"},
        {"id": "R4", "title": "Twilio SMS Lead Alerts for VIP Vendors"},
    ]

    eval_res = agent.evaluate_requirements(requirements)

    native_titles = [n["title"] for n in eval_res["native_configuration"]]
    custom_titles = [c["title"] for c in eval_res["custom_development"]]

    assert "Three Tiered Membership Plans" in native_titles
    assert "Stripe Recurring Payment Integration" in native_titles
    assert "Custom Branded Map Cluster Widget" in custom_titles
    assert "Twilio SMS Lead Alerts for VIP Vendors" in custom_titles

    assert eval_res["native_percentage"] == 50.0
    assert eval_res["custom_percentage"] == 50.0
