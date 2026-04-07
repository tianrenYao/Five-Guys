# Business Sustainability Management Platform

> Group 9 - Five Guys | University Software Engineering Course Project

A web-based enterprise sustainability management platform that helps companies track carbon emissions, manage waste, and auto-generate sustainability reports, aligned with UN SDGs (9, 11, 12, 13).

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, ECharts 5 |
| Backend | Python 3.10+, Flask 3.x |
| Database | MySQL 8.0+ |
| PDF Export | ReportLab |

## Project Structure

```
├── backend/
│   ├── app.py              # Flask main application
│   ├── config.py           # Configuration
│   ├── init_db.py          # Database initialization script
│   ├── routes/
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── carbon.py       # Carbon tracking endpoints
│   │   ├── waste.py        # Waste management endpoints
│   │   ├── report.py       # Report generation endpoints
│   │   └── dashboard.py    # Dashboard data endpoints
│   └── utils/
│       ├── db.py           # Database connection helper
│       └── auth_helper.py  # Auth decorators
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/             # Page-specific JavaScript
│   └── templates/          # Jinja2 HTML templates
├── database/
│   ├── schema.sql          # Full database schema
│   └── DATABASE_DESIGN.md  # Design documentation
├── docs/                   # Project documents (WP deliverables)
├── requirements.txt
└── .gitignore
```

## Quick Start

### 1. Setup MySQL Database

```bash
mysql -u root -p < database/schema.sql
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

### 4. Initialize Test Accounts

```bash
python3 backend/init_db.py
```

### 5. Run the Application

```bash
python3 backend/app.py
```

Visit `http://localhost:5001` in your browser (port 5000 is often occupied by AirPlay on macOS).

### Test Accounts

| Username | Password | Role |
|---|---|---|
| test_business | 123456 | Business Admin |
| test_staff | 123456 | Staff |

## Core Modules

1. **Carbon Footprint Tracking** - Record and calculate carbon emissions from electricity, transport, fuel, commuting
2. **Waste Management** - Track waste by category, calculate recycling rates
3. **Sustainability Report** - Auto-generate monthly/quarterly/annual ESG reports with PDF export

## Team

| Member | Primary Responsibility |
|---|---|
| You Haoyang | WP1 - Requirements & Architecture Design |
| Liu Haopu | WP2 - Database & Backend / WP6 - Documentation |
| Li Sihang | WP3 - Frontend Framework / WP4 - Frontend Modules |
| Lu Yu'an | WP5 - Integration Testing & Deployment |
| Yao Tianren | WP2 contributor / Repository management |
