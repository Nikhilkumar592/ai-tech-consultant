"""Proposal Agent: generates client-ready technical proposal and Statement of Work."""
from __future__ import annotations

import datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ProposalAgent:
    """Generates professional technical proposal and Statement of Work (SOW)."""

    def generate_proposal(
        self,
        analyst_output: dict[str, Any],
        feasibility_output: dict[str, Any],
        estimation_output: dict[str, Any],
    ) -> str:
        """Synthesize all agent outputs into a comprehensive Markdown proposal."""
        client_name = analyst_output.get("client_name", "Valued Client")
        hours_data = estimation_output.get("hours", {})
        budget_data = estimation_output.get("budget", {})
        rate = estimation_output.get("blended_hourly_rate", 110.0)

        proposal_md = f"""# Technical Proposal & Statement of Work (SOW)

**Project Title:** Directory Modernization, 2,500 Listing Migration & Custom Enhancements  
**Client:** {client_name}  
**Prepared By:** AI Tech Consulting Practice, Antigravity Solutions  
**Date:** {datetime.datetime.utcnow().strftime('%B %d, %Y')}  
**Target Delivery Window:** 6 Weeks (Production Launch before Thanksgiving peak season)  

---

## 1. Executive Summary & Business Objectives
{client_name} currently operates a directory of over 2,500 active wedding vendors on a legacy WordPress stack (WooCommerce + GeoDirectory + 30 plugins). The current architecture suffers from severe performance bottlenecks (6+ second mobile load times), frequent plugin conflicts, and poor lead conversion.

This project migrates {client_name} to **Brilliant Directories**, delivering:
1. **Blazing Fast Performance**: Cloud-native hosting with sub-second page loads and mobile-optimized directory browsing.
2. **Automated Recurring Monetization**: Three clear membership tiers (Basic Free, Premium Featured at $49/mo, and VIP Sponsor at $149/mo) with native Stripe billing.
3. **High-Impact Custom Branding**: A custom interactive Google Maps cluster pin widget tailored to Austin's brand aesthetic.
4. **Instant Lead Delivery**: Native email lead routing plus custom Twilio SMS alerts for VIP vendors.
5. **Zero SEO Loss**: Comprehensive 301 permalink redirection preserving all established Google rankings.

---

## 2. Technical Feasibility & Solution Architecture
To minimize development cost and maximize reliability, this solution leverages Brilliant Directories native capabilities for standard workflows, reserving custom engineering strictly for high-value differentiators.

### A. Native Platform Capabilities ({feasibility_output.get('native_percentage', 55.6)}% of Scope)
- **Membership Plan Management**: Free, Premium ($49/mo), and VIP ($149/mo) tiers with automated recurring subscriptions and dunning emails.
- **Stripe Payment Gateway**: Native API connection with SCA 3D-Secure compliance.
- **Radial Geocoding Search**: Native location search powered by Google Maps Places API.
- **Member Review Moderation**: Native administrative approval queue ensuring zero spam or malicious reviews.
- **Claim Listing System**: Native tokenized password setup invitations.

### B. Custom Engineering & Integration ({feasibility_output.get('custom_percentage', 44.4)}% of Scope)
- **Custom Branded Map Cluster Widget**: Frontend JavaScript widget integrating Google Maps MarkerClusterer with Austin pastel pin icons and dynamic card filtering.
- **Twilio SMS Lead Webhook Handler**: Lightweight webhook microservice receiving lead notifications and dispatching immediate SMS alerts to VIP vendors.
- **WordPress Data Transformation Pipeline**: Python ETL script cleansing 2,500 vendor records, mapping taxonomy, and re-hosting media assets.
- **301 Permalink Redirection Matrix**: Complete URI rewrite rules redirecting legacy WordPress slugs to Brilliant Directories URLs.

---

## 3. Work Breakdown Structure (WBS) & Effort Itemization

| Ref ID | Work Package / Deliverable | Type | Complexity | Hours | Cost (USD) |
|---|---|---|---|---|---|
"""
        for item in estimation_output.get("wbs", []):
            type_label = item["type"].replace("_", " ").title()
            proposal_md += f"| {item['id']} | {item['title']} | {type_label} | {item['complexity']} | {item['estimated_hours']} hrs | ${item['estimated_cost']:,.2f} |\n"

        proposal_md += f"""| **TOTAL** | **Full Scope of Work** | **Integrated** | **Expected** | **{hours_data.get('expected', 96)} hrs** | **${budget_data.get('expected', 10560):,.2f}** |

---

## 4. Phased Delivery Schedule & Milestones

"""
        for ms in estimation_output.get("milestones", []):
            proposal_md += f"### {ms['milestone']} ({ms['weeks']} — {ms['hours']} Hours)\n"
            proposal_md += "**Key Deliverables:**\n"
            for d in ms.get("deliverables", []):
                proposal_md += f"- [x] {d}\n"
            proposal_md += "\n"

        proposal_md += f"""---

## 5. Budget, Invoicing & Terms of Engagement
- **Blended Professional Rate:** ${rate:.2f} / hour
- **Estimated Project Investment:** ${budget_data.get('expected', 10560):,.2f} (Estimated range: ${budget_data.get('min', 9500):,.2f} – ${budget_data.get('max', 12100):,.2f})
- **Payment Milestones:**
  - 30% Upon Project Kickoff & Platform Provisioning
  - 30% Upon Completion of Milestone 2 (Data Migration & Test Import Approval)
  - 25% Upon Completion of Milestone 3 (Custom Map & Twilio Verification)
  - 15% Upon Milestone 4 Production Go-Live & Client Acceptance

---

## 6. Assumptions & Client Responsibilities
1. Client will provide WordPress CSV export including media URL column within 5 business days of kickoff.
2. Client will maintain active Stripe and Twilio account credentials with sufficient API credits.
3. Domain DNS access will be provided 72 hours prior to scheduled production cutover.
4. Any requests outside the itemized WBS above will be handled via standard change order at ${rate:.2f}/hr.

---

**Authorized Signatures:**

_______________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; _______________________________  
**Mark Stevens** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Alex Vance**  
Founder, Austin Wedding Vendors Network &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Lead AI Tech Consultant, Antigravity  
"""
        return proposal_md
