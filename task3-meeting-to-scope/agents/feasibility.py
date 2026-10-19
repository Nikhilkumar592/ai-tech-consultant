"""Feasibility Agent: cross-references requirements with platform capabilities."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FeasibilityAgent:
    """Evaluates technical feasibility of requirements on Brilliant Directories."""

    # Rules mapping keywords to platform feasibility classification
    NATIVE_FEATURES = {
        "Three Tiered Membership Plans": {
            "type": "native_configuration",
            "feature": "Membership Plans Manager",
            "notes": "Fully supported natively under Finance > Membership Plans. Configure pricing, billing frequency, and feature permissions.",
        },
        "Stripe Recurring Payment Integration": {
            "type": "native_configuration",
            "feature": "Payment Gateways",
            "notes": "Native Stripe payment gateway integration with SCA 3DS compliance and webhook support.",
        },
        "Radial Geocoding Location Search": {
            "type": "native_configuration",
            "feature": "Google Maps & Location Search",
            "notes": "Native Google Maps API integration with postal code and radial distance calculations.",
        },
        "Member Review Moderation Queue": {
            "type": "native_configuration",
            "feature": "Member Reviews Module",
            "notes": "Native setting in Member Settings > Reviews. Toggle 'Require Admin Approval' enabled with zero custom code.",
        },
    }

    CUSTOM_FEATURES = {
        "Custom Branded Map Cluster Widget": {
            "type": "custom_development",
            "tech_stack": "JavaScript, Google Maps MarkerClusterer, Custom CSS",
            "notes": "Requires custom frontend widget development in Design Settings > Custom Widgets with branded pastel pin SVG markers.",
        },
        "Twilio SMS Lead Alerts for VIP Vendors": {
            "type": "custom_development",
            "tech_stack": "Webhook Endpoint, Twilio REST API, Python/Node Serverless",
            "notes": "Outgoing webhook on lead generation connected to a webhook handler dispatching SMS alerts via Twilio.",
        },
        "2,500 Vendor Listing Migration": {
            "type": "custom_development",
            "tech_stack": "Python Data Cleaning Script, CSV Import",
            "notes": "Custom ETL script required to normalize WordPress taxonomy and re-link uploaded image URLs before batch CSV import.",
        },
        "301 Redirect Mapping & SEO Preservation": {
            "type": "custom_development",
            "tech_stack": "DNS Edge Redirect Rules / .htaccess Map",
            "notes": "Requires extracting legacy WordPress permalinks and configuring permanent 301 redirects to new category slugs.",
        },
        "Claim Profile Email Campaign": {
            "type": "native_configuration",
            "feature": "Email Template Manager",
            "notes": "Configure claim listing email template and trigger via bulk member notification system.",
        },
    }

    def evaluate_requirements(self, requirements: list[dict[str, Any]]) -> dict[str, Any]:
        """Classify each requirement as native configuration vs custom development."""
        native_items = []
        custom_items = []
        unsupported_items = []

        for req in requirements:
            title = req["title"]
            if title in self.NATIVE_FEATURES:
                eval_info = self.NATIVE_FEATURES[title]
                native_items.append({
                    "id": req["id"],
                    "title": title,
                    "type": "native_configuration",
                    "feature": eval_info["feature"],
                    "notes": eval_info["notes"],
                    "complexity": "Low",
                })
            elif title in self.CUSTOM_FEATURES:
                eval_info = self.CUSTOM_FEATURES[title]
                target_list = custom_items if eval_info["type"] == "custom_development" else native_items
                target_list.append({
                    "id": req["id"],
                    "title": title,
                    "type": eval_info["type"],
                    "tech_stack": eval_info.get("tech_stack", ""),
                    "notes": eval_info["notes"],
                    "complexity": "Medium" if "Widget" in title or "Migration" in title else "Low",
                })
            else:
                # Fallback rule
                if "custom" in title.lower() or "sms" in title.lower() or "migration" in title.lower():
                    custom_items.append({
                        "id": req["id"],
                        "title": title,
                        "type": "custom_development",
                        "complexity": "Medium",
                        "notes": "Custom engineering required.",
                    })
                else:
                    native_items.append({
                        "id": req["id"],
                        "title": title,
                        "type": "native_configuration",
                        "complexity": "Low",
                        "notes": "Configured via platform admin interface.",
                    })

        return {
            "native_configuration": native_items,
            "custom_development": custom_items,
            "unsupported": unsupported_items,
            "native_percentage": round((len(native_items) / max(1, len(requirements))) * 100, 1),
            "custom_percentage": round((len(custom_items) / max(1, len(requirements))) * 100, 1),
        }
