# Aureum — Smart Personal Expense Tracker

Web app for the BCA project **Smart Personal Expense Tracker and Financial Analysis System**. It records income and expenses, scans bills, tracks budgets, and shows monthly/yearly charts.

## Features from the synopsis

- Registration, login, and profile
- Income and expense ledger with categories
- Edit, delete, search, and date filters
- Monthly budgets with live usage
- Dashboard and reports with Chart.js
- CSV export

## Extra features

- **Scan a bill**: photograph a paper receipt or a GPay / PhonePe / Paytm screenshot. On-device OCR reads the text; the server extracts amount, merchant, date, and category. You confirm, then it is saved.
- Savings goals
- Smart spending insights
- One-click demo account with sample data
- CSRF protection, login throttling, password reset and safe additive startup migrations
- Recurring entries, custom categories, budget alerts, payment transfers and bulk ledger actions
- Forecast, month comparison, anomaly flags, health score, top merchants and weekday spending
- PDF, Excel and printable reports, plus mapped CSV import with duplicate checks
- Saved light/dark theme, currency setting, global ledger search and account deletion

## Stack (matches the synopsis)

- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- Backend: Python, Flask
- Database: SQLite by default; MySQL and PostgreSQL are also supported through `DATABASE_URL`

## Run on Windows

```powershell
cd C:\Users\Hp\smart-expense-tracker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Existing SQLite databases are upgraded on startup with additive column changes and new tables. Back up `instance/expense.db` before upgrading. The same additive migration runs for MySQL and PostgreSQL. `schema.sql` documents the complete schema and includes optional manual SQL for MySQL installations that need it.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The tests cover authentication, CSRF, transaction ownership, budgets, recurring transactions, receipt parsing and the forecast calculation.

## Screenshots

Project report screenshots are available in [`docs/figures/`](docs/figures/). System diagrams and test cases are in [`docs/diagrams.md`](docs/diagrams.md).

- Create an account, or click **Try the live demo** (`demo@aureum.app` / `demo123`).
- Use **Scan a bill** for receipts and UPI screenshots.

## MySQL or PostgreSQL (optional)

For MySQL, create the database with `schema.sql`. For PostgreSQL, create an empty database in your provider; the app creates its tables at startup. Copy `.env.example` to `.env` and set one of these URLs:

```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/expense_tracker
```

For PostgreSQL, set `DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE`. The app selects the bundled Psycopg 3 driver automatically. Render provides `DATABASE_URL` from its database resource and starts the app with `gunicorn app:app` as configured in `render.yaml`.

## Academic note

Submitted by Drup Kumar Paswan (U18GH24S0085), Seshadripuram Institute of Commerce and Management, under the guidance of Tejaswini, academic year 2026–2027.
