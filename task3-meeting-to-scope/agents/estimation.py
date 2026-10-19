"""Estimation Agent: computes itemized work breakdown, hours, and budget."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EstimationAgent:
    """Estimates engineering hours and budget for native and custom items."""

    BLENDED_HOURLY_RATE = 110.0  # USD per hour

    # Standard hour baselines per item
    HOUR_ESTIMATES = {
        "Three Tiered Membership Plans": {"hours": 6, "complexity": "Low"},
        "Stripe Recurring Payment Integration": {"hours": 4, "complexity": "Low"},
        "Radial Geocoding Location Search": {"hours": 4, "complexity": "Low"},
        "Member Review Moderation Queue": {"hours": 2, "complexity": "Low"},
        "Claim Profile Email Campaign": {"hours": 4, "complexity": "Low"},
        "Custom Branded Map Cluster Widget": {"hours": 18, "complexity": "Medium"},
        "Twilio SMS Lead Alerts for VIP Vendors": {"hours": 12, "complexity": "Medium"},
        "2,500 Vendor Listing Migration": {"hours": 24, "complexity": "High"},
        "301 Redirect Mapping & SEO Preservation": {"hours": 12, "complexity": "Medium"},
    }

    def generate_estimate(
        self,
        feasibility_result: dict[str, Any],
        timeline_weeks: int = 6,
    ) -> dict[str, Any]:
        """Generate itemized WBS, milestones, and cost estimate."""
        native_items = feasibility_result.get("native_configuration", [])
        custom_items = feasibility_result.get("custom_development", [])

        itemized_wbs = []
        total_hours = 0.0

        for item in native_items + custom_items:
            title = item["title"]
            est = self.HOUR_ESTIMATES.get(title, {"hours": 8, "complexity": "Medium"})
            hours = est["hours"]
            cost = hours * self.BLENDED_HOURLY_RATE
            total_hours += hours

            itemized_wbs.append({
                "id": item["id"],
                "title": title,
                "type": item["type"],
                "complexity": est["complexity"],
                "estimated_hours": hours,
                "estimated_cost": cost,
            })

        # Add 10 hours for end-to-end integration testing and production deployment
        qa_hours = 10.0
        total_hours += qa_hours
        itemized_wbs.append({
            "id": "QA-01",
            "title": "Cross-Browser QA, Security Audit, & Production Cutover",
            "type": "deployment_and_qa",
            "complexity": "Medium",
            "estimated_hours": qa_hours,
            "estimated_cost": qa_hours * self.BLENDED_HOURLY_RATE,
        })

        # 4 Structured Milestones
        milestones = [
            {
                "milestone": "Milestone 1: Platform & Billing Architecture",
                "weeks": "Weeks 1-2",
                "hours": 18.0,
                "deliverables": [
                    "DNS connection & SSL activation",
                    "Stripe payment gateway integration & live webhook verification",
                    "3 membership tiers configured (Free, Premium $49/mo, VIP $149/mo)",
                    "Brand color palette and directory typography styling",
                ],
            },
            {
                "milestone": "Milestone 2: Data Migration & Member Onboarding",
                "weeks": "Weeks 2-3",
                "hours": 28.0,
                "deliverables": [
                    "2,500 WordPress listings cleaned and transformed",
                    "Taxonomy and category tree mapped",
                    "Vendor logo and image assets re-hosted",
                    "Claim listing email template and claim tokens ready",
                ],
            },
            {
                "milestone": "Milestone 3: Custom Features (Map Widget & Twilio SMS)",
                "weeks": "Weeks 3-4",
                "hours": 30.0,
                "deliverables": [
                    "Branded pastel map cluster pin widget on homepage",
                    "Interactive vendor filtering on radius change",
                    "Twilio SMS lead notification webhook handler",
                    "SMS dispatch verified with test lead submissions",
                ],
            },
            {
                "milestone": "Milestone 4: QA, 301 Redirects, & Production Launch",
                "weeks": "Weeks 5-6",
                "hours": 20.0,
                "deliverables": [
                    "Comprehensive 301 redirect map for legacy WordPress permalinks",
                    "LocalBusiness Schema.org structured data validation",
                    "2,500 vendor claim profile email blast sent",
                    "Final production cutover and admin training session",
                ],
            },
        ]

        expected_hours = total_hours
        min_hours = round(expected_hours * 0.9, 1)
        max_hours = round(expected_hours * 1.15, 1)

        return {
            "blended_hourly_rate": self.BLENDED_HOURLY_RATE,
            "hours": {
                "expected": expected_hours,
                "min": min_hours,
                "max": max_hours,
            },
            "budget": {
                "expected": round(expected_hours * self.BLENDED_HOURLY_RATE, 2),
                "min": round(min_hours * self.BLENDED_HOURLY_RATE, 2),
                "max": round(max_hours * self.BLENDED_HOURLY_RATE, 2),
            },
            "wbs": itemized_wbs,
            "milestones": milestones,
        }
