"""Tests for Analyst Agent."""
import pytest
from agents.analyst import AnalystAgent

SAMPLE_TRANSCRIPT = """
CONSULTATION MEETING TRANSCRIPT
Date: October 14, 2026
Client: Austin Wedding Vendors Network
Participants:
- Alex (Lead Consultant)
- Mark Stevens (Founder)

[00:01:00] Mark Stevens: We have 2,500 vendor listings on WordPress that we need to migrate.
We want 3 tiers: Basic Free, Premium ($49/mo), and VIP ($149/mo) with Stripe recurring payments.
Also an interactive map cluster with Austin pastel pin icons, and Twilio SMS lead notifications.
Our timeline is 6 weeks and budget is around $8,800 to $12,100.
"""


def test_analyst_agent_extraction():
    agent = AnalystAgent()
    res = agent.analyze_transcript(SAMPLE_TRANSCRIPT)

    assert "Austin Wedding Vendors Network" in res["client_name"]
    assert res["constraints"]["timeline_weeks"] == 6
    assert len(res["business_goals"]) >= 2

    req_titles = [r["title"] for r in res["requirements"]]
    assert any("Three Tiered Membership" in t for t in req_titles)
    assert any("Stripe" in t for t in req_titles)
    assert any("2,500 Vendor" in t for t in req_titles)
    assert any("Twilio SMS" in t for t in req_titles)
