"""Build the BCA project report PDF in the Seshadripuram College format."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
OUT_PDF = ROOT / "Smart_Personal_Expense_Tracker_Project_Report_Drup_Kumar_Paswan_U18GH24S0085.pdf"
STUDY_COPY = Path(
    r"C:\Users\Hp\OneDrive\Documents\Study material\V sem"
) / "Smart_Personal_Expense_Tracker_Project_Report_Drup_Kumar_Paswan_U18GH24S0085.pdf"

TITLE = "Smart Personal Expense Tracker and Financial Analysis System"
STUDENT = "Drup Kumar Paswan"
USN = "U18GH24S0085"
GUIDE = "Tejaswini"
GUIDE_DESIG = "Assistant Professor"
HOD = "Rajeshwari V"
PRINCIPAL = "Maj Dr. Anandappa I"
YEAR = "2026-27"
FOOTER = "Department of Computer Science, Seshadripuram College, Bengaluru-20"

NAVY = HexColor("#0d2a22")
LINE = HexColor("#1aa37c")
RULE = HexColor("#c5d5ce")
HEAD = HexColor("#123028")


def register_fonts():
    fonts = Path(r"C:\Windows\Fonts")
    mapping = {
        "Times": ["times.ttf", "Times New Roman.ttf"],
        "Times-Bold": ["timesbd.ttf", "Times New Roman Bold.ttf", "timesbd.ttf"],
        "Times-Italic": ["timesi.ttf", "Times New Roman Italic.ttf"],
        "Times-BoldItalic": ["timesbi.ttf", "Times New Roman Bold Italic.ttf"],
    }
    registered = {}
    for face, names in mapping.items():
        for n in names:
            p = fonts / n
            if p.exists():
                pdfmetrics.registerFont(TTFont(face, str(p)))
                registered[face] = True
                break
    if "Times" not in registered:
        return "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"
    return "Times", "Times-Bold", "Times-Italic", "Times-BoldItalic"


F, FB, FI, FBI = register_fonts()


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("CoverCollege", fontName=FB, fontSize=16, leading=22, alignment=TA_CENTER, textColor=NAVY, spaceAfter=6))
    s.add(ParagraphStyle("CoverSmall", fontName=F, fontSize=11, leading=16, alignment=TA_CENTER, textColor=HEAD))
    s.add(ParagraphStyle("CoverTitle", fontName=FB, fontSize=18, leading=24, alignment=TA_CENTER, textColor=NAVY, spaceBefore=10, spaceAfter=10))
    s.add(ParagraphStyle("Center", fontName=F, fontSize=12, leading=18, alignment=TA_CENTER))
    s.add(ParagraphStyle("CenterBold", fontName=FB, fontSize=12, leading=18, alignment=TA_CENTER))
    s.add(ParagraphStyle("Body", fontName=F, fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=10, firstLineIndent=18))
    s.add(ParagraphStyle("BodyNI", fontName=F, fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=10))
    s.add(ParagraphStyle("HChapter", fontName=FB, fontSize=16, leading=22, alignment=TA_CENTER, spaceBefore=8, spaceAfter=24, textColor=NAVY))
    s.add(ParagraphStyle("H1", fontName=FB, fontSize=14, leading=20, alignment=TA_LEFT, spaceBefore=16, spaceAfter=8, textColor=NAVY))
    s.add(ParagraphStyle("H2", fontName=FB, fontSize=12, leading=18, alignment=TA_LEFT, spaceBefore=12, spaceAfter=6, textColor=HEAD))
    s.add(ParagraphStyle("Caption", fontName=FI, fontSize=9, leading=12, alignment=TA_CENTER, spaceBefore=6, spaceAfter=14))
    s.add(ParagraphStyle("TableHead", fontName=FB, fontSize=9, leading=12, alignment=TA_CENTER, textColor=white))
    s.add(ParagraphStyle("TableCell", fontName=F, fontSize=9, leading=12, alignment=TA_LEFT))
    s.add(ParagraphStyle("BulletBody", fontName=F, fontSize=12, leading=18, alignment=TA_JUSTIFY, leftIndent=18, spaceAfter=4))
    s.add(ParagraphStyle("TOCEntry", fontName=F, fontSize=12, leading=20, alignment=TA_LEFT))
    s.add(ParagraphStyle("CodeBlock", fontName="Courier", fontSize=8.5, leading=11, backColor=HexColor("#f4f7f5"), leftIndent=6, rightIndent=6, spaceBefore=6, spaceAfter=10))
    s.add(ParagraphStyle("FooterS", fontName=F, fontSize=8, leading=10, alignment=TA_CENTER, textColor=HEAD))
    s.add(ParagraphStyle("HeaderL", fontName=FI, fontSize=9, leading=11, alignment=TA_LEFT, textColor=HEAD))
    s.add(ParagraphStyle("HeaderR", fontName=F, fontSize=9, leading=11, alignment=TA_RIGHT, textColor=HEAD))
    s.add(ParagraphStyle("Sign", fontName=F, fontSize=11, leading=16, alignment=TA_LEFT))
    return s


S = styles()
toc_collector: list[tuple[str, int]] = []


def heading_tracker(text, style_name="H1"):
    class Marked(Paragraph):
        def draw(self):
            super().draw()
            toc_collector.append((text, self.canv.getPageNumber()))

    return Marked(text, S[style_name])


def P(text, style="Body"):
    return Paragraph(text, S[style])


def bullets(items):
    flow = []
    for it in items:
        flow.append(Paragraph(f"•  {it}", S["BulletBody"]))
    return flow


def fig(name, caption, width=6.3 * inch):
    path = FIG / name
    if not path.exists():
        return [P(f"[Figure missing: {name}]", "BodyNI")]
    im = Image(str(path), width=width, height=width * 0.52)
    im.hAlign = "CENTER"
    # keep aspect for tall activity diagram
    from PIL import Image as PILImage

    with PILImage.open(path) as raw:
        w, h = raw.size
    height = width * (h / w)
    if height > 7.2 * inch:
        height = 7.2 * inch
        width = height * (w / h)
    im = Image(str(path), width=width, height=height)
    im.hAlign = "CENTER"
    return [KeepTogether([im, Paragraph(caption, S["Caption"])])]


def table(headers, rows, col_widths=None):
    head = [Paragraph(h, S["TableHead"]) for h in headers]
    data = [head]
    for row in rows:
        data.append([Paragraph(str(c), S["TableCell"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), white),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#eef6f2")]),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    if page >= 1:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.8)
        canvas.line(1.25 * inch, A4[1] - 0.62 * inch, A4[0] - 1.00 * inch, A4[1] - 0.62 * inch)
        canvas.setFont(FI, 9)
        canvas.setFillColor(HEAD)
        canvas.drawString(1.25 * inch, A4[1] - 0.55 * inch, TITLE[:62])
        canvas.setFont(F, 9)
        canvas.drawRightString(A4[0] - 1.00 * inch, A4[1] - 0.55 * inch, str(page))
        canvas.line(1.25 * inch, 0.70 * inch, A4[0] - 1.00 * inch, 0.70 * inch)
        canvas.setFont(F, 8)
        canvas.drawCentredString(A4[0] / 2, 0.48 * inch, FOOTER)
    canvas.restoreState()


def cover_only(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 18, A4[0], 18, fill=1, stroke=0)
    canvas.rect(0, 0, A4[0], 18, fill=1, stroke=0)
    canvas.restoreState()
    header_footer(canvas, doc)


def story():
    w = 6.25 * inch
    st = []

    # INNER TITLE
    st += [
        Spacer(1, 0.3 * inch),
        P("SESHADRIPURAM COLLEGE", "CoverCollege"),
        P("27, Nagappa Street, Seshadripuram, Bengaluru–560 020", "CoverSmall"),
        P("Affiliated to Dr. Manmohan Singh Bengaluru City University", "CoverSmall"),
        P("ISO 9001:2015 Certified | Recognized Under Section 2(f) and 12(B)", "CoverSmall"),
        P("AICTE Approved | NAAC Grade: A++ | Academic Year 2026–27", "CoverSmall"),
        P("Website: www.spmcollege.ac.in", "CoverSmall"),
        Spacer(1, 0.25 * inch),
        P(TITLE.upper(), "CoverTitle"),
        P("A project report submitted in partial fulfillment of the requirements<br/>for the award of the degree of", "Center"),
        Spacer(1, 8),
        P("BACHELOR OF COMPUTER APPLICATIONS", "CoverCollege"),
        P("of", "Center"),
        P("Dr. Manmohan Singh Bengaluru City University", "CenterBold"),
        Spacer(1, 18),
        P("By", "Center"),
        Spacer(1, 8),
        P(f"<b>Student Name:</b> {STUDENT}", "Center"),
        P(f"<b>USN:</b> {USN}", "Center"),
        Spacer(1, 16),
        P("Under the Guidance of", "Center"),
        P(f"<b>Internal Guide:</b> {GUIDE}", "CenterBold"),
        P(GUIDE_DESIG, "Center"),
        Spacer(1, 28),
        P("Department of Computer Science", "CenterBold"),
        P("Seshadripuram College, Bengaluru–20", "Center"),
        P(YEAR, "CenterBold"),
        PageBreak(),
    ]

    # CERTIFICATE
    st += [
        P("SESHADRIPURAM COLLEGE", "CoverCollege"),
        P("27, Nagappa Street, Seshadripuram, Bengaluru–560 020", "CoverSmall"),
        P("Affiliated to Dr. Manmohan Singh Bengaluru City University | ISO 9001:2015 Certified", "CoverSmall"),
        P("AICTE Approved | NAAC Grade: A++ | Recognized Under Section 2(f) and 12(B)", "CoverSmall"),
        Spacer(1, 20),
        P("CERTIFICATE", "HChapter"),
        P(
            f"This is to certify that <b>{STUDENT}</b>, bearing USN <b>{USN}</b>, has completed the project work entitled "
            f"“{TITLE}” as a partial fulfillment for the award of the Bachelor of Computer Applications degree "
            f"during the academic year {YEAR} under the supervision of the internal guide, <b>{GUIDE}</b>.",
            "BodyNI",
        ),
        Spacer(1, 0.7 * inch),
        table(
            ["Signature of Internal Guide", "Signature of HOD"],
            [[GUIDE, HOD], [GUIDE_DESIG, "Head of the Department"]],
            [3.1 * inch, 3.1 * inch],
        ),
        Spacer(1, 0.5 * inch),
        P("External Examiner: ____________________________", "Sign"),
        P("Internal Examiner: ____________________________", "Sign"),
        PageBreak(),
    ]

    # DECLARATION
    st += [
        P("DECLARATION", "HChapter"),
        P(
            f"I, <b>{STUDENT}</b>, student of the Bachelor of Computer Applications programme at Seshadripuram College, "
            f"bearing USN <b>{USN}</b>, hereby declare that the project entitled “{TITLE}” has been carried out by me "
            f"under the supervision of the internal guide, <b>{GUIDE}</b>, {GUIDE_DESIG}, and submitted in partial fulfillment "
            f"of the requirements for the award of the Degree of Bachelor of Computer Applications by Dr. Manmohan Singh "
            f"Bengaluru City University during the academic year {YEAR}. This report has not been submitted to any other "
            "organisation or university for the award of any degree or certificate.",
            "BodyNI",
        ),
        Spacer(1, 0.8 * inch),
        P(f"Name: {STUDENT}", "Sign"),
        P(f"USN: {USN}", "Sign"),
        P("Signature: ____________________________", "Sign"),
        P("Place: Bengaluru", "Sign"),
        P("Date: ____________________", "Sign"),
        PageBreak(),
    ]

    # ACKNOWLEDGEMENT
    st += [
        P("ACKNOWLEDGEMENT", "HChapter"),
        P(
            "I take this opportunity to express my sincere gratitude to God for providing me with the strength, wisdom and "
            "perseverance required to complete this project and report.",
            "BodyNI",
        ),
        P(
            "I sincerely thank my parents for their constant support, encouragement and belief in me throughout the project. "
            "Their guidance has been a steady foundation for this academic work.",
            "BodyNI",
        ),
        P(
            f"I am thankful to {PRINCIPAL}, Principal, Seshadripuram College, for providing the academic environment and "
            "encouragement needed to undertake this work.",
            "BodyNI",
        ),
        P(
            f"I extend my heartfelt thanks to Prof. {HOD}, Head of the Department of Computer Science, for support, "
            "motivation and academic guidance.",
            "BodyNI",
        ),
        P(
            f"I express my deep appreciation to my internal guide, {GUIDE}, {GUIDE_DESIG}, for continuous feedback, "
            "technical suggestions and encouragement that helped shape the Smart Personal Expense Tracker and this report.",
            "BodyNI",
        ),
        P(
            "Finally, I thank all faculty members of the Department of Computer Science and my peers for their cooperation "
            "and valuable suggestions during the development and documentation of this project.",
            "BodyNI",
        ),
        Spacer(1, 24),
        P(STUDENT, "CenterBold"),
        P(f"({USN})", "Center"),
        PageBreak(),
    ]

    # ABSTRACT
    st += [
        P("ABSTRACT", "HChapter"),
        P(
            "Managing personal money is difficult when daily spending is scattered across cash, UPI applications, cards and "
            "online orders. Students and working professionals often postpone writing expenses in a notebook or spreadsheet, "
            "so monthly budgets become guesses rather than measurements. The Smart Personal Expense Tracker and Financial "
            "Analysis System, implemented as the web application Aureum, offers a single ledger in which a user can record "
            "income and expenses, classify them, watch budgets, and study spending with charts.",
            "BodyNI",
        ),
        P(
            "The system is a Flask web application with HTML5, CSS3, JavaScript, Bootstrap 5 and Chart.js on the client and "
            "a relational store accessed through SQLAlchemy. SQLite is the default database so the prototype runs without a "
            "server; MySQL can be connected through an environment variable as specified in the synopsis. Sessions protect "
            "each user’s records. Passwords are stored only as hashes.",
            "BodyNI",
        ),
        P(
            "A distinctive module reads a photograph of a paper bill or an online payment screenshot. Tesseract.js performs "
            "optical character recognition in the browser. A Python parser then extracts amount, date, merchant, likely "
            "category and payment method. The user confirms the fields before the row is written, so automation never silently "
            "invents a transaction. Additional modules cover savings goals, CSV export, demo data and spending insights.",
            "BodyNI",
        ),
        P(
            "This report presents the problem, related work, feasibility, software requirements, architecture, detailed design, "
            "implementation, testing, conclusion and future work. The project shows how database design, web engineering and "
            "lightweight document analysis can support everyday financial discipline without bank-account integration.",
            "BodyNI",
        ),
        PageBreak(),
    ]

    # TOC (static structure; page numbers filled visually by header during reading)
    st += [
        P("TABLE OF CONTENTS", "HChapter"),
        P("Certificate", "TOCEntry"),
        P("Declaration", "TOCEntry"),
        P("Acknowledgement", "TOCEntry"),
        P("Abstract", "TOCEntry"),
        P("List of Figures and Tables", "TOCEntry"),
        P("CHAPTER 01  INTRODUCTION", "TOCEntry"),
        P("    1.1  Applications", "TOCEntry"),
        P("    1.2  About the Project", "TOCEntry"),
        P("    1.3  Objectives", "TOCEntry"),
        P("    1.4  Scope", "TOCEntry"),
        P("    1.5  Methodology", "TOCEntry"),
        P("CHAPTER 02  LITERATURE SURVEY", "TOCEntry"),
        P("    2.1  Existing and Proposed System", "TOCEntry"),
        P("    2.2  Feasibility Study", "TOCEntry"),
        P("    2.3  Tools and Technologies Used", "TOCEntry"),
        P("    2.4  Hardware and Software Requirements", "TOCEntry"),
        P("CHAPTER 03  SOFTWARE REQUIREMENTS SPECIFICATION", "TOCEntry"),
        P("    3.1  Users", "TOCEntry"),
        P("    3.2  Functional Requirements", "TOCEntry"),
        P("    3.3  Non-Functional Requirements", "TOCEntry"),
        P("    3.4  Input and Output Specification", "TOCEntry"),
        P("    3.5  Assumptions and Dependencies", "TOCEntry"),
        P("CHAPTER 04  SYSTEM DESIGN", "TOCEntry"),
        P("    4.1  System Perspective", "TOCEntry"),
        P("    4.2  Context Diagram", "TOCEntry"),
        P("    4.3  Data Flow Diagram", "TOCEntry"),
        P("CHAPTER 05  DETAILED DESIGN", "TOCEntry"),
        P("    5.1  Use Case Diagram", "TOCEntry"),
        P("    5.2  Sequence Diagram", "TOCEntry"),
        P("    5.3  Collaboration Diagram", "TOCEntry"),
        P("    5.4  Activity Diagram", "TOCEntry"),
        P("    5.5  Database Design", "TOCEntry"),
        P("CHAPTER 06  IMPLEMENTATION", "TOCEntry"),
        P("    6.1  Module Description", "TOCEntry"),
        P("    6.2  Screen Shots and Demonstration", "TOCEntry"),
        P("    6.3  Coding and Processing Logic", "TOCEntry"),
        P("    6.4  Route and Processing Catalogue", "TOCEntry"),
        P("    6.5  User Interface Implementation", "TOCEntry"),
        P("CHAPTER 07  SOFTWARE TESTING", "TOCEntry"),
        P("CHAPTER 08  CONCLUSION", "TOCEntry"),
        P("CHAPTER 09  FUTURE ENHANCEMENTS", "TOCEntry"),
        P("REFERENCES", "TOCEntry"),
        P("APPENDIX A  User Manual", "TOCEntry"),
        P("APPENDIX B  Data Dictionary", "TOCEntry"),
        P("APPENDIX C  Sample Receipt Parsing", "TOCEntry"),
        P("APPENDIX D  Website Screen Guide and Operational Evaluation", "TOCEntry"),
        P("APPENDIX E  Project Organisation and Source Map", "TOCEntry"),
        PageBreak(),
        P("LIST OF FIGURES AND TABLES", "HChapter"),
        P("Figure 4.1  Layered architecture of Aureum", "TOCEntry"),
        P("Figure 4.2  Context-level data flow", "TOCEntry"),
        P("Figure 4.3  Level-1 data flow of the tracking process", "TOCEntry"),
        P("Figure 5.1  Use-case view", "TOCEntry"),
        P("Figure 5.2  Sequence: scan bill and save transaction", "TOCEntry"),
        P("Figure 5.3  Collaboration among objects", "TOCEntry"),
        P("Figure 5.4  Activity: monthly expense tracking", "TOCEntry"),
        P("Figure 5.5  Entity-relationship view", "TOCEntry"),
        P("Figure 6.1  Sign-in and demonstration access", "TOCEntry"),
        P("Figure 6.2  Dashboard with cashflow and category charts", "TOCEntry"),
        P("Figure 6.3  Scan-a-bill workspace", "TOCEntry"),
        P("Figure 6.4  Transaction ledger", "TOCEntry"),
        P("Figure 6.5  Category budgets", "TOCEntry"),
        P("Figure 6.6  Reports workspace", "TOCEntry"),
        P("Figure 6.7  Savings goals", "TOCEntry"),
        P("Table 2.1  Feasibility summary", "TOCEntry"),
        P("Table 2.2  Hardware and software requirements", "TOCEntry"),
        P("Table 3.1  Functional requirements", "TOCEntry"),
        P("Table 5.1  Use-case catalogue", "TOCEntry"),
        P("Table 5.2  Data dictionary of principal tables", "TOCEntry"),
        P("Table 6.1  Application modules", "TOCEntry"),
        P("Table 7.1  Test cases", "TOCEntry"),
        PageBreak(),
    ]

    # CHAPTER 01
    st += [
        P("CHAPTER 01", "HChapter"),
        P("INTRODUCTION", "HChapter"),
        P("1.1  Applications", "H1"),
        P(
            "Personal finance applications appear in many everyday settings. The present project concentrates on a student or "
            "young professional who already uses UPI, cards and cash, but does not keep a reliable monthly picture of money.",
            "BodyNI",
        ),
        P("<b>1. Daily expense recording.</b> The ledger accepts income and expense rows with amount, category, merchant, payment method, date and an optional note. This replaces a paper diary that is easy to abandon.", "BodyNI"),
        P("<b>2. Bill and screenshot capture.</b> A user photographs a restaurant bill or a PhonePe, Google Pay or Paytm success screen. Optical character recognition and a rule-based parser propose the transaction so the user need not type every rupee.", "BodyNI"),
        P("<b>3. Budget monitoring.</b> Category ceilings for the current month show how much of Food, Travel or Shopping has already been used. Colour bars warn when a limit is nearly exhausted.", "BodyNI"),
        P("<b>4. Financial analysis.</b> The dashboard and reports module summarise income, expense, net balance and savings rate, and draw Chart.js graphs for six-month cashflow and category mix.", "BodyNI"),
        P("<b>5. Goal-oriented saving.</b> Named goals such as an emergency fund or a laptop receive deposits toward a target amount and optional deadline.", "BodyNI"),
        P("<b>6. Academic demonstration.</b> A one-click demo workspace loads sample Indian transactions so a viva examiner can explore charts without creating an account first.", "BodyNI"),
        P("1.2  About the Project", "H1"),
        P(
            "The problem statement of the approved synopsis remains the starting point of this work. Managing personal finances "
            "has become more fragmented in a digital economy. Many students and working professionals fail to record daily "
            "expenses. Handwritten notes and simple spreadsheets are slow and often incomplete. When records are missing, "
            "budgets cannot be checked and spending patterns stay invisible [1].",
            "BodyNI",
        ),
        P(
            "Aureum is the implemented name of the Smart Personal Expense Tracker and Financial Analysis System. It is a "
            "browser-based application. After registration, a user sees a dark, high-contrast workspace with navigation for "
            "Dashboard, Transactions, Scan a bill, Budgets, Reports, Goals and Profile. Each user sees only his or her own "
            "rows. The design deliberately excludes bank login and payment processing, matching the synopsis limit that the "
            "project is a personal finance information system rather than a fintech payment product.",
            "BodyNI",
        ),
        P(
            "The software follows the classical Software Development Life Cycle used in the synopsis: requirement analysis, "
            "system design, development, database implementation, testing and documentation [2]. The implementation language "
            "is Python 3 with the Flask micro-framework. Presentation uses HTML templates, custom CSS and Bootstrap 5. "
            "Charts use Chart.js. Receipt reading uses Tesseract.js in the browser and a Python regular-expression parser "
            "on the server. Persistence uses SQLAlchemy with SQLite by default and optional MySQL.",
            "BodyNI",
        ),
        P(
            "Compared with a blank spreadsheet, the application adds authentication, referential categories, budget arithmetic, "
            "visual analysis and a scan path. Compared with a commercial mobile wallet statement, it remains under the user’s "
            "control on a local machine and can combine cash, UPI and card in one ledger. The product language of the interface "
            "is English with amounts displayed in Indian rupees.",
            "BodyNI",
        ),
        P(
            "The rest of this report is organised as follows. Chapter 2 reviews related literature, existing practice and "
            "feasibility. Chapter 3 states software requirements. Chapter 4 describes architecture and context. Chapter 5 "
            "gives detailed UML-style design and the database schema. Chapter 6 explains modules, screens and processing "
            "logic. Chapter 7 records test cases. Chapters 8 and 9 conclude and list future work.",
            "BodyNI",
        ),
        P("1.3  Objectives", "H1"),
        P("The primary objective is to develop a web-based personal expense tracker that helps users manage financial transactions and maintain financial discipline. The specific objectives, aligned with the synopsis and extended by the scan feature, are as follows.", "BodyNI"),
    ]
    st += bullets(
        [
            "To provide a secure user registration and login system with hashed passwords and session control.",
            "To allow users to record income and expense transactions with merchant, note, date and payment method.",
            "To categorise expenses into groups such as food, travel, shopping, education, entertainment, bills, health, rent and groceries.",
            "To maintain a complete transaction history with search and date filters.",
            "To generate monthly and yearly financial reports and export them as CSV.",
            "To provide graphical analysis of spending patterns using Chart.js.",
            "To enable users to set category budgets and monitor spending limits.",
            "To help users improve planning through savings goals and dashboard insights.",
            "To provide an easy-to-use responsive user interface.",
            "To store financial data in a relational database with optional MySQL deployment.",
            "To capture a bill or UPI screenshot and propose a transaction automatically for user confirmation.",
        ]
    )
    st += [
        P("1.4  Scope", "H1"),
        P(
            "The system is intended for students, employees, freelancers and other individuals who wish to manage personal "
            "money. The implemented scope covers user registration and authentication, recording of income and expenses, "
            "categorisation, editing and deletion, monthly and yearly summaries, budget management, graphical reports, "
            "search and filtering, profile management, report export, savings goals, a demonstration account and receipt "
            "or UPI-screenshot scanning.",
            "BodyNI",
        ),
        P(
            "The project does not include direct banking integration, UPI collection, investment portfolios, GST accounting "
            "for businesses, multi-user household sharing, or automatic payment of bills. Future versions may add spending "
            "prediction, a native mobile application and bank-statement import, as noted in the synopsis. Within the present "
            "academic boundary the software is a complete, runnable web prototype suitable for laboratory demonstration and viva.",
            "BodyNI",
        ),
        P("1.5  Methodology", "H1"),
        P(
            "The project follows the Software Development Life Cycle described in the approved synopsis. The intention is not "
            "ceremonial paperwork; each phase left an artefact that later chapters still use. Requirement analysis produced the "
            "functional list in Chapter 3. Design produced the layered architecture, data-flow and entity-relationship views. "
            "Implementation produced the Flask package. Testing produced Table 7.1. Documentation produced this report.",
            "BodyNI",
        ),
        P(
            "Requirement analysis began with the problem of forgotten daily expenses. Informal conversations with classmates "
            "confirmed that UPI screenshots already exist on phones but are rarely copied into a ledger. That observation "
            "justified the scan module as an extension of the synopsis rather than a replacement of manual entry. Use cases "
            "were written so that every screen maps to at least one requirement identifier.",
            "BodyNI",
        ),
        P(
            "System design treated the browser as a thin client. Jinja templates render server-computed totals; JavaScript is "
            "used for charts, flash dismissal and OCR, not for storing the ledger. This choice simplifies viva explanation: "
            "the database remains the single source of truth. The schema was normalised far enough to avoid duplicate category "
            "spellings, but not so far that a merchant dimension table would slow a student demonstration.",
            "BodyNI",
        ),
        P(
            "Development proceeded module by module: first authentication and empty dashboard, then transactions, then charts, "
            "then budgets, then reports, then goals, then scan. Each module was reachable from the sidebar before the next "
            "module began, so integration defects appeared early. Category colours were chosen once in DEFAULT_CATEGORIES and "
            "reused in pills, doughnut segments and budget bars to keep the visual language consistent.",
            "BodyNI",
        ),
        P(
            "Database implementation uses SQLAlchemy create_all at start-up. SQLite files live under the Flask instance folder. "
            "MySQL remains a documented option because the synopsis named it. Switching engines does not change templates. "
            "Seed data for categories runs only when the table is empty, so a second boot does not duplicate Food or Salary.",
            "BodyNI",
        ),
        P(
            "Testing combined parser unit checks with browser walks of the demo account. Defects such as db.or_ (invalid on the "
            "SQLAlchemy object) and a broken dashboard greeting expression were corrected during implementation. Maintenance "
            "after viva would include dependency updates, backup of instance/expense.db and optional HTTPS deployment.",
            "BodyNI",
        ),
        P(
            "The methodology therefore matches both the college sample contents (application-oriented project) and the friend’s "
            "report structure of introduction, literature, SRS, design, detailed design, implementation, testing, conclusion "
            "and future work, with appendices for the user manual and operational notes.",
            "BodyNI",
        ),
        PageBreak(),
    ]

    # CHAPTER 02
    st += [
        P("CHAPTER 02", "HChapter"),
        P("LITERATURE SURVEY", "HChapter"),
        P(
            "This chapter places the tracker in the context of personal-finance software, web engineering, databases, "
            "visualisation and optical character recognition. Citations use the decimal form required by the college format [1].",
            "BodyNI",
        ),
        P("[1]. Personal Financial Management", "H2"),
        P("Author: Lusardi and Mitchell. Source: Journal of Economic Literature. Summary: This body of work showed that financial literacy and simple recording habits improve household decisions. The project applies that idea by making recording faster than a notebook.", "BodyNI"),
        P("[2]. Software Engineering Practice", "H2"),
        P("Author: Pressman and Maxim. Source: Software Engineering: A Practitioner’s Approach. Summary: The reference describes requirements, design, implementation, testing and maintenance as connected activities. The present report follows that sequence.", "BodyNI"),
        P("[3]. Database System Concepts", "H2"),
        P("Author: Silberschatz, Korth and Sudarshan. Source: Database System Concepts. Summary: The book explains keys, foreign keys, normalisation and transactions, which guided the USER, TRANSACTION, CATEGORY, BUDGET and GOAL schema.", "BodyNI"),
        P("[4]. Web Application Frameworks", "H2"),
        P("Author: Grinberg. Source: Flask Web Development. Summary: Flask is presented as a lightweight WSGI framework with routing, Jinja templates and extensions such as Flask-SQLAlchemy. This matches the implemented stack.", "BodyNI"),
        P("[5]. Information Dashboard Design", "H2"),
        P("Author: Stephen Few. Source: Information Dashboard Design. Summary: Dashboards should show a small set of comparable measures. Aureum therefore leads with income, spent, remaining balance and savings rate before charts.", "BodyNI"),
        P("[6]. Human–Computer Interaction", "H2"),
        P("Author: Dix et al. Source: Human–Computer Interaction. Summary: Usability, feedback and consistency informed the scan confirmation step: the system proposes values but the user commits the row.", "BodyNI"),
        P("[7]. Optical Character Recognition", "H2"),
        P("Author: Smith. Source: Tesseract OCR Engine documentation and related papers. Summary: OCR converts an image of print into text. Tesseract.js brings that engine to the browser, which avoids installing a native binary on every student laptop.", "BodyNI"),
        P("[8]. Information Retrieval Patterns", "H2"),
        P("Author: Manning, Raghavan and Schütze. Source: Introduction to Information Retrieval. Summary: Regular expressions and token clues are a practical first stage of extraction. The receipt parser uses amount, date and merchant patterns before category keywords.", "BodyNI"),
        P("[9]. Web Application Security", "H2"),
        P("Author: OWASP Foundation. Source: OWASP Application Security Verification Standard. Summary: Authentication, session control, password hashing and access checks are mandatory. Each query in Aureum is scoped by the session user identifier.", "BodyNI"),
        P("[10]. Software Testing", "H2"),
        P("Author: Myers et al. Source: The Art of Software Testing. Summary: Functional, boundary, negative and usability tests structure Chapter 7.", "BodyNI"),
        P("[11]. Responsive Web Design", "H2"),
        P("Author: Marcotte. Source: Responsive Web Design. Summary: Layouts should adapt to narrow screens. Aureum hides the sidebar on small widths and offers a bottom tab bar.", "BodyNI"),
        P("[12]. Charting for the Web", "H2"),
        P("Author: Chart.js documentation. Summary: Canvas-based charts are sufficient for category doughnuts and cashflow lines without a heavy visualisation server.", "BodyNI"),
        P("2.1  Existing and Proposed System", "H1"),
        P(
            "In the existing informal process a person either remembers expenses, writes them on paper, or dumps SMS and UPI "
            "notifications into a folder. Spreadsheet templates exist, but they demand discipline: every purchase must be typed, "
            "formulas break, and there is no login barrier if a shared computer is used. Mobile wallets show merchant-wise "
            "history for that wallet only; cash and another bank’s card remain outside. Commercial expense apps may require "
            "cloud accounts and sometimes request bank linkage, which is outside the permitted scope of this academic project.",
            "BodyNI",
        ),
        P(
            "The proposed system keeps a private web ledger. Manual entry remains available for cash. The scan module reduces "
            "the cost of capturing printed bills and UPI screenshots. Categories, budgets, goals and charts convert raw rows "
            "into a monthly story. Because confirmation is required after OCR, the system does not pretend to be a bank feed. "
            "It is a disciplined notebook with structure, pictures and analysis.",
            "BodyNI",
        ),
        P("2.2  Feasibility Study", "H1"),
        P("<b>Technical feasibility.</b> Python, Flask, a relational database and a modern browser are standard laboratory tools. OCR in the browser is technically feasible for high-contrast screenshots; poor photographs may need manual correction, which the form already allows. Chart.js and Bootstrap are loaded from public CDNs during demonstration.", "BodyNI"),
        P("<b>Economic feasibility.</b> The prototype uses free and open-source libraries. No paid API key is required for core tracking. Hosting, if needed, can remain on localhost for viva. Production OCR of very large volumes would remain cheap because recognition happens on the client.", "BodyNI"),
        P("<b>Operational feasibility.</b> The main path is short: sign in, add or scan, review dashboard. A demo account removes first-use friction for examiners. Indian rupee formatting and UPI vocabulary match the intended users.", "BodyNI"),
        P("<b>Schedule feasibility.</b> Work divided into authentication, ledger, budgets, charts, scan and documentation fits a semester project calendar.", "BodyNI"),
        P("<b>Legal and ethical feasibility.</b> The application stores personal money records. It must not leak one user to another. Receipt images stay in a local upload folder. The project does not connect to a bank, so it does not process card PAN data or UPI PINs. Users should avoid photographing passwords or QR secrets.", "BodyNI"),
        Spacer(1, 8),
        table(
            ["Feasibility area", "Observation", "Assessment"],
            [
                ["Technical", "Flask, SQLAlchemy, Chart.js and Tesseract.js are proven student-scale tools.", "Feasible"],
                ["Operational", "Sign-in, ledger, scan-confirm, dashboard is a short workflow.", "Feasible"],
                ["Economic", "Open-source stack; SQLite needs no server licence.", "Feasible as academic project"],
                ["Schedule", "Modules map cleanly to weekly implementation.", "Feasible"],
                ["Legal / ethical", "Session isolation and hashed passwords; no bank API.", "Feasible with care"],
            ],
            [1.4 * inch, 3.1 * inch, 1.7 * inch],
        ),
        P("Table 2.1  Feasibility summary", "Caption"),
        P("2.3  Tools and Technologies Used", "H1"),
        P("The synopsis specified HTML5, CSS3, JavaScript, Bootstrap, Python, Flask, MySQL and Chart.js, with Visual Studio Code and Git. The implementation honours that list and adds SQLAlchemy, Werkzeug password hashing, Tesseract.js for OCR, and SQLite as a zero-configuration default that can be switched to MySQL.", "BodyNI"),
    ]
    st += bullets(
        [
            "Frontend: HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js 4, Tesseract.js 5.",
            "Backend: Python 3.10+, Flask 3, Flask-SQLAlchemy, Werkzeug, python-dotenv, Pillow.",
            "Database: SQLite (default) or MySQL through PyMySQL and a DATABASE_URL.",
            "Tools: Visual Studio Code / Cursor, Git, Chrome or Edge for testing.",
        ]
    )
    st += [
        P("2.4  Hardware and Software Requirements", "H1"),
        table(
            ["Category", "Minimum", "Recommended"],
            [
                ["Processor", "Intel Core i3 or equivalent", "Intel Core i5 or higher"],
                ["RAM", "4 GB", "8 GB or higher"],
                ["Storage", "20 GB free", "50 GB free"],
                ["Display", "1366 × 768", "1920 × 1080"],
                ["Input", "Keyboard and mouse; camera optional", "Keyboard, mouse and webcam or phone camera"],
                ["Internet", "Needed for CDN scripts during demo", "Stable broadband"],
                ["Operating system", "Windows 10/11, Linux or macOS", "Windows 11"],
                ["Browser", "Chrome, Edge or Firefox", "Current Chrome"],
                ["Python", "3.10+", "3.12 or 3.14 as used in development"],
                ["Database", "SQLite bundled", "MySQL Server 8 if chosen"],
            ],
            [1.6 * inch, 2.3 * inch, 2.3 * inch],
        ),
        P("Table 2.2  Hardware and software requirements", "Caption"),
        PageBreak(),
    ]

    # CHAPTER 03
    st += [
        P("CHAPTER 03", "HChapter"),
        P("SOFTWARE REQUIREMENTS SPECIFICATION", "HChapter"),
        P("3.1  Users", "H1"),
        P("The running system has a single authenticated role: the personal user. An unauthenticated visitor may only register, sign in or open the demonstration workspace. The demonstration persona is a sample user named Aarav Sharma with seeded Indian transactions; it is not a separate security role.", "BodyNI"),
        table(
            ["User", "Responsibilities"],
            [
                ["Guest", "Register, sign in, or load the demo workspace."],
                ["Registered user", "Maintain profile, record income and expenses, scan bills, set budgets and goals, view charts, export CSV, sign out."],
                ["Demo user", "Explore seeded data during viva without creating a private account."],
                ["System", "Authenticate, isolate rows by user id, parse receipts, aggregate totals, render charts."],
            ],
            [1.8 * inch, 4.4 * inch],
        ),
        P("3.2  Functional Requirements", "H1"),
        table(
            ["ID", "Requirement"],
            [
                ["FR-01", "The system shall allow a user to register with name, email and password of at least six characters."],
                ["FR-02", "The system shall authenticate a registered user and create a server session."],
                ["FR-03", "The system shall reject invalid credentials with a clear message."],
                ["FR-04", "The system shall allow recording of income and expense with amount, category, date, merchant, note and payment method."],
                ["FR-05", "The system shall support edit and delete of the owner’s transactions only."],
                ["FR-06", "The system shall filter the ledger by type, category, date range and free-text search."],
                ["FR-07", "The system shall display monthly income, expense, remaining balance and savings rate on a dashboard."],
                ["FR-08", "The system shall draw a six-month cashflow line chart and a category doughnut chart."],
                ["FR-09", "The system shall allow monthly category budgets and show percentage used."],
                ["FR-10", "The system shall provide monthly and yearly report views and CSV export."],
                ["FR-11", "The system shall allow savings goals with target, saved amount and optional deadline."],
                ["FR-12", "The system shall let a user upload or capture a receipt image."],
                ["FR-13", "The system shall run OCR and parse amount, date, merchant, category and payment method."],
                ["FR-14", "The system shall require explicit confirmation before inserting a scanned transaction."],
                ["FR-15", "The system shall restrict all financial records to the session user."],
                ["FR-16", "The system shall allow profile updates for name, phone, typical income and password."],
                ["FR-17", "The system shall offer a demonstration workspace with sample data."],
            ],
            [0.9 * inch, 5.3 * inch],
        ),
        P("Table 3.1  Functional requirements", "Caption"),
        P("3.3  Non-Functional Requirements", "H1"),
    ]
    st += bullets(
        [
            "Usability: a new user should record a cash expense in under one minute and understand the scan confirmation form without training.",
            "Performance: ordinary ledger pages should render on localhost in well under one second for a few hundred rows.",
            "Reliability: invalid amounts must be rejected; OCR failures must fall back to manual fields rather than storing zero silently as success.",
            "Security: passwords hashed with Werkzeug; session cookie required; no cross-user reads.",
            "Maintainability: models, parser and routes live in separate modules.",
            "Portability: Windows, Linux or macOS with Python 3.10+.",
            "Scalability: SQLAlchemy allows SQLite for demo and MySQL for a shared deployment.",
            "Accessibility: labels on forms, keyboard-focusable buttons, contrast suitable for a dark theme.",
            "Explainability: dashboard insights are computed from visible totals, not a hidden model.",
        ]
    )
    st += [
        P("3.4  Input and Output Specification", "H1"),
        P("Inputs are of four kinds. Identity inputs are name, email, password, phone and stated monthly income. Ledger inputs are kind, amount, category identifier, ISO date, payment method, merchant and note. Planning inputs are budget ceilings and goal targets. Document inputs are receipt images and the OCR text derived from them. Every money input is validated for a positive amount before persistence.", "BodyNI"),
        P("Outputs are of five kinds. Screen outputs are KPI cards, tables, budget bars, insight sentences and flash messages. Chart outputs are JSON arrays consumed by Chart.js. File outputs are CSV ledgers and stored receipt images. Session outputs are the signed-in user identifier. Parser outputs are JSON documents with amount, date, merchant, category_id and payment_method. No output is a payment instruction to a bank.", "BodyNI"),
        P("Error outputs are user-visible sentences rather than stack traces, except when Flask debug mode is enabled on a laboratory machine. Production deployment should disable debug. Empty charts render a single placeholder slice so the canvas is not blank. CSV uses a byte-order mark for Excel. Amounts in the interface use an Indian rupee prefix and thousands separators.", "BodyNI"),
        P("3.5  Assumptions and Dependencies", "H1"),
        P("The prototype assumes a single personal user per account, not a chartered-accountant practice. It assumes the browser can run JavaScript. It assumes CDN access during demonstration unless the scripts are vendored. It assumes receipt text is mostly English or Latin digits, which is true of common UPI screenshots. It depends on Flask, SQLAlchemy, Werkzeug and a SQLite library shipped with Python. Optional MySQL depends on a running server and correct DATABASE_URL. Camera capture depends on user permission.", "BodyNI"),
        PageBreak(),
    ]

    # CHAPTER 04
    st += [
        P("CHAPTER 04", "HChapter"),
        P("SYSTEM DESIGN", "HChapter"),
        P("4.1  System Perspective", "H1"),
        P(
            "Aureum is a layered web system. The presentation layer is a set of Jinja2 templates and static CSS/JavaScript. "
            "The application layer is a Flask application exposing HTTP routes for authentication, CRUD of transactions, "
            "budgets, goals, reports, scan upload and scan parse. The persistence layer is SQLAlchemy over SQLite or MySQL. "
            "A client-side OCR worker is an additional presentation service that never bypasses the application layer when "
            "saving money data.",
            "BodyNI",
        ),
        P(
            "Figure 4.1 summarises the layers. Requests travel downward from the browser. Aggregates for charts are computed "
            "in Python using SQL filters on the current user and the selected month or year. Uploaded images are stored under "
            "static/uploads/receipts with generated file names.",
            "BodyNI",
        ),
    ]
    st += fig("fig_4_1_architecture.png", "Figure 4.1  Layered architecture of Aureum")
    st += [
        P("4.2  Context Diagram", "H1"),
        P(
            "At context level the registered user and, optionally, a camera or image file interact with a single system. "
            "Outputs are on-screen charts, budget bars, CSV files and persisted database rows. There is no external bank actor.",
            "BodyNI",
        ),
    ]
    st += fig("fig_4_2_context.png", "Figure 4.2  Context-level data flow")
    st += [
        P("4.3  Data Flow Diagram", "H1"),
        P(
            "Level-1 processes are authenticate, capture transaction, scan receipt, aggregate, visualise and export. All of "
            "them read or write a single logical store D1, the financial database. Scan receipt feeds capture transaction "
            "after the user confirms parsed fields.",
            "BodyNI",
        ),
    ]
    st += fig("fig_4_3_dfd.png", "Figure 4.3  Level-1 data flow of the tracking process")
    st += [PageBreak()]

    # CHAPTER 05
    st += [
        P("CHAPTER 05", "HChapter"),
        P("DETAILED DESIGN", "HChapter"),
        P("5.1  Use Case Diagram", "H1"),
        P("The actor is the registered user. Principal use cases are register or login, manage profile, add income or expense, search the ledger, scan a bill, set a budget, view dashboard charts, generate reports, create a savings goal, edit or delete a transaction, and load the demo workspace.", "BodyNI"),
    ]
    st += fig("fig_5_1_usecase.png", "Figure 5.1  Use-case view")
    st += [
        table(
            ["Actor", "Use case", "Outcome"],
            [
                ["User", "Register / login", "A session is created for a private ledger."],
                ["User", "Add income or expense", "A normalised row is stored with a category."],
                ["User", "Scan bill", "OCR text is parsed; user confirms; row is stored with source=scan."],
                ["User", "Set budget", "A monthly category ceiling is created or updated."],
                ["User", "View dashboard", "Totals, charts, insights and recent rows are shown."],
                ["User", "Export CSV", "A UTF-8 spreadsheet of the user’s transactions is downloaded."],
                ["User", "Manage goals", "Saved amounts move toward a named target."],
            ],
            [1.1 * inch, 1.8 * inch, 3.3 * inch],
        ),
        P("Table 5.1  Use-case catalogue", "Caption"),
        P("5.2  Sequence Diagram", "H1"),
        P("The scan sequence is the most distinctive interaction. The user supplies an image. The browser runs Tesseract.js, posts the file to /scan/upload and the recognised text to /scan/parse. The parser returns structured fields. After confirmation, POST /transactions/new inserts the row and the user is redirected.", "BodyNI"),
    ]
    st += fig("fig_5_2_sequence.png", "Figure 5.2  Sequence: scan bill and save transaction")
    st += [
        P("5.3  Collaboration Diagram", "H1"),
        P("Objects collaborating in the scan-and-save path are the user, the scan page, parser.py, the transaction form, the Transaction entity and the SQLAlchemy session. The ledger form can also be reached without OCR.", "BodyNI"),
    ]
    st += fig("fig_5_3_collaboration.png", "Figure 5.3  Collaboration among objects")
    st += [
        P("5.4  Activity Diagram", "H1"),
        P("The monthly tracking activity starts when the user opens the site, authenticates, and chooses manual entry or scan. A missing photo sends the user to the ordinary form. After storage the dashboard and budget bars refresh. Export is optional.", "BodyNI"),
    ]
    st += fig("fig_5_4_activity.png", "Figure 5.4  Activity: monthly expense tracking", width=5.2 * inch)
    st += [
        P("5.5  Database Design", "H1"),
        P(
            "Five tables implement the conceptual schema. USER holds identity and a hashed password. CATEGORY is a shared lookup of income and expense names with icon and colour. TRANSACTION is the fact table: amount, kind, merchant, payment method, date, source (manual, scan or demo) and optional receipt path. BUDGET stores a ceiling per user, category, month and year. GOAL stores a named target. Foreign keys isolate transactions, budgets and goals under a user. Category names are unique. Email is unique. Amounts are floating-point values suitable for rupees and paise.",
            "BodyNI",
        ),
    ]
    st += fig("fig_5_5_er.png", "Figure 5.5  Entity-relationship view")
    st += [
        table(
            ["Table", "Key fields", "Notes"],
            [
                ["user", "id, email, password_hash, monthly_income", "One person, many transactions."],
                ["category", "id, name, kind, color", "Seeded at first run."],
                ["transaction", "id, user_id, category_id, amount, kind, txn_date, source", "Income or expense fact."],
                ["budget", "id, user_id, category_id, month, year, amount", "One ceiling per category-month."],
                ["goal", "id, user_id, name, target_amount, saved_amount", "Progress is user-updated."],
            ],
            [1.4 * inch, 2.6 * inch, 2.2 * inch],
        ),
        P("Table 5.2  Data dictionary of principal tables", "Caption"),
        P(
            "Normalisation: repeating merchant names stay in the transaction row because they are descriptive attributes of a fact, not a slowly changing dimension required for this prototype. Categories are factored out to avoid spelling drift. Budgets are not stored as computed fields; they are independent planning numbers compared at read time with SUM of expenses.",
            "BodyNI",
        ),
        PageBreak(),
    ]

    # CHAPTER 06
    st += [
        P("CHAPTER 06", "HChapter"),
        P("IMPLEMENTATION", "HChapter"),
        P("6.1  Module Description", "H1"),
        table(
            ["Module", "Files / routes", "Behaviour"],
            [
                ["Authentication", "register, login, logout, demo", "Creates users, verifies hashes, seeds demo data."],
                ["Dashboard", "/dashboard", "Monthly KPIs, Chart.js data, insights, recent rows, budget snippets."],
                ["Ledger", "/transactions", "List, filter, add modal, edit, delete."],
                ["Scan", "/scan, /scan/parse, /scan/upload", "Image capture, OCR, parse, confirm."],
                ["Budgets", "/budgets", "Create/update current-month ceilings."],
                ["Reports", "/reports, /reports/export", "Year/month aggregates and CSV."],
                ["Goals", "/goals", "Create, add savings, delete."],
                ["Profile", "/profile", "Name, phone, income, password."],
                ["Parser", "parser.py", "Regex extraction of amount, date, merchant, category."],
            ],
            [1.3 * inch, 2.0 * inch, 2.9 * inch],
        ),
        P("Table 6.1  Application modules", "Caption"),
        P("6.2  Screen Shots and Demonstration", "H1"),
        P("The implemented interface uses a deep green canvas, mint accents and serif headings. The following plates correspond to the running application at http://127.0.0.1:5000.", "BodyNI"),
    ]
    st += fig("fig_6_1_login.png", "Figure 6.1  Sign-in and demonstration access")
    st += [
        P("The sign-in page states the product promise and offers registration or a live demo. The demo route creates demo@aureum.app if needed and inserts representative Indian transactions such as salary, Swiggy, Uber, DMart and Spotify.", "BodyNI"),
    ]
    st += fig("fig_6_2_dashboard.png", "Figure 6.2  Dashboard with cashflow and category charts")
    st += [
        P("The dashboard is the analysis surface promised in the synopsis. Four KPI cards report income, spent, remaining amount and savings rate. A line chart compares income and expense across six months. A doughnut chart shows where money went. Insights are short English sentences derived from category totals and budget percentages.", "BodyNI"),
    ]
    st += fig("fig_6_3_scan.png", "Figure 6.3  Scan-a-bill workspace")
    st += [
        P("The scan page accepts drag-and-drop, file picker or camera. Progress text reports OCR percentage. Detected fields are editable. A sample PhonePe image is linked for laboratory testing. Raw OCR text is available under a disclosure panel so a student can explain parsing during viva.", "BodyNI"),
    ]
    st += fig("fig_6_4_transactions.png", "Figure 6.4  Transaction ledger")
    st += fig("fig_6_5_budgets.png", "Figure 6.5  Category budgets")
    st += fig("fig_6_6_reports.png", "Figure 6.6  Reports workspace")
    st += fig("fig_6_7_goals.png", "Figure 6.7  Savings goals")
    st += [
        P("6.3  Coding and Processing Logic", "H1"),
        P("Application start-up creates tables and seeds categories if they are empty. The login_required decorator redirects anonymous users. Totals on the dashboard are computed in Python from query results filtered by the current calendar month. Savings rate is (income − expense) / income when income is positive, otherwise zero.", "BodyNI"),
        P("Receipt parsing is deterministic. Amount patterns look for phrases such as grand total, amount paid, total, Rs, INR and the rupee sign. If those fail, the largest plausible decimal number in the text is used. Dates accept dd/mm/yyyy, dd-mm-yyyy and day-month-year forms. Merchant lines prefer “Paid to”. Category inference counts keyword hits for Indian services such as Swiggy, IRCTC, Airtel and DMart.", "BodyNI"),
        P("Representative server logic for parsing is shown below. It is an explanatory extract of parser.py, not a dump of the entire repository.", "BodyNI"),
        Preformatted(
            """def parse_receipt_text(text):
    amount = first_match(AMOUNT_PATTERNS, text)
    date_value = first_date(DATE_PATTERNS, text) or today()
    merchant = extract_merchant(text)
    category = infer_category(text + " " + merchant)
    payment = "UPI" if "upi" in text.lower() else "Card"
    return {
        "amount": amount or 0,
        "date": date_value,
        "merchant": merchant,
        "category": category,
        "payment_method": payment,
    }""",
            S["CodeBlock"],
        ),
        P("Client logic for OCR is equally short. After Tesseract.js finishes, the browser posts JSON to /scan/parse and fills the confirmation form. The save button stays disabled until parsing returns or the user chooses to type values after a failure.", "BodyNI"),
        Preformatted(
            """const result = await Tesseract.recognize(file, "eng");
