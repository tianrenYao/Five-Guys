# User Documentation Screenshot Checklist

This file is a teammate-facing execution checklist for completing the final user documentation.

It is designed for members who are not fully familiar with every implemented module.
Please follow the account suggestions, file naming suggestions, and screenshot scope notes below.

## 1. Goal of this checklist

The final user documentation should explain how each user role uses the system.
Screenshots should therefore:

- show the real implemented interface
- match the role being described
- preserve the sidebar and page title whenever possible
- highlight practical workflows instead of technical details

If page count becomes tight, keep the **high-priority** screenshots first.

---

## 2. Available test accounts

Based on the current seeded accounts in the project, the most reliable available accounts are:

| Username | Password | Role | Recommended Use |
| --- | --- | --- | --- |
| `test_business` | `123456` | `hq_manager` | Use for dashboard, reports, alerts, ESG management, compliance, user management, audit log |
| `test_region` | `123456` | `region_manager` | Use for region-level dashboard, alerts review, compliance score, anomaly detection |
| `test_staff` | `123456` | `store_staff` | Use for login, carbon, waste, training, basic report workflow |

## Important note

There is **no guaranteed pre-seeded `admin` account** in the current default setup.
For that reason:

- use `test_business` to capture most advanced management pages
- if an actual admin account is later created manually, it can be used to replace or supplement one or two screenshots
- for the user manual, this is acceptable because many HQ/admin pages overlap visually

---

## 3. General screenshot rules

## 3.1 Always try to include

- left sidebar
- top page title
- the main table/form/chart area

## 3.2 Avoid

- browser tabs or bookmarks if possible
- personal chat windows or unrelated desktop content
- screenshots that are too zoomed in and lose page context
- screenshots with empty tables if sample data are available

## 3.3 Preferred style

- one screenshot = one clear purpose
- use full-page screenshots for dashboard-style pages
- use partial close-up screenshots only when a modal or scorecard form is the real focus

## 3.4 Naming rule

Save screenshots using this format:

`userdoc_[role]_[module]_[purpose].png`

Examples:

- `userdoc_staff_login_main.png`
- `userdoc_staff_carbon_table_form.png`
- `userdoc_hq_alerts_thresholds.png`
- `userdoc_hq_supplier_scorecard_modal.png`

---

## 4. Minimum screenshot set for the final user document

If time is limited, capture these first.

| No. | Priority | Account | Page | Suggested filename |
| --- | --- | --- | --- | --- |
| 1 | High | `test_staff` | Login page | `userdoc_staff_login_main.png` |
| 2 | High | `test_business` | Dashboard | `userdoc_hq_dashboard_overview.png` |
| 3 | High | `test_staff` | Carbon Tracking | `userdoc_staff_carbon_table_form.png` |
| 4 | High | `test_staff` | Waste Management | `userdoc_staff_waste_table_form.png` |
| 5 | High | `test_business` or `test_staff` | Reports | `userdoc_shared_reports_generate_list.png` |
| 6 | High | `test_business` | Alerts | `userdoc_hq_alerts_thresholds_logs.png` |
| 7 | High | `test_business` | ESG Management - Supplier | `userdoc_hq_supplier_scores.png` |
| 8 | High | `test_business` | User Management | `userdoc_hq_users_table.png` |

This minimum set is enough to support a strong final user document.

---

## 5. Full screenshot execution checklist

## 5.1 Welcome page

- **Account:** no login required
- **Priority:** Low
- **Suggested filename:** `userdoc_public_welcome_page.png`
- **What to capture:**
  - hero section
  - project branding
  - login button
- **Why useful:**
  - helps explain how users first enter the platform
- **Can be omitted?**
  - yes, if page count is tight

---

## 5.2 Login page

- **Account:** no login required
- **Priority:** High
- **Suggested filename:** `userdoc_staff_login_main.png`
- **What to capture:**
  - username field
  - password field
  - login button
  - optional test-account hint area
