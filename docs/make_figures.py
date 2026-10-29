"""Academic figures and UI plates for the project report."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
    except OSError:
        return ImageFont.load_default()


def box(draw, xy, fill, outline="#1f3d34", width=2, radius=10):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, xy, text, f, fill="#10241e"):
    x0, y0, x1, y1 = xy
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2), text, font=f, fill=fill)


def save(img: Image.Image, name: str):
    path = OUT / name
    img.save(path, "PNG")
    print("wrote", path)


def architecture():
    img = Image.new("RGB", (1400, 780), "#f7faf8")
    d = ImageDraw.Draw(img)
    title = font(22, True)
    body = font(16)
    layers = [
        (40, 70, "Presentation Layer", "HTML5 · CSS3 · Bootstrap 5 · Chart.js · Tesseract.js", "#d8f5ea"),
        (40, 210, "Application Layer (Flask)", "Auth · Transactions · Budgets · Reports · OCR parse · Goals", "#cfe8ff"),
        (40, 350, "Persistence Layer", "SQLAlchemy ORM · SQLite / MySQL · Uploaded receipts", "#ffe7c2"),
        (40, 490, "Client Device", "Browser · Camera / file upload · Session cookie", "#f0e6ff"),
    ]
    d.text((40, 20), "Figure 4.1  Layered architecture of Aureum", font=title, fill="#0d2a22")
    for i, (x, y, h, s, c) in enumerate(layers):
        box(d, (x, y, 1320, y + 110), c)
        d.text((x + 24, y + 22), h, font=font(20, True), fill="#0d2a22")
        d.text((x + 24, y + 62), s, font=body, fill="#24483c")
        if i < 3:
            d.polygon([(700, y + 118), (688, y + 132), (712, y + 132)], fill="#1f3d34")
    save(img, "fig_4_1_architecture.png")


def context():
    img = Image.new("RGB", (1400, 720), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 20), "Figure 4.2  Context-level data flow", font=font(22, True), fill="#0d2a22")
    actors = [
        (60, 280, "Registered User"),
        (60, 480, "Camera / Receipt Photo"),
    ]
    for x, y, t in actors:
        box(d, (x, y, x + 280, y + 90), "#ffffff")
        center_text(d, (x, y, x + 280, y + 90), t, font(16, True), "#0d2a22")
    box(d, (520, 250, 980, 470), "#d8f5ea")
    center_text(d, (520, 250, 980, 400), "Aureum Expense Tracker", font(20, True), "#0d2a22")
    center_text(d, (520, 330, 980, 430), "Flask + Relational DB", font(16), "#24483c")
    box(d, (1080, 180, 1360, 280), "#cfe8ff")
    center_text(d, (1080, 180, 1360, 280), "Charts / Reports", font(16, True), "#0d2a22")
    box(d, (1080, 330, 1360, 430), "#ffe7c2")
    center_text(d, (1080, 330, 1360, 430), "SQLite / MySQL", font(16, True), "#0d2a22")
    box(d, (1080, 480, 1360, 580), "#f0e6ff")
    center_text(d, (1080, 480, 1360, 580), "CSV Export File", font(16, True), "#0d2a22")
    d.line((340, 325, 520, 325), fill="#1f3d34", width=3)
    d.line((340, 525, 700, 525), fill="#1f3d34", width=3)
    d.line((700, 470, 700, 525), fill="#1f3d34", width=3)
    d.line((980, 230, 1080, 230), fill="#1f3d34", width=3)
    d.line((980, 380, 1080, 380), fill="#1f3d34", width=3)
    d.line((980, 430, 1030, 430), fill="#1f3d34", width=3)
    d.line((1030, 430, 1030, 530), fill="#1f3d34", width=3)
    d.line((1030, 530, 1080, 530), fill="#1f3d34", width=3)
    d.text((350, 290), "login, transactions, budgets", font=font(13), fill="#24483c")
    d.text((360, 535), "receipt image", font=font(13), fill="#24483c")
    save(img, "fig_4_2_context.png")


def usecase():
    img = Image.new("RGB", (1400, 860), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 18), "Figure 5.1  Use-case view", font=font(22, True), fill="#0d2a22")
    d.ellipse((70, 360, 230, 560), outline="#1f3d34", width=3)
    d.line((150, 560, 150, 640), fill="#1f3d34", width=3)
    d.line((90, 610, 210, 610), fill="#1f3d34", width=3)
    d.line((150, 640, 110, 730), fill="#1f3d34", width=3)
    d.line((150, 640, 190, 730), fill="#1f3d34", width=3)
    d.text((92, 760), "User", font=font(18, True), fill="#0d2a22")
    box(d, (320, 70, 1320, 820), "#ffffff", radius=6)
    d.text((340, 90), "Aureum System Boundary", font=font(16, True), fill="#1aa37c")
    cases = [
        (380, 150, "Register / Login"),
        (780, 150, "Manage Profile"),
        (380, 250, "Add Income / Expense"),
        (780, 250, "Search and Filter Ledger"),
        (380, 350, "Scan Bill / UPI Screenshot"),
        (780, 350, "Set Category Budget"),
        (380, 450, "View Dashboard Charts"),
        (780, 450, "Generate Reports / CSV"),
        (380, 550, "Create Savings Goal"),
        (780, 550, "Edit / Delete Transaction"),
        (580, 660, "Load Demo Workspace"),
    ]
    for x, y, t in cases:
        d.ellipse((x, y, x + 300, y + 70), outline="#1f3d34", width=2)
        center_text(d, (x, y, x + 300, y + 70), t, font(14), "#0d2a22")
    d.line((230, 460, 380, 385), fill="#1f3d34", width=2)
    save(img, "fig_5_1_usecase.png")


def sequence():
    img = Image.new("RGB", (1400, 820), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 16), "Figure 5.2  Sequence: scan bill and save transaction", font=font(22, True), fill="#0d2a22")
    cols = [(160, "User"), (430, "Browser"), (740, "Flask App"), (1080, "Database")]
    for x, t in cols:
        box(d, (x, 70, x + 160, 120), "#d8f5ea")
        center_text(d, (x, 70, x + 160, 120), t, font(15, True), "#0d2a22")
        d.line((x + 80, 120, x + 80, 780), fill="#98b8ac", width=2)
    steps = [
        (180, "1. Upload / capture photo"),
        (250, "2. Tesseract.js reads text"),
        (320, "3. POST /scan/upload"),
        (390, "4. POST /scan/parse"),
        (460, "5. Return amount, merchant, category"),
        (530, "6. User confirms form"),
        (600, "7. POST /transactions/new"),
        (670, "8. INSERT transaction row"),
        (740, "9. Redirect to dashboard"),
    ]
    y = 170
    for _y, text in steps:
        d.text((40, y), text, font=font(13), fill="#0d2a22")
        y += 68
    d.line((240, 200, 510, 200), fill="#0d2a22", width=2)
    d.line((510, 270, 240, 270), fill="#0d2a22", width=2)
    d.line((510, 340, 820, 340), fill="#0d2a22", width=2)
    d.line((510, 410, 820, 410), fill="#0d2a22", width=2)
    d.line((820, 480, 510, 480), fill="#0d2a22", width=2)
    d.line((240, 550, 820, 550), fill="#0d2a22", width=2)
    d.line((820, 620, 1160, 620), fill="#0d2a22", width=2)
    d.line((820, 760, 240, 760), fill="#0d2a22", width=2)
    save(img, "fig_5_2_sequence.png")


def collaboration():
    img = Image.new("RGB", (1400, 680), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 18), "Figure 5.3  Collaboration among objects", font=font(22, True), fill="#0d2a22")
    nodes = [
        (120, 280, "User"),
        (420, 140, "Scan Page"),
        (420, 420, "Ledger Form"),
        (760, 140, "parser.py"),
        (760, 420, "Transaction"),
        (1100, 280, "SQLAlchemy / DB"),
    ]
    for x, y, t in nodes:
        box(d, (x, y, x + 200, y + 90), "#ffffff")
        center_text(d, (x, y, x + 200, y + 90), t, font(15, True), "#0d2a22")
    d.line((320, 325, 420, 185), fill="#1f3d34", width=2)
    d.line((320, 325, 420, 465), fill="#1f3d34", width=2)
    d.line((620, 185, 760, 185), fill="#1f3d34", width=2)
    d.line((620, 465, 760, 465), fill="#1f3d34", width=2)
    d.line((960, 185, 1100, 325), fill="#1f3d34", width=2)
    d.line((960, 465, 1100, 325), fill="#1f3d34", width=2)
    d.text((500, 90), "1: image + OCR text", font=font(13), fill="#24483c")
    d.text((630, 360), "2: confirmed fields", font=font(13), fill="#24483c")
    d.text((980, 210), "3: persist", font=font(13), fill="#24483c")
    save(img, "fig_5_3_collaboration.png")


def activity():
    img = Image.new("RGB", (900, 1100), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((30, 16), "Figure 5.4  Activity: monthly expense tracking", font=font(20, True), fill="#0d2a22")
    d.ellipse((340, 60, 560, 110), fill="#1f3d34")
    center_text(d, (340, 60, 560, 110), "Start", font(16, True), "#ffffff")
    steps = [
        (70, "Open Aureum in browser"),
        (160, "Register or sign in"),
        (250, "Choose add or scan"),
        (430, "OCR extracts fields"),
        (520, "User confirms amount"),
        (610, "Store in database"),
        (700, "Refresh dashboard / budget bars"),
        (790, "Optional: export CSV"),
    ]
    for y, t in steps:
        box(d, (220, y, 680, y + 70), "#d8f5ea")
        center_text(d, (220, y, 680, y + 70), t, font(15), "#0d2a22")
    box(d, (220, 340, 680, 410), "#ffe7c2")
    center_text(d, (220, 340, 680, 410), "Photo available?", font(15, True), "#0d2a22")
    d.ellipse((340, 900, 560, 960), fill="#1f3d34")
    center_text(d, (340, 900, 560, 960), "End", font(16, True), "#ffffff")
    d.text((700, 360), "No → manual form", font=font(13), fill="#24483c")
    d.text((700, 450), "Yes → OCR path", font=font(13), fill="#24483c")
    save(img, "fig_5_4_activity.png")


def erd():
    img = Image.new("RGB", (1500, 820), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 16), "Figure 5.5  Entity-relationship view", font=font(22, True), fill="#0d2a22")

    def entity(x, y, w, h, title, fields):
        box(d, (x, y, x + w, y + h), "#ffffff", radius=6)
        d.rectangle((x, y, x + w, y + 40), fill="#1aa37c")
        d.text((x + 12, y + 10), title, font=font(15, True), fill="#ffffff")
        for i, f in enumerate(fields):
            d.text((x + 12, y + 50 + i * 24), f, font=font(13), fill="#0d2a22")

    entity(40, 80, 280, 250, "USER", ["id PK", "name", "email UNIQUE", "password_hash", "phone", "monthly_income"])
    entity(400, 80, 280, 210, "CATEGORY", ["id PK", "name UNIQUE", "kind", "icon", "color"])
    entity(760, 80, 320, 310, "TRANSACTION", ["id PK", "user_id FK", "category_id FK", "amount", "kind", "merchant", "txn_date", "source", "receipt_path"])
    entity(400, 430, 300, 230, "BUDGET", ["id PK", "user_id FK", "category_id FK", "month", "year", "amount"])
    entity(760, 430, 300, 230, "GOAL", ["id PK", "user_id FK", "name", "target_amount", "saved_amount", "deadline"])
    d.line((320, 160, 760, 160), fill="#1f3d34", width=2)
    d.line((680, 160, 760, 160), fill="#1f3d34", width=2)
    d.line((180, 330, 180, 540), fill="#1f3d34", width=2)
    d.line((180, 540, 400, 540), fill="#1f3d34", width=2)
    d.line((180, 330, 180, 540), fill="#1f3d34", width=2)
    d.line((180, 620, 760, 620), fill="#1f3d34", width=2)
    d.text((500, 40), "1  to  many from USER to TRANSACTION, BUDGET, GOAL", font=font(14), fill="#24483c")
    save(img, "fig_5_5_er.png")


def dfds():
    img = Image.new("RGB", (1400, 720), "#f7faf8")
    d = ImageDraw.Draw(img)
    d.text((40, 16), "Figure 4.3  Level-1 data flow of the tracking process", font=font(20, True), fill="#0d2a22")
    procs = [
        (80, 300, "1.0 Authenticate"),
        (400, 160, "2.0 Capture Txn"),
        (400, 440, "3.0 Scan Receipt"),
        (760, 300, "4.0 Aggregate"),
        (1080, 180, "5.0 Visualise"),
        (1080, 440, "6.0 Export"),
    ]
    for x, y, t in procs:
        d.ellipse((x, y, x + 220, y + 110), outline="#1f3d34", width=3, fill="#d8f5ea")
        center_text(d, (x, y, x + 220, y + 110), t, font(14, True), "#0d2a22")
    box(d, (400, 620, 760, 690), "#ffe7c2", radius=4)
    center_text(d, (400, 620, 760, 690), "D1  Financial Database", font(14, True), "#0d2a22")
    save(img, "fig_4_3_dfd.png")


def ui_plate(name, title, lines, accent="#3ee0b0"):
    img = Image.new("RGB", (1280, 720), "#06110e")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 240, 720), fill="#071814")
    d.rounded_rectangle((28, 24, 70, 66), 12, fill=accent)
    d.text((38, 32), "A", font=font(22, True), fill="#06241b")
    d.text((80, 32), "Aureum", font=font(16, True), fill="#eff8f3")
    nav = ["Dashboard", "Transactions", "Scan a bill", "Budgets", "Reports", "Goals", "Profile"]
    for i, n in enumerate(nav):
        y = 110 + i * 48
        if n.lower() in title.lower() or (n == "Scan a bill" and "scan" in title.lower()):
            d.rounded_rectangle((18, y, 222, y + 40), 10, fill="#123028")
        d.text((36, y + 10), n, font=font(14), fill="#cfe7de")
    d.text((280, 36), title, font=font(28, True), fill="#eff8f3")
    y = 110
    for line in lines:
        d.rounded_rectangle((280, y, 1220, y + 70), 16, fill="#0e241e", outline="#1d3f36")
        d.text((304, y + 22), line, font=font(16), fill="#cfe7de")
        y += 86
    save(img, name)


def ui_plates():
    ui_plate(
        "fig_6_1_login.png",
        "Sign in",
        [
            "Email and password authentication with hashed secrets",
            "Create account for a private personal ledger",
            "Try the live demo workspace (demo@aureum.app)",
            "No bank login and no payment processing",
        ],
    )
    # richer login-like plate
    img = Image.new("RGB", (1400, 800), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((70, 80), "Money, made visible.", font=font(42, True), fill="#eff8f3")
    d.text((70, 150), "Smart Personal Expense Tracker and Financial Analysis System", font=font(16), fill="#93b0a6")
    d.rounded_rectangle((820, 120, 1320, 680), 28, fill="#0a1c17", outline="#1d3f36")
    d.text((860, 170), "Welcome back", font=font(26, True), fill="#eff8f3")
    d.rounded_rectangle((860, 240, 1280, 300), 12, outline="#2a4a40")
    d.text((880, 258), "you@college.edu", font=font(14), fill="#93b0a6")
    d.rounded_rectangle((860, 330, 1280, 390), 12, outline="#2a4a40")
    d.text((880, 348), "Password", font=font(14), fill="#93b0a6")
    d.rounded_rectangle((860, 430, 1280, 490), 14, fill="#3ee0b0")
    center_text(d, (860, 430, 1280, 490), "Enter Aureum", font(16, True), "#06241b")
    d.rounded_rectangle((860, 520, 1280, 575), 14, outline="#2a4a40")
    center_text(d, (860, 520, 1280, 575), "Try the live demo", font(15), "#eff8f3")
    save(img, "fig_6_1_login.png")

    img = Image.new("RGB", (1400, 820), "#06110e")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 250, 820), fill="#071814")
    d.text((30, 30), "Aureum", font=font(18, True), fill="#3ee0b0")
    for i, n in enumerate(["Dashboard", "Transactions", "Scan a bill", "Budgets", "Reports", "Goals", "Profile"]):
        d.text((30, 120 + i * 42), n, font=font(14), fill="#cfe7de")
    d.text((290, 30), "Aarav, here is your month in motion.", font=font(24, True), fill="#eff8f3")
    cards = [("Income", "Rs 53,000"), ("Spent", "Rs 7,960"), ("Left to use", "Rs 45,040"), ("Savings rate", "85%")]
    for i, (k, v) in enumerate(cards):
        x = 290 + i * 270
        d.rounded_rectangle((x, 100, x + 250, 210), 18, fill="#0e241e", outline="#1d3f36")
        d.text((x + 20, 120), k, font=font(13), fill="#93b0a6")
        d.text((x + 20, 150), v, font=font(22, True), fill="#3ee0b0" if i != 1 else "#ff8b7a")
    d.rounded_rectangle((290, 240, 860, 560), 18, fill="#0e241e", outline="#1d3f36")
    d.text((320, 260), "Cashflow  (last 6 months)", font=font(16, True), fill="#eff8f3")
    d.line((340, 500, 820, 500), fill="#2a4a40", width=2)
    d.line((360, 460, 450, 450, 540, 440, 630, 430, 720, 300, 800, 220), fill="#3ee0b0", width=3)
    d.rounded_rectangle((880, 240, 1360, 560), 18, fill="#0e241e", outline="#1d3f36")
    d.ellipse((980, 290, 1260, 520), outline="#3ee0b0", width=28)
    d.text((1060, 390), "Categories", font=font(14), fill="#cfe7de")
    d.text((290, 590), "Recent: Swiggy  -Rs 280    Uber  -Rs 164    DMart  -Rs 1,860", font=font(14), fill="#cfe7de")
    save(img, "fig_6_2_dashboard.png")

    img = Image.new("RGB", (1400, 820), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((50, 30), "Photograph a bill. Aureum writes the transaction.", font=font(24, True), fill="#eff8f3")
    d.rounded_rectangle((50, 110, 780, 760), 20, outline="#3ee0b0")
    d.text((180, 360), "Drop a photo, upload, or use the camera", font=font(18), fill="#93b0a6")
    d.rounded_rectangle((80, 680, 280, 730), 12, fill="#3ee0b0")
    center_text(d, (80, 680, 280, 730), "Choose photo", font(14, True), "#06241b")
    d.rounded_rectangle((820, 110, 1350, 760), 20, fill="#0e241e", outline="#1d3f36")
    d.text((850, 140), "Detected details", font=font(18, True), fill="#eff8f3")
    fields = ["Amount (Rs)  642.00", "Merchant  Zomato", "Category  Food", "Date  2026-10-26", "Payment  UPI"]
    for i, f in enumerate(fields):
        d.rounded_rectangle((850, 200 + i * 80, 1320, 260 + i * 80), 10, outline="#2a4a40")
        d.text((870, 218 + i * 80), f, font=font(14), fill="#cfe7de")
    d.rounded_rectangle((850, 620, 1320, 680), 12, fill="#3ee0b0")
    center_text(d, (850, 620, 1320, 680), "Add to tracker", font(15, True), "#06241b")
    save(img, "fig_6_3_scan.png")

    img = Image.new("RGB", (1400, 720), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Ledger  —  every rupee accounted for", font=font(22, True), fill="#eff8f3")
    headers = ["Date", "Details", "Category", "Method", "Amount"]
    rows = [
        ["26 Oct 2026", "Swiggy / Lunch", "Food", "UPI", "-Rs 280"],
        ["25 Oct 2026", "Uber / Commute", "Travel", "UPI", "-Rs 164"],
        ["23 Oct 2026", "DMart / Vegetables", "Groceries", "Card", "-Rs 1,860"],
        ["22 Oct 2026", "Spotify", "Entertainment", "UPI", "-Rs 199"],
        ["20 Oct 2026", "Myntra / Sale", "Shopping", "UPI", "-Rs 1,299"],
        ["01 Oct 2026", "Company payroll", "Salary", "Bank", "+Rs 45,000"],
    ]
    for i, h in enumerate(headers):
        d.text((40 + i * 260, 90), h, font=font(14, True), fill="#93b0a6")
    for r, row in enumerate(rows):
        y = 140 + r * 80
        d.rounded_rectangle((30, y, 1370, y + 64), 12, fill="#0e241e")
        for i, cell in enumerate(row):
            d.text((40 + i * 260, y + 20), cell, font=font(14), fill="#cfe7de")
    save(img, "fig_6_4_transactions.png")

    img = Image.new("RGB", (1400, 640), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Budgets for October 2026", font=font(22, True), fill="#eff8f3")
    items = [("Food", 0.45), ("Travel", 0.75), ("Shopping", 0.32)]
    for i, (n, p) in enumerate(items):
        y = 110 + i * 150
        d.text((50, y), n, font=font(18, True), fill="#eff8f3")
        d.rounded_rectangle((50, y + 50, 1320, y + 74), 10, fill="#123028")
        d.rounded_rectangle((50, y + 50, 50 + int(1270 * p), y + 74), 10, fill="#3ee0b0")
    save(img, "fig_6_5_budgets.png")

    img = Image.new("RGB", (1400, 640), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Reports  —  yearly cashflow and category mix", font=font(22, True), fill="#eff8f3")
    d.rounded_rectangle((40, 90, 760, 600), 18, fill="#0e241e")
    d.text((70, 120), "Yearly cashflow", font=font(16, True), fill="#eff8f3")
    d.line((80, 520, 720, 520), fill="#2a4a40", width=2)
    d.line((100, 480, 200, 450, 300, 400, 400, 360, 500, 280, 620, 220, 700, 180), fill="#3ee0b0", width=3)
    d.rounded_rectangle((800, 90, 1360, 600), 18, fill="#0e241e")
    d.ellipse((900, 200, 1260, 540), outline="#e8c07a", width=30)
    d.text((1000, 350), "Mix", font=font(16, True), fill="#cfe7de")
    save(img, "fig_6_6_reports.png")

    img = Image.new("RGB", (1400, 520), "#06110e")
    d = ImageDraw.Draw(img)
    d.text((40, 24), "Savings goals", font=font(22, True), fill="#eff8f3")
    d.rounded_rectangle((40, 100, 680, 460), 18, fill="#0e241e")
    d.text((70, 140), "Emergency fund", font=font(18, True), fill="#eff8f3")
    d.text((70, 180), "Rs 12,500 of Rs 50,000", font=font(14), fill="#93b0a6")
    d.rounded_rectangle((70, 240, 640, 264), 8, fill="#123028")
    d.rounded_rectangle((70, 240, 70 + int(570 * 0.25), 264), 8, fill="#3ee0b0")
    d.rounded_rectangle((720, 100, 1360, 460), 18, fill="#0e241e")
    d.text((760, 140), "New laptop", font=font(18, True), fill="#eff8f3")
    d.text((760, 180), "Rs 18,000 of Rs 65,000", font=font(14), fill="#93b0a6")
    d.rounded_rectangle((760, 240, 1320, 264), 8, fill="#123028")
    d.rounded_rectangle((760, 240, 760 + int(560 * 0.28), 264), 8, fill="#e8c07a")
    save(img, "fig_6_7_goals.png")


if __name__ == "__main__":
    architecture()
    context()
    usecase()
    sequence()
    collaboration()
    activity()
    erd()
    dfds()
    ui_plates()
    print("figures ready")
