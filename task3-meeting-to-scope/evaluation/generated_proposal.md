# Technical Proposal & Statement of Work (SOW)

**Project Title:** Directory Modernization, 2,500 Listing Migration & Custom Enhancements  
**Client:** Austin Wedding Vendors Network  
**Prepared By:** AI Tech Consulting Practice, Antigravity Solutions  
**Date:** October 16, 2026  
**Target Delivery Window:** 6 Weeks (Production Launch before Thanksgiving peak season)  

---

## 1. Executive Summary & Business Objectives
Austin Wedding Vendors Network currently operates a directory of over 2,500 active wedding vendors on a legacy WordPress stack (WooCommerce + GeoDirectory + 30 plugins). The current architecture suffers from severe performance bottlenecks (6+ second mobile load times), frequent plugin conflicts, and poor lead conversion.

This project migrates Austin Wedding Vendors Network to **Brilliant Directories**, delivering:
1. **Blazing Fast Performance**: Cloud-native hosting with sub-second page loads and mobile-optimized directory browsing.
2. **Automated Recurring Monetization**: Three clear membership tiers (Basic Free, Premium Featured at $49/mo, and VIP Sponsor at $149/mo) with native Stripe billing.
3. **High-Impact Custom Branding**: A custom interactive Google Maps cluster pin widget tailored to Austin's brand aesthetic.
4. **Instant Lead Delivery**: Native email lead routing plus custom Twilio SMS alerts for VIP vendors.
5. **Zero SEO Loss**: Comprehensive 301 permalink redirection preserving all established Google rankings.

---

## 2. Technical Feasibility & Solution Architecture
To minimize development cost and maximize reliability, this solution leverages Brilliant Directories native capabilities for standard workflows, reserving custom engineering strictly for high-value differentiators.

### A. Native Platform Capabilities (55.6% of Scope)
- **Membership Plan Management**: Free, Premium ($49/mo), and VIP ($149/mo) tiers with automated recurring subscriptions and dunning emails.
- **Stripe Payment Gateway**: Native API connection with SCA 3D-Secure compliance.
- **Radial Geocoding Search**: Native location search powered by Google Maps Places API.
- **Member Review Moderation**: Native administrative approval queue ensuring zero spam or malicious reviews.
- **Claim Listing System**: Native tokenized password setup invitations.

### B. Custom Engineering & Integration (44.4% of Scope)
- **Custom Branded Map Cluster Widget**: Frontend JavaScript widget integrating Google Maps MarkerClusterer with Austin pastel pin icons and dynamic card filtering.
- **Twilio SMS Lead Webhook Handler**: Lightweight webhook microservice receiving lead notifications and dispatching immediate SMS alerts to VIP vendors.
- **WordPress Data Transformation Pipeline**: Python ETL script cleansing 2,500 vendor records, mapping taxonomy, and re-hosting media assets.
- **301 Permalink Redirection Matrix**: Complete URI rewrite rules redirecting legacy WordPress slugs to Brilliant Directories URLs.

---

## 3. Work Breakdown Structure (WBS) & Effort Itemization

| Ref ID | Work Package / Deliverable | Type | Complexity | Hours | Cost (USD) |
|---|---|---|---|---|---|
| REQ-01 | Three Tiered Membership Plans | Native Configuration | Low | 6 hrs | $660.00 |
| REQ-02 | Stripe Recurring Payment Integration | Native Configuration | Low | 4 hrs | $440.00 |
| REQ-04 | Radial Geocoding Location Search | Native Configuration | Low | 4 hrs | $440.00 |
| REQ-07 | Member Review Moderation Queue | Native Configuration | Low | 2 hrs | $220.00 |
| REQ-09 | Claim Profile Email Campaign | Native Configuration | Low | 4 hrs | $440.00 |
| REQ-03 | 2,500 Vendor Listing Migration | Custom Development | High | 24 hrs | $2,640.00 |
| REQ-05 | Custom Branded Map Cluster Widget | Custom Development | Medium | 18 hrs | $1,980.00 |
| REQ-06 | Twilio SMS Lead Alerts for VIP Vendors | Custom Development | Medium | 12 hrs | $1,320.00 |
| REQ-08 | 301 Redirect Mapping & SEO Preservation | Custom Development | Medium | 12 hrs | $1,320.00 |
| QA-01 | Cross-Browser QA, Security Audit, & Production Cutover | Deployment And Qa | Medium | 10.0 hrs | $1,100.00 |
| **TOTAL** | **Full Scope of Work** | **Integrated** | **Expected** | **96.0 hrs** | **$10,560.00** |

---

## 4. Phased Delivery Schedule & Milestones

### Milestone 1: Platform & Billing Architecture (Weeks 1-2 — 18.0 Hours)
**Key Deliverables:**
- [x] DNS connection & SSL activation
- [x] Stripe payment gateway integration & live webhook verification
- [x] 3 membership tiers configured (Free, Premium $49/mo, VIP $149/mo)
- [x] Brand color palette and directory typography styling

### Milestone 2: Data Migration & Member Onboarding (Weeks 2-3 — 28.0 Hours)
**Key Deliverables:**
- [x] 2,500 WordPress listings cleaned and transformed
- [x] Taxonomy and category tree mapped
- [x] Vendor logo and image assets re-hosted
- [x] Claim listing email template and claim tokens ready

### Milestone 3: Custom Features (Map Widget & Twilio SMS) (Weeks 3-4 — 30.0 Hours)
**Key Deliverables:**
- [x] Branded pastel map cluster pin widget on homepage
- [x] Interactive vendor filtering on radius change
- [x] Twilio SMS lead notification webhook handler
- [x] SMS dispatch verified with test lead submissions

### Milestone 4: QA, 301 Redirects, & Production Launch (Weeks 5-6 — 20.0 Hours)
**Key Deliverables:**
- [x] Comprehensive 301 redirect map for legacy WordPress permalinks
- [x] LocalBusiness Schema.org structured data validation
- [x] 2,500 vendor claim profile email blast sent
- [x] Final production cutover and admin training session

---

## 5. Budget, Invoicing & Terms of Engagement
- **Blended Professional Rate:** $110.00 / hour
- **Estimated Project Investment:** $10,560.00 (Estimated range: $9,504.00 – $12,144.00)
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
4. Any requests outside the itemized WBS above will be handled via standard change order at $110.00/hr.

---

**Authorized Signatures:**

_______________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; _______________________________  
**Mark Stevens** &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Alex Vance**  
Founder, Austin Wedding Vendors Network &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Lead AI Tech Consultant, Antigravity  
