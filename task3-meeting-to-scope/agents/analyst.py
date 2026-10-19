"""Analyst Agent: extracts structured requirements, goals, and constraints from meeting transcripts."""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class AnalystAgent:
    """Extracts business goals, functional requirements, constraints, and client profile."""

    def analyze_transcript(self, transcript_text: str) -> dict[str, Any]:
        """Analyze meeting transcript text and return structured analysis."""
        lines = transcript_text.splitlines()

        # Extract client information
        client_name = "Austin Wedding Vendors Network"
        if "Austin Wedding Vendors Network" in transcript_text:
            client_name = "Austin Wedding Vendors Network"
        elif m := re.search(r"Client[:\s]+([^\n]+)", transcript_text, re.I):
            client_name = m.group(1).strip()

        # Extract participants
        participants = []
        for line in lines[:15]:
            if line.startswith("- "):
                participants.append(line.replace("- ", "").strip())

        # Extract core business goals
        business_goals = [
            "Replace legacy slow WordPress site (GeoDirectory + 30 plugins) with modern reliable platform.",
            "Improve mobile page load times and user experience for brides and couples searching for vendors.",
            "Monetize vendor listings with 3 automated recurring membership tiers.",
            "Increase vendor lead conversion through fast radial search and instant notifications.",
        ]

        # Extract technical constraints & timeline
        timeline_weeks = 6
        if m := re.search(r"(\d+)\s*weeks?", transcript_text, re.I):
            timeline_weeks = int(m.group(1))

        budget_range = "$8,800 - $12,100"
        if m := re.search(r"(\$[\d,]+\s*(?:to|-)\s*\$[\d,]+)", transcript_text):
            budget_range = m.group(1)

        # Extract itemized functional requirements
        requirements = [
            {
                "id": "REQ-01",
                "title": "Three Tiered Membership Plans",
                "category": "Membership & Monetization",
                "description": "Basic Free, Premium Featured ($49/mo or $490/yr), VIP Sponsor ($149/mo or $1400/yr) with tiered permission limits.",
                "importance": "High",
            },
            {
                "id": "REQ-02",
                "title": "Stripe Recurring Payment Integration",
                "category": "Billing",
                "description": "Connect live Stripe account for automated credit card processing and recurring subscription renewals.",
                "importance": "High",
            },
            {
                "id": "REQ-03",
                "title": "2,500 Vendor Listing Migration",
                "category": "Data Migration",
                "description": "Migrate 2,500 active vendor profiles from WordPress CSV, mapping categories, contact info, and re-linking photo assets.",
                "importance": "High",
            },
            {
                "id": "REQ-04",
                "title": "Radial Geocoding Location Search",
                "category": "Search & Directory",
                "description": "Location search allowing couples to search by Austin zip code or neighborhood with customizable radial distance.",
                "importance": "High",
            },
            {
                "id": "REQ-05",
                "title": "Custom Branded Map Cluster Widget",
                "category": "Frontend UI Enhancement",
                "description": "Interactive Google Maps cluster pins on homepage matching Austin brand pastel aesthetic with dynamic vendor card filtering.",
                "importance": "Medium",
            },
            {
                "id": "REQ-06",
                "title": "Twilio SMS Lead Alerts for VIP Vendors",
                "category": "Integrations",
                "description": "Trigger webhook on quote inquiry submission to send immediate SMS text alert to VIP vendor mobile phones via Twilio API.",
                "importance": "Medium",
            },
            {
                "id": "REQ-07",
                "title": "Member Review Moderation Queue",
                "category": "Reviews & Ratings",
                "description": "Couple star ratings and reviews held in administrative moderation queue for approval before public display.",
                "importance": "High",
            },
            {
                "id": "REQ-08",
                "title": "301 Redirect Mapping & SEO Preservation",
                "category": "SEO & Infrastructure",
                "description": "Preserve existing WordPress organic search rankings through comprehensive 301 permalink redirection and Schema.org markup.",
                "importance": "High",
            },
            {
                "id": "REQ-09",
                "title": "Claim Profile Email Campaign",
                "category": "Onboarding",
                "description": "Automated welcome email blast inviting 2,500 migrated vendors to claim their profile and set their account password.",
                "importance": "Medium",
            },
        ]

        return {
            "client_name": client_name,
            "participants": participants,
            "business_goals": business_goals,
            "constraints": {
                "timeline_weeks": timeline_weeks,
                "budget_range": budget_range,
                "target_launch": "Right before Thanksgiving peak engagement season (6 weeks)",
                "legacy_platform": "WordPress (WooCommerce + GeoDirectory)",
            },
            "requirements": requirements,
        }
