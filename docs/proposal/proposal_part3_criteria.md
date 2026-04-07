# 3. Success Criteria

The following success criteria are defined using the **SMART** framework (Specific, Measurable, Achievable, Relevant, Time-bound) to ensure clear, objective evaluation of project outcomes.

**SC1 — Backend API Completion**
All 22 RESTful API endpoints (covering authentication, carbon tracking, waste management, dashboard analytics, and report generation) shall be fully implemented and pass automated integration testing via Postman by **Week 8**. Each endpoint must return standardised JSON responses with appropriate HTTP status codes.

**SC2 — Frontend Interface Delivery**
Five complete business pages (Login, Dashboard, Carbon Tracking, Waste Management, and Report Generation) shall be developed with responsive layouts (Bootstrap 5) and interactive data visualisations (ECharts 5), rendering correctly on the latest versions of Chrome and Firefox, by **Week 12**.

**SC3 — Remote Deployment and Accessibility**
The platform shall be deployed to the university-provided virtual machine and accessible via a public URL by **Week 14**, enabling the examiner to remotely log in, navigate all modules, and verify functionality from any location using only a standard web browser.

**SC4 — Data Security and Access Control**
The system shall enforce role-based access control with two distinct roles (Business Admin and Staff). All user passwords must be stored using Werkzeug PBKDF2-SHA256 hashing. Every API endpoint (except the login page) shall require session-based authentication, and all database queries shall use parameterised statements to prevent SQL injection.

**SC5 — Sustainability Report Generation and Export**
The report module shall support three reporting periods (monthly, quarterly, annual) and a custom date range. Each generated report must automatically aggregate carbon emission and waste management data for the selected period, and the system shall export reports as downloadable PDF documents containing data summaries, trend analysis, and SDG alignment indicators.
