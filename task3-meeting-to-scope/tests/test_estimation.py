"""Tests for Estimation Agent."""
import pytest
from agents.estimation import EstimationAgent


def test_estimation_agent():
    agent = EstimationAgent()
    feasibility_data = {
        "native_configuration": [
            {"id": "R1", "title": "Three Tiered Membership Plans", "type": "native_configuration"},
            {"id": "R2", "title": "Stripe Recurring Payment Integration", "type": "native_configuration"},
        ],
        "custom_development": [
            {"id": "R3", "title": "Custom Branded Map Cluster Widget", "type": "custom_development"},
            {"id": "R4", "title": "Twilio SMS Lead Alerts for VIP Vendors", "type": "custom_development"},
        ],
    }

    est = agent.generate_estimate(feasibility_data, timeline_weeks=6)

    assert est["blended_hourly_rate"] == 110.0
    assert est["hours"]["expected"] > 0
    assert est["budget"]["expected"] == est["hours"]["expected"] * 110.0
    assert len(est["milestones"]) == 4
    assert len(est["wbs"]) >= 5
