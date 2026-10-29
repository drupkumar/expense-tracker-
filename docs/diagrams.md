# Aureum system diagrams

## Entity relationship diagram

```mermaid
erDiagram
  USER ||--o{ TRANSACTION : records
  USER ||--o{ BUDGET : plans
  USER ||--o{ GOAL : saves_for
  USER ||--o{ RECURRING_TRANSACTION : schedules
  USER ||--o{ TRANSFER : moves
  USER ||--o{ IMPORT_BATCH : imports
  USER o|--o{ CATEGORY : owns
  CATEGORY ||--o{ TRANSACTION : classifies
  CATEGORY ||--o{ BUDGET : limits
  CATEGORY ||--o{ RECURRING_TRANSACTION : classifies
```

## Data flow diagram

```mermaid
flowchart LR
  Person[User] --> Browser[Bootstrap pages and JavaScript]
  Browser -->|HTTPS form or JSON with CSRF token| Flask[Flask routes]
  Flask --> Auth[Session and ownership checks]
  Auth --> Logic[Validation, finance calculations, receipt parser]
  Logic --> ORM[Flask-SQLAlchemy]
  ORM --> DB[(SQLite or MySQL)]
  Logic --> Files[Receipt uploads and CSV, PDF, XLSX exports]
  Files --> Browser
  DB --> Logic
  Logic --> Browser
```

## Test cases

| Area | Test | Expected result |
|---|---|---|
| Authentication | Register and log in with a strong password | Session starts and dashboard opens |
| Authentication | Submit a POST without a CSRF token | Request is rejected with HTTP 400 |
| Transactions | Create then delete a transaction | Only the signed-in user's row changes |
| Ownership | Submit another user's category ID for a budget | Request is rejected and no budget is saved |
| Budgets | Spend 80% of a category budget | Budget page shows a near-limit alert |
| Recurring | Process an item due today | One dated transaction is created and next date advances |
| Parser | Parse PhonePe/BHIM style receipt text | Amount, payment type, category and confidence are returned |
| Forecast | Regress three increasing monthly totals | Positive slope and next-month projection are calculated |
| Imports | Upload the same mapped CSV twice | Duplicate rows are skipped on the second import |
| Reports | Request PDF, Excel and print versions | Responses use PDF/XLSX formats and the print view renders |
| Deployment config | Normalize a Render PostgreSQL URL | SQLAlchemy uses the installed Psycopg driver |