- **Best description in document:**
  - explain that users enter credentials and are redirected to the dashboard after successful authentication
- **Optional second screenshot:**
  - failed login alert
  - filename: `userdoc_staff_login_error.png`

---

## 5.3 Dashboard overview

- **Account:** `test_business` preferred
- **Priority:** High
- **Suggested filename:** `userdoc_hq_dashboard_overview.png`
- **What to capture:**
  - sidebar
  - summary cards
  - at least one chart
  - SDG 12 panel if visible in the same frame
- **Best description in document:**
  - this is the main overview page after login
  - it helps users quickly inspect carbon, waste, recycling, and reporting performance
- **Notes:**
  - this is one of the strongest screenshots in the entire report
  - make sure data are loaded before capturing

---

## 5.4 Carbon Tracking page

- **Account:** `test_staff`
- **Priority:** High
- **Suggested filename:** `userdoc_staff_carbon_table_form.png`
- **What to capture:**
  - carbon records table
  - add-record form or modal if possible
  - keep the page title and sidebar visible
- **Best description in document:**
  - store staff record operational carbon-related data here
  - records later feed dashboards, reports, and comparisons
- **Optional second screenshot:**
  - comparison or analysis result
  - filename: `userdoc_staff_carbon_compare.png`

---

## 5.5 Waste Management page

- **Account:** `test_staff`
- **Priority:** High
- **Suggested filename:** `userdoc_staff_waste_table_form.png`
- **What to capture:**
  - waste records table
  - key form fields such as waste type, total weight, recycled weight, and date
- **Best description in document:**
  - users record waste generation and recycling-related information here
  - this supports later reporting and monitoring
- **Important note for writer:**
  - mention that recycled amount should remain logically consistent with total waste

---

## 5.6 Reports page

- **Account:** `test_business` preferred, `test_staff` acceptable if page is sufficiently populated
- **Priority:** High
- **Suggested filename:** `userdoc_shared_reports_generate_list.png`
- **What to capture:**
  - generate-report form on the left
  - generated report list on the right
- **Best description in document:**
  - users select a date range and generate a structured sustainability report
  - generated reports are stored and can later be previewed or exported
- **Optional second screenshot:**
  - preview pane with content visible
  - filename: `userdoc_shared_reports_preview.png`
- **Optional third screenshot:**
  - AI ESG analysis area
  - filename: `userdoc_shared_reports_ai_analysis.png`

---

## 5.7 Training page

- **Account:** `test_staff` or `test_business`
- **Priority:** Medium
- **Suggested filename:** `userdoc_shared_training_form_stats.png`
- **What to capture:**
  - training log form on the left
  - statistics cards and records table on the right
- **Best description in document:**
  - this page is used to record sustainability-related staff training and monitor summary indicators
- **Important note for writer:**
  - describe both the data-entry side and the monitoring side

---

## 5.8 Alerts page

- **Account:** `test_business`
- **Priority:** High
- **Suggested filename:** `userdoc_hq_alerts_thresholds_logs.png`
- **What to capture:**
  - alert threshold configuration area
  - alert log table
- **Best description in document:**
  - managers can define threshold rules and review triggered alerts
- **Optional second screenshot:**
  - add-threshold modal
  - filename: `userdoc_hq_alerts_add_threshold_modal.png`
- **Important note for writer:**
  - region managers may mainly review alerts, while HQ/admin users handle more configuration tasks

---

## 5.9 ESG Management - Supplier ESG table

- **Account:** `test_business`
- **Priority:** High
- **Suggested filename:** `userdoc_hq_supplier_scores.png`
- **What to capture:**
  - supplier ESG table
  - tab bar showing Supplier ESG and Company Policies
  - visible score columns and grade column
- **Best description in document:**
  - this page helps management review supplier ESG performance in one place
- **Optional second screenshot:**
  - add/edit supplier modal with scorecard fields
  - filename: `userdoc_hq_supplier_scorecard_modal.png`