const res = await fetch("/scan/parse", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: result.data.text })
});
const data = await res.json();
amountInput.value = data.amount;""",
            S["CodeBlock"],
        ),
        P("Security implementation details include generate_password_hash and check_password_hash, a secret key for the Flask session, file-extension checks on uploads, and first_or_404 queries that always include user_id. SQLAlchemy parameter binding avoids string-concatenated SQL.", "BodyNI"),
        P("6.4  Route and Processing Catalogue", "H1"),
        P("The following catalogue is written so that an examiner can map any sidebar label to a function in app.py. All money queries include user_id from the session.", "BodyNI"),
        P("<b>GET /</b> redirects to the dashboard when a session exists, otherwise to login. This avoids an empty landing page.", "BodyNI"),
        P("<b>GET, POST /register</b> validates name, email and password length. Duplicate emails are rejected. On success the new user identifier is stored in the session and the dashboard opens with a welcome flash.", "BodyNI"),
        P("<b>GET, POST /login</b> loads the user by lowercase email and verifies the password hash. Failure yields a generic invalid-credentials message so that attackers cannot distinguish unknown emails from bad passwords.", "BodyNI"),
        P("<b>GET /demo</b> finds or creates demo@aureum.app, calls seed_demo_data once for a new demo user, and stores the session. Sample rows include salary, freelance income, food, travel, groceries, entertainment, shopping, education, bills and health. Three budgets and two goals are also inserted so charts are not empty during viva.", "BodyNI"),
        P("<b>GET /logout</b> clears the session.", "BodyNI"),
        P("<b>GET /dashboard</b> computes month bounds, sums income and expense, derives savings rate, compares expense with the previous month, groups expenses by category for the doughnut, and walks six calendar months for the line chart. Recent transactions are limited to eight rows. Insights mention the top category, budget pressure and unspent income when monthly_income is set on the profile.", "BodyNI"),
        P("<b>GET /transactions</b> applies optional filters kind, category, q, start and end. Results sort by date descending. The add and edit modals reuse a Jinja partial so field names stay consistent.", "BodyNI"),
        P("<b>POST /transactions/new</b> rejects non-positive amounts, parses the ISO date, and stores source and receipt_path when they arrive from the scan form.", "BodyNI"),
        P("<b>POST /transactions/&lt;id&gt;/edit</b> and <b>delete</b> load the row with user_id so a guessed identifier cannot alter another ledger.", "BodyNI"),
        P("<b>GET /scan</b> shows only expense categories in the confirmation list because a photographed bill is treated as money leaving the user. Income still uses the manual form.", "BodyNI"),
        P("<b>POST /scan/parse</b> accepts JSON or form text, runs parse_receipt_text, maps the inferred category name onto a database id, and returns JSON for the browser form.", "BodyNI"),
        P("<b>POST /scan/upload</b> stores jpg, png, jpeg, webp or bmp files under a UUID name. Other extensions are rejected.", "BodyNI"),
        P("<b>GET, POST /budgets</b> upserts a ceiling for the current month. Progress is spent divided by amount, capped visually at 100 percent.", "BodyNI"),
        P("<b>GET /reports</b> aggregates by year or optional month, builds payment-method totals and twelve monthly cashflow points. <b>GET /reports/export</b> streams a CSV with a UTF-8 BOM so Microsoft Excel on Windows opens rupee text correctly.", "BodyNI"),
        P("<b>Goals and profile routes</b> update saved_amount additively and allow an optional password change when the new value has at least six characters. Email is displayed but not edited, to keep the login key stable.", "BodyNI"),
        P("6.5  User Interface Implementation", "H1"),
        P(
            "The visual design is intentional. A dark green field with mint and gold accents presents money as a calm product rather than a spreadsheet. Fraunces is used for headings and Manrope for interface text. Glass cards, KPI tiles and progress bars give examiners something to look at from a distance during a slide-less demo. On viewports below 980 pixels the sidebar hides and a bottom tab bar appears, satisfying the synopsis requirement of a responsive interface.",
            "BodyNI",
        ),
        P(
            "Flash messages use Flask’s flashed-message API and fade after a few seconds in app.js. Chart configuration shares mint and rose colours with the CSS variables so the doughnut legend matches category pills. Empty states tell the user to scan a bill or add a row instead of showing a blank table.",
            "BodyNI",
        ),
        PageBreak(),
    ]

    # CHAPTER 07
    st += [
        P("CHAPTER 07", "HChapter"),
        P("SOFTWARE TESTING", "HChapter"),
        P("7.1  Testing Approach", "H1"),
        P(
            "Testing followed an application-oriented plan: unit checks of the parser, integration checks of Flask routes with a cookie session, validation checks of empty forms, interface checks of dashboard totals, and a security check that one user cannot open another user’s transaction by identifier. The live application on localhost was used as the test harness. Parser tests used synthetic Google Pay and PhonePe text.",
            "BodyNI",
        ),
        P("7.2  Test Cases", "H1"),
        table(
            ["ID", "Test case", "Expected result", "Status"],
            [
                ["TC-01", "Open /login", "Sign-in page renders with demo link.", "Pass"],
                ["TC-02", "Register with short password", "Rejected with validation message.", "Pass"],
                ["TC-03", "Register unique email", "Session starts; dashboard opens.", "Pass"],
                ["TC-04", "Login with wrong password", "Invalid credentials message.", "Pass"],
                ["TC-05", "Open /dashboard while logged out", "Redirect to login.", "Pass"],
                ["TC-06", "Click Try the live demo", "Seeded dashboard for Aarav.", "Pass"],
                ["TC-07", "Add expense 280 Food", "Row appears in ledger.", "Pass"],
                ["TC-08", "Add income salary", "Dashboard income increases.", "Pass"],
                ["TC-09", "Edit merchant name", "Updated text stored.", "Pass"],
                ["TC-10", "Delete a row", "Row removed after confirm.", "Pass"],
                ["TC-11", "Filter kind=expense", "Income rows hidden.", "Pass"],
                ["TC-12", "Search Swiggy", "Matching merchant rows listed.", "Pass"],
                ["TC-13", "Set Food budget 6000", "Budget card shows percentage.", "Pass"],
                ["TC-14", "Open reports for 2026", "Income, expense, net displayed.", "Pass"],
                ["TC-15", "Export CSV", "File downloads with headers.", "Pass"],
                ["TC-16", "Create emergency-fund goal", "Progress bar rendered.", "Pass"],
                ["TC-17", "Add 1000 to goal", "Saved amount increases.", "Pass"],
                ["TC-18", "Update profile phone", "Value persists after reload.", "Pass"],
                ["TC-19", "Parse GPay text Paid to Swiggy Rs 428", "amount 428, category Food, UPI.", "Pass"],
                ["TC-20", "Parse PhonePe Zomato Rs 642 26/10/2026", "merchant Zomato, date 2026-10-26.", "Pass"],
                ["TC-21", "Upload non-image file to scan", "JSON error asking for JPG/PNG/WEBP.", "Pass"],
                ["TC-22", "Save scanned row after confirm", "source=scan in database.", "Pass"],
                ["TC-23", "Two users, same category names", "Totals never mix across sessions.", "Pass"],
                ["TC-24", "Mobile-width layout", "Bottom tabs visible; pages usable.", "Pass"],
                ["TC-25", "Empty amount on add", "Transaction not stored.", "Pass"],
            ],
            [0.7 * inch, 2.1 * inch, 2.1 * inch, 0.7 * inch],
        ),
        P("Table 7.1  Test cases", "Caption"),
        P("7.3  Parser Evaluation Notes", "H1"),
        P("A controlled Google Pay sample produced amount 428, merchant Swiggy, category Food and payment UPI. A PhonePe-style sample produced amount 642 and merchant Zomato. Photographs that are blurred, cropped away from the total, or written in heavy stylised fonts may yield empty amounts; the confirmation form then requires typing. This limitation is accepted for an academic OCR path and is disclosed to the user through status text such as “amount was unclear”.", "BodyNI"),
        P("7.4  Validation, Usability and Security", "H1"),
        P("Validation tests covered empty registration fields, duplicate email, non-numeric amounts and missing category. Usability observations: the demo button lets an examiner reach charts in one click; the scan page keeps raw text for teaching; budget bars use both length and a numeric percentage so colour is not the only signal. Security observations: password hashes are not reversible in the database file; transaction edit URLs belonging to another user id return 404; uploaded files are renamed with UUID prefixes.", "BodyNI"),
        P("7.5  Defect Tracking Practice", "H1"),
        P("Defects during development were corrected immediately in the same iteration rather than through a separate industrial bug tracker. Remaining known limitations are documented in Chapter 9: OCR quality on poor photos, absence of multi-currency, and absence of emailed reminders. A release for viva is accepted when TC-01 to TC-25 behave as in Table 7.1 on the demonstration machine.", "BodyNI"),
        P("7.6  Input Validation and Ingestion Tests", "H1"),
        P(
            "Planned and executed validation goes beyond happy-path clicks. Registration must fail when the name is blank, when the email is not a well-formed address, and when the password is shorter than six characters. A second registration with the same email must fail without creating a second USER row. Login must fail both for an unknown email and for a known email with a wrong password, with the same user-visible wording.",
            "BodyNI",
        ),
        P(
            "Transaction amounts of zero, negative numbers and non-numeric text must not be stored. Dates must be calendar dates. Scan upload must refuse a .pdf or .exe even if the field is renamed. Maximum upload size is bounded by Flask MAX_CONTENT_LENGTH at twelve megabytes so a laboratory computer is not filled by a mistaken video file. Parser input that contains no digits should yield amount 0 and leave the save button enabled so the user can type.",
            "BodyNI",
        ),
        P(
            "Unicode merchants such as names in Kannada or Hindi should store without crashing; the SQLite default encoding is UTF-8. Extremely long notes are truncated by the VARCHAR(255) column, which is an accepted prototype limit and should be mentioned if a tester pastes a full invoice.",
            "BodyNI",
        ),
        P("7.7  Aggregation and Consistency Tests", "H1"),
        P(
            "Dashboard income for a month must equal the sum of income rows whose txn_date lies between the first and last day of that month. Expense must match likewise. Remaining balance is income minus expense and may be negative if the user overspends; the interface still shows the signed value. Savings rate uses income as denominator and must not divide by zero.",
            "BodyNI",
        ),
        P(
            "Budget percentage uses only expense rows of that category in the same month, not income, not other months, and not other users. Reports for a whole year must equal the sum of the twelve monthly buckets. CSV export order is date descending and must include every row belonging to the session user and no other user. Repeating the same report request twice in one session must reproduce the same totals because aggregation is deterministic.",
            "BodyNI",
        ),
        P("7.8  Usability, Accessibility and Responsive Tests", "H1"),
        P(
            "Keyboard users can tab through login fields and submit with Enter. Scan buttons are ordinary HTML buttons. Colour is not the only meaning: expenses use a minus sign as well as a rose colour; budgets print a numeric percent. Contrast on mint-on-dark buttons was chosen for projection in a classroom. At a narrow viewport the examiner can still reach Scan, Ledger and Reports from the bottom tabs. Browser zoom to 125 percent should keep primary actions visible. Flash messages must not cover the add-transaction button.",
            "BodyNI",
        ),
        P("7.9  Privacy and Responsible-Use Tests", "H1"),
        P(
            "Receipt photographs can contain account numbers. The prototype stores them locally under generated names and does not print them on the dashboard. A production deployment should add login throttling, HTTPS, and a delete-account path that removes images. The scanner must not be used to photograph another person’s private messages. Suggested merchants are taken from OCR text; the parser must not invent a famous brand when the text is empty. These responsible-use rules were treated as acceptance criteria even though the laboratory deployment is local.",
            "BodyNI",
        ),
        P("7.10  Test Execution Record", "H1"),
        P(
            "Execution distinguished observed localhost results from planned production checks. TC-01 to TC-25 in Table 7.1 were observed on Windows 10 with Python 3.14 and Chrome against http://127.0.0.1:5000. Parser samples were executed as a Python command importing parser.py. HTTPS, multi-machine MySQL and screen-reader certification remain planned for any public host and are not claimed as passed. High-severity issues found during coding were fixed before this report was generated. Unresolved limitations are listed only in Chapter 9.",
            "BodyNI",
        ),
        PageBreak(),
    ]

    # CHAPTER 08-09
    st += [
        P("CHAPTER 08", "HChapter"),
        P("CONCLUSION", "HChapter"),
        P(
            "The Smart Personal Expense Tracker and Financial Analysis System demonstrates that a focused Flask application can turn scattered daily spending into a structured ledger with charts, budgets and goals. It satisfies the synopsis objectives of authentication, categorised transactions, history, monthly and yearly analysis, graphical reports, budget limits, a usable interface and relational storage. The additional scan module addresses the practical reason people abandon trackers: typing every UPI payment is tedious. By pairing on-device OCR with an explicit confirmation step, the project stays honest about automation.",
            "BodyNI",
        ),
        P(
            "The work also shows standard software-engineering practice: requirements, layered design, an ER schema, implementation of modules, and a documented test table. The prototype is suitable for laboratory demonstration and for personal use on a laptop. It is not a bank. Its value is clarity—seeing where money went—so that a student or professional can choose the next expense with more discipline.",
            "BodyNI",
        ),
        PageBreak(),
        P("CHAPTER 09", "HChapter"),
        P("FUTURE ENHANCEMENTS", "HChapter"),
    ]
    st += bullets(
        [
            "Native Android or iOS wrappers so camera capture is even faster on a phone.",
            "Optional import of bank or UPI CSV statements while still avoiding live bank login.",
            "Recurring bills with reminder dates for rent, broadband and subscriptions.",
            "Household sharing with role-based access for a family ledger.",
            "Stronger OCR using server-side Tesseract or a small vision model for crumpled paper bills.",
            "Budgets that roll across months and warn by email or push notification.",
            "Multi-currency and overseas-student modes.",
            "Spending prediction using simple moving averages, as suggested in the synopsis future work.",
            "Two-factor authentication and encrypted receipt storage for a hosted deployment.",
            "Accessibility audit against WCAG on both the dark theme and a light theme toggle.",
        ]
    )
    st += [PageBreak()]

    # REFERENCES
    st += [
        P("REFERENCES", "HChapter"),
        P("[1]  A. Lusardi and O. S. Mitchell, “The economic importance of financial literacy,” Journal of Economic Literature, 2014.", "BodyNI"),
        P("[2]  R. S. Pressman and B. R. Maxim, Software Engineering: A Practitioner’s Approach. McGraw-Hill.", "BodyNI"),
        P("[3]  A. Silberschatz, H. F. Korth and S. Sudarshan, Database System Concepts. McGraw-Hill.", "BodyNI"),
        P("[4]  M. Grinberg, Flask Web Development. O’Reilly Media.", "BodyNI"),
        P("[5]  S. Few, Information Dashboard Design. Analytics Press.", "BodyNI"),
        P("[6]  A. Dix, J. Finlay, G. Abowd and R. Beale, Human–Computer Interaction. Pearson.", "BodyNI"),
        P("[7]  R. Smith, “An overview of the Tesseract OCR engine,” in Proc. ICDAR.", "BodyNI"),
        P("[8]  C. D. Manning, P. Raghavan and H. Schütze, Introduction to Information Retrieval. Cambridge University Press.", "BodyNI"),
        P("[9]  OWASP Foundation, Application Security Verification Standard.", "BodyNI"),
        P("[10] G. J. Myers, C. Sandler and T. Badgett, The Art of Software Testing. Wiley.", "BodyNI"),
        P("[11] E. Marcotte, Responsive Web Design. A Book Apart.", "BodyNI"),
        P("[12] Chart.js documentation, https://www.chartjs.org.", "BodyNI"),
        P("[13] Pallets Projects, Flask documentation, https://flask.palletsprojects.com.", "BodyNI"),
        P("[14] Bootstrap 5 documentation, https://getbootstrap.com.", "BodyNI"),
        P("[15] Dr. Manmohan Singh Bengaluru City University / Seshadripuram College, Guidelines for the Preparation of Project Reports, BCA, 2026-27.", "BodyNI"),
        PageBreak(),
    ]

    # APPENDIX A
    st += [
        P("APPENDIX A", "HChapter"),
        P("USER MANUAL", "HChapter"),
        P("A.1  Installation", "H1"),
        P("Copy the project folder smart-expense-tracker to the laboratory computer. Open a terminal in that folder. Create a virtual environment if desired. Install dependencies with python -m pip install -r requirements.txt. Start the server with python app.py. Open Chrome at http://127.0.0.1:5000.", "BodyNI"),
        P("A.2  First use", "H1"),
        P("Choose Create an account and enter name, email and password, or choose Try the live demo. The demo password documented in the README is demo123 for demo@aureum.app after the demo route has created the user.", "BodyNI"),
        P("A.3  Recording a cash expense", "H1"),
        P("Open Transactions, click Add transaction, choose Expense, type the amount, pick a category, set the date, choose Cash, enter a merchant and save.", "BodyNI"),
        P("A.4  Scanning a UPI bill", "H1"),
        P("Open Scan a bill. Upload a clear screenshot showing Paid to, the rupee amount and the date. Wait until Detected details fill. Correct any field. Click Add to tracker. Verify the new row on the dashboard.", "BodyNI"),
        P("A.5  Budgets, reports and goals", "H1"),
        P("Under Budgets, pick a category and a monthly rupee limit. Under Reports, choose a year or month and optionally download CSV. Under Goals, name a target, enter already-saved money, and add later deposits.", "BodyNI"),
        P("A.6  MySQL option", "H1"),
        P("Create a database with schema.sql. Copy .env.example to .env and set DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/expense_tracker. Restart the application. Tables are created if they do not exist.", "BodyNI"),
        PageBreak(),
        P("APPENDIX B", "HChapter"),
        P("DATA DICTIONARY (EXPANDED)", "HChapter"),
        P("user.id — integer primary key. user.name — up to 120 characters. user.email — unique login identity. user.password_hash — Werkzeug hash, never logged. user.phone — optional. user.monthly_income — planning figure used in insights. user.currency — default INR. user.created_at — UTC timestamp.", "BodyNI"),
        P("category.id — integer primary key. category.name — unique label. category.kind — income or expense. category.icon — Bootstrap icon name. category.color — hex colour for charts and pills.", "BodyNI"),
        P("transaction.id — integer primary key. transaction.user_id — owner. transaction.category_id — classification. transaction.amount — positive rupee value. transaction.kind — income or expense. transaction.note — free text. transaction.merchant — payee. transaction.payment_method — UPI, Card, Cash, Net Banking, Wallet or Bank. transaction.txn_date — business date. transaction.source — manual, scan or demo. transaction.receipt_path — relative static path. transaction.created_at — insertion time.", "BodyNI"),
        P("budget.id — integer primary key. budget.month and budget.year — calendar identity of the ceiling. budget.amount — planned maximum expense for that category.", "BodyNI"),
        P("goal.id — integer primary key. goal.name — for example Emergency fund. goal.target_amount — desired total. goal.saved_amount — running total. goal.deadline — optional date.", "BodyNI"),
        PageBreak(),
        P("APPENDIX C", "HChapter"),
        P("SAMPLE RECEIPT PARSING", "HChapter"),
        P("Input text used during development:", "BodyNI"),
        Preformatted(
            """Google Pay
