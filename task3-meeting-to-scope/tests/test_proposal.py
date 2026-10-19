"""Tests for Proposal Agent and Comparison Module."""
import pytest
from agents.analyst import AnalystAgent
from agents.feasibility import FeasibilityAgent
from agents.estimation import EstimationAgent
from agents.proposal import ProposalAgent
from agents.comparison import ScopeComparisonModule


def test_proposal_agent_generation():
    analyst_out = {
        "client_name": "Austin Wedding Vendors Network",
        "constraints": {"timeline_weeks": 6},
    }
    feasibility_out = {
        "native_percentage": 50.0,
        "custom_percentage": 50.0,
    }
    estimation_out = {
        "blended_hourly_rate": 110.0,
        "hours": {"expected": 96.0, "min": 86.4, "max": 110.4},
        "budget": {"expected": 10560.0, "min": 9504.0, "max": 12144.0},
        "wbs": [
            {"id": "REQ-01", "title": "Three Tiered Membership Plans", "type": "native_configuration", "complexity": "Low", "estimated_hours": 6, "estimated_cost": 660.0},
            {"id": "REQ-05", "title": "Custom Branded Map Cluster Widget", "type": "custom_development", "complexity": "Medium", "estimated_hours": 18, "estimated_cost": 1980.0},
        ],
        "milestones": [
            {"milestone": "Milestone 1", "weeks": "Weeks 1-2", "hours": 20, "deliverables": ["Setup"]}
        ],
    }

    agent = ProposalAgent()
    md = agent.generate_proposal(analyst_out, feasibility_out, estimation_out)

    assert "Austin Wedding Vendors Network" in md
    assert "Statement of Work" in md
    assert "$10,560.00" in md
    assert "Work Breakdown Structure" in md


def test_scope_comparison_module():
    ai_est = {
        "hours": {"expected": 96.0},
        "budget": {"expected": 10560.0},
        "wbs": [
            {"title": "Three Tiered Membership Plans"},
            {"title": "Stripe Recurring Payment Integration"},
            {"title": "Custom Branded Map Cluster Widget"},
            {"title": "Twilio SMS Lead Alerts for VIP Vendors"},
            {"title": "2,500 Vendor Listing Migration"},
            {"title": "301 Redirect Mapping & SEO Preservation"},
        ],
        "milestones": [1, 2, 3, 4],
    }

    baseline = {
        "budget": {
            "estimated_hours_expected": 95.0,
            "total_cost_expected": 10450.0,
        },
        "requirements_breakdown": {
            "native_configuration": [{"item": "Three Tiered Membership Plans"}, {"item": "Stripe Payment Gateway Integration"}],
            "custom_development": [{"item": "Custom Branded Map Cluster Widget"}, {"item": "Twilio SMS Lead Notification Webhook"}],
            "data_migration": [{"item": "2,500 Member CSV Data Cleansing & Import"}],
            "seo_and_deployment": [{"item": "301 Redirect Mapping & SEO Cutover"}],
        },
        "milestones": [1, 2, 3, 4],
    }

    comp = ScopeComparisonModule()
    res = comp.compare_scopes(ai_est, baseline)

    assert res["requirement_coverage_rate"] >= 80.0
    assert abs(res["hours"]["delta"]) <= 5.0
    assert "STRONG ALIGNMENT" in res["verdict"]

    report_md = comp.generate_markdown_report(res)
    assert "Benchmark Summary" in report_md