- **Important note for writer:**
  - explain the scoring interaction simply: managers select scorecard values and the system calculates results automatically

---

## 5.10 ESG Management - Policy tab

- **Account:** `test_business`
- **Priority:** Medium
- **Suggested filename:** `userdoc_hq_policy_list_detail.png`
- **What to capture:**
  - policy list on the left
  - policy detail on the right
- **Best description in document:**
  - this page supports viewing and maintaining company ESG policies
- **Optional second screenshot:**
  - policy edit form
  - filename: `userdoc_hq_policy_edit_form.png`
- **Important note for writer:**
  - present it as a lightweight governance document-management feature

---

## 5.11 Compliance Score page

- **Account:** `test_region` or `test_business`
- **Priority:** Medium
- **Suggested filename:** `userdoc_manager_compliance_score.png`
- **What to capture:**
  - score gauge
  - grade label
  - dimension breakdown
  - detailed metrics table if visible in same frame
- **Best description in document:**
  - management users use this page to calculate and review a yearly ESG compliance scorecard
- **Important preparation note:**
  - click the calculate button and wait until the page is fully populated before taking the screenshot

---

## 5.12 Anomaly Detection page

- **Account:** `test_region`
- **Priority:** Medium to low
- **Suggested filename:** `userdoc_region_anomaly_detection.png`
- **What to capture:**
  - anomaly results after detection is loaded
  - highlighted abnormal records if available
- **Best description in document:**
  - this page helps managers identify unusual or suspicious operational values
- **Can be shortened in final doc?**
  - yes

---

## 5.13 User Management page

- **Account:** `test_business`
- **Priority:** High
- **Suggested filename:** `userdoc_hq_users_table.png`
- **What to capture:**
  - summary cards
  - user table
  - role badges if visible clearly
- **Best description in document:**
  - this page supports account management, role assignment, and access-scope maintenance
- **Optional second screenshot:**
  - add-user modal
  - filename: `userdoc_hq_users_add_modal.png`
- **Optional third screenshot:**
  - reset-password modal
  - filename: `userdoc_hq_users_reset_password.png`
- **Important note for writer:**
  - mention that region/store assignment is important for some user roles

---

## 5.14 Audit Log page

- **Account:** `test_business`
- **Priority:** Medium
- **Suggested filename:** `userdoc_hq_audit_log.png`
- **What to capture:**
  - statistics cards
  - filters
  - operation table
- **Best description in document:**
  - this page supports traceability and review of important system operations
- **Can be shorter in final doc?**
  - yes

---

## 6. Recommended final figure selection by page limit

## If there is room for only 6 figures

Use these:

1. Login
2. Dashboard
3. Carbon Tracking
4. Waste Management
5. Reports
6. Alerts or ESG Management

## If there is room for 8 figures

Use these:

1. Login
2. Dashboard
3. Carbon Tracking
4. Waste Management
5. Reports
6. Training
7. Alerts
8. ESG Management - Supplier

## If there is room for 10 or more figures

Add these next:

- User Management
- Compliance Score
- Policy Management
- Audit Log
- Anomaly Detection

---

## 7. Suggested division of screenshot work between two teammates

## Teammate A: shared workflow and operational pages

Capture:

- login
- dashboard
- carbon
- waste
- reports
- training

## Teammate B: management and governance pages

Capture:

- alerts
- supplier ESG
- policy management
- compliance score
- anomaly detection
- user management
- audit log

This split is recommended because it follows the same logic as the user document structure: common workflows first, management workflows second.

---

## 8. Final handoff reminders

Before inserting screenshots into the final user document, check:

- the screenshot matches the role being described
- the data are loaded and not empty
- the image is clear enough when scaled down in PDF
- the filename is understandable
- the figure caption focuses on user operation, not technical implementation

If a screenshot looks too crowded, use one full-page screenshot plus one cropped detail screenshot instead of forcing everything into one image.