Payment successful
Paid to Swiggy
Rs 428.00
26 Oct 2026
UPI transaction ID 1234567890""",
            S["CodeBlock"],
        ),
        P("Parser output: amount 428.0, date 2026-10-26, merchant Swiggy, category Food, payment_method UPI, note “Imported from receipt - Swiggy”. This sample confirms that Indian UPI vocabulary is within the scope of the extraction rules described in Chapter 6.", "BodyNI"),
        PageBreak(),
        P("APPENDIX D", "HChapter"),
        P("WEBSITE SCREEN GUIDE AND OPERATIONAL EVALUATION", "HChapter"),
        P("D.1  Sign-in and demonstration access", "H1"),
        P("The left column of the login page explains three ideas: photograph a bill, read monthly charts, and keep the ledger on the local machine. The right column is the credential card. Examiners who do not wish to invent an email should use Try the live demo. After the demo redirect, a flash confirms that sample money stories were loaded. Sign out returns to this page and the session cookie is cleared.", "BodyNI"),
        P("D.2  Dashboard evaluation", "H1"),
        P("A successful dashboard load shows four KPIs, two charts, a recent list and an insight list. If charts fail, the usual cause is a blocked CDN for Chart.js; the rest of the page still shows numeric totals. If all KPIs are zero, the month has no rows—either switch to the demo user or add a salary row dated in the current month. The Scan a bill button in the header is a shortcut to the OCR workspace.", "BodyNI"),
        P("D.3  Scan workbench evaluation", "H1"),
        P("Operational success means: an image appears in the frame, the progress line moves, raw text is not empty, and at least the date field is filled. Operational partial success means text appears but amount is zero; the user types the total. Operational failure means the camera is denied; the user switches to Choose photo. The sample PhonePe screenshot in static/uploads/receipts can be downloaded and re-uploaded when a live camera is unavailable in the laboratory.", "BodyNI"),
        P("D.4  Ledger, budget and report evaluation", "H1"),
        P("The ledger must show both plus and minus amounts. Filters combine with AND logic. A budget that exceeds 100 percent should still be deletable. Reports month list uses English month names. CSV should open in Excel with columns Date, Type, Category, Merchant, Amount, Payment, Note, Source. Goals must not allow a blank name. Profile email is read-only.", "BodyNI"),
        P("D.5  Operational risks", "H1"),
        P("If two students run python app.py on the same port 5000, the second process will fail; choose another port. If instance/expense.db is deleted, accounts vanish but categories are reseeded. If the machine is offline, CDN scripts for Bootstrap, icons, Chart.js and Tesseract.js will not load; a laboratory with internet is assumed, matching the synopsis network requirement. These risks are operational rather than algorithmic and should be checked before a scheduled viva.", "BodyNI"),
        PageBreak(),
        P("APPENDIX E", "HChapter"),
        P("PROJECT ORGANISATION AND SOURCE MAP", "HChapter"),
        P("The repository is organised for a student examiner who opens the folder for the first time.", "BodyNI"),
    ]
    st += bullets(
        [
            "app.py — application factory, routes, dashboard aggregates, demo seed.",
            "models.py — SQLAlchemy entities User, Category, Transaction, Budget, Goal.",
            "parser.py — receipt and UPI text extraction rules.",
            "config.py — secret key, database URI, upload folder, twelve-megabyte limit.",
            "schema.sql — MySQL CREATE statements matching the ORM.",
            "requirements.txt — pinned Python dependencies.",
            "templates/ — Jinja documents including base, login, dashboard, scan, reports.",
            "static/css/style.css — visual design system.",
            "static/js/app.js — Chart.js bootstrapping.",
            "static/js/scan.js — camera, Tesseract.js, parse POST.",
            "docs/ — this report generator, figures and the official PDF.",
        ]
    )
    st += [
        P(
            "The candidate name on every formal page of this volume is Drup Kumar Paswan. The university seat number is "
            "U18GH24S0085. The internal guide is Tejaswini, Assistant Professor. The work was carried out in the Department "
            "of Computer Science, Seshadripuram College, Bengaluru, affiliated to Dr. Manmohan Singh Bengaluru City "
            "University, during the academic year 2026-27, as a partial fulfillment of the Bachelor of Computer Applications "
            "degree. Two printed copies and a compact disc with the software and this report are required by the college "
            "guidelines; the electronic PDF supplied with the source tree is the candidate’s soft copy.",
            "BodyNI",
        ),
        P(
            "The candidate confirms that screenshots and figures in Chapters 4 to 6 describe the software that accompanies "
            "this report, that test statuses marked Pass were observed on the development computer, and that OCR is an "
            "assistive feature requiring human confirmation. No bank credentials were used. No third-party paid API was "
            "required to obtain the results discussed here.",
            "BodyNI",
        ),
        Spacer(1, 24),
        P("— End of Report —", "CenterBold"),
        P(f"{STUDENT}  |  {USN}  |  {YEAR}", "Center"),
        P("Seshadripuram College, Bengaluru–20", "Center"),
    ]
    return st


def main():
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=1.25 * inch,
        rightMargin=1.00 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.90 * inch,
        title=TITLE,
        author=STUDENT,
        subject="BCA Project Report",
    )
    doc.build(story(), onFirstPage=header_footer, onLaterPages=header_footer)
    STUDY_COPY.parent.mkdir(parents=True, exist_ok=True)
    STUDY_COPY.write_bytes(OUT_PDF.read_bytes())
    print("PDF pages written to", OUT_PDF)
    print("Copy:", STUDY_COPY)
    print("size_bytes", OUT_PDF.stat().st_size)


if __name__ == "__main__":
    main()
