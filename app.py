from ui.feed import render_feed
from ui.home import render_home
from ui.business_memory import render_business_memory
from ui.identity_review import render_identity_review
from ui.pilot_mode import render_pilot_mode
from ui.accountant_workspace import render_accountant_workspace
from ui.design_system import render_global_styles
from ui.recipes import render_recipes
import re
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from landing_page import render_landing_page

from ui.sidebar import render_sidebar

from batch_dashboard import render_batch_dashboard
from ai_dashboard import render_ai_dashboard
from business_dashboard import render_business_dashboard
from smart_archive import render_database_archive
from daily_intake import render_daily_intake
from database_dashboard import render_database_dashboard
from migration_dashboard import render_migration_dashboard
from month_closing import render_month_closing
from database_diagnostics import render_database_diagnostics
from supplier_page import render_suppliers_page
from enhanced_dashboard import render_enhanced_dashboard
from ai_accountant import render_ai_accountant
from services.pilot_support import APP_VERSION, log_runtime_error

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
PREVIEW_DIR = DATA_DIR / "previews"
DB_PATH = DATA_DIR / "invoices.db"

for folder in (DATA_DIR, UPLOAD_DIR, PREVIEW_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        original_file_name TEXT NOT NULL,
        stored_file_path TEXT NOT NULL,
        document_type TEXT,
        supplier TEXT,
        supplier_id TEXT,
        invoice_number TEXT,
        invoice_date TEXT,
        due_date TEXT,
        subtotal REAL,
        vat REAL,
        total REAL,
        currency TEXT DEFAULT 'ILS',
        notes TEXT,
        raw_text TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        item_code TEXT,
        description TEXT,
        quantity REAL,
        unit_price REAL,
        line_total REAL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id)
    )
    """)
    conn.commit()
    return conn


def run_command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "הפקודה נכשלה")
    return result.stdout


def convert_pdf_to_images(pdf_path: Path) -> list[Path]:
    prefix = PREVIEW_DIR / f"{pdf_path.stem}_page"
    run_command([
        "/opt/homebrew/bin/pdftoppm",
        "-png", "-r", "160",
        str(pdf_path), str(prefix)
    ])
    return sorted(PREVIEW_DIR.glob(f"{pdf_path.stem}_page-*.png"))


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        txt_path = path.with_suffix(".txt")
        try:
            run_command([
                "/opt/homebrew/bin/pdftotext",
                "-layout", str(path), str(txt_path)
            ])
            text = txt_path.read_text(encoding="utf-8", errors="ignore")
            if len(re.sub(r"\s+", "", text)) >= 40:
                return text
        except Exception:
            pass

        pages = convert_pdf_to_images(path)
        texts = []
        for page in pages:
            with tempfile.TemporaryDirectory() as td:
                out_base = Path(td) / "ocr"
                run_command([
                    "/opt/homebrew/bin/tesseract",
                    str(page), str(out_base),
                    "-l", "heb+eng", "--psm", "6"
                ])
                txt = out_base.with_suffix(".txt")
                if txt.exists():
                    texts.append(txt.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(texts)

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td) / "ocr"
            run_command([
                "/opt/homebrew/bin/tesseract",
                str(path), str(out_base),
                "-l", "heb+eng", "--psm", "6"
            ])
            return out_base.with_suffix(".txt").read_text(
                encoding="utf-8", errors="ignore"
            )

    raise ValueError("סוג קובץ לא נתמך")


from parser_engine import parse_invoice as infer_fields, extract_items


def save_invoice(data, items_df, uploaded_name, stored_path, raw_text):
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO invoices (
            created_at, original_file_name, stored_file_path,
            document_type, supplier, supplier_id, invoice_number,
            invoice_date, due_date, subtotal, vat, total,
            currency, notes, raw_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        uploaded_name,
        str(stored_path),
        data["document_type"],
        data["supplier"],
        data["supplier_id"],
        data["invoice_number"],
        data["invoice_date"],
        data["due_date"],
        data["subtotal"],
        data["vat"],
        data["total"],
        data["currency"],
        data["notes"],
        raw_text,
    ))
    invoice_id = cursor.lastrowid

    for _, item in items_df.iterrows():
        description = str(item.get("תיאור", "")).strip()
        if not description:
            continue
        conn.execute("""
            INSERT INTO invoice_items (
                invoice_id, item_code, description,
                quantity, unit_price, line_total
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            str(item.get("קוד מוצר", "")).strip(),
            description,
            float(item.get("כמות", 0) or 0),
            float(item.get("מחיר יחידה", 0) or 0),
            float(item.get("סה״כ שורה", 0) or 0),
        ))

    conn.commit()


def load_invoices():
    return pd.read_sql_query("""
        SELECT
            id,
            invoice_date,
            supplier,
            document_type,
            invoice_number,
            subtotal,
            vat,
            total,
            original_file_name
        FROM invoices
        ORDER BY id DESC
    """, get_db())


st.set_page_config(page_title="Barni", page_icon="🥚", layout="wide")
render_global_styles()

render_landing_page()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: #f4f0e5;
        border-right: 1px solid rgba(35, 60, 46, 0.12);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        border: 0;
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        background: transparent;
        color: #24362b;
        font-weight: 500;
        text-align: left;
        box-shadow: none;
        transition:
            background 160ms ease,
            transform 160ms ease;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(54, 94, 68, 0.10);
        transform: translateX(2px);
        color: #183b28;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #dce8d8;
        color: #173d28;
        font-weight: 700;
    }

    .barni-sidebar-header {
        text-align: center;
        padding: 0.4rem 0 1.2rem;
    }

    .barni-sidebar-egg {
        display: inline-block;
        font-size: 2.4rem;
        line-height: 1;
        margin-bottom: 0.45rem;
        transform-origin: 50% 86%;
        animation: barni-egg-hatch 3s ease-in-out infinite;
        will-change: transform, filter;
    }

    @keyframes barni-egg-hatch {
        0%, 72%, 84%, 96%, 100% {
            transform: rotate(0deg) scale(1, 1);
            filter: drop-shadow(0 2px 3px rgba(35, 60, 46, 0.08));
        }
        76% {
            transform: rotate(-1.6deg) scale(1.012, 0.992);
            filter: drop-shadow(1px 4px 4px rgba(35, 60, 46, 0.14));
        }
        80% {
            transform: rotate(1.7deg) scale(0.994, 1.014);
            filter: drop-shadow(-1px 4px 5px rgba(35, 60, 46, 0.15));
        }
        88% {
            transform: rotate(-1.1deg) scale(1.008, 0.996);
            filter: drop-shadow(1px 3px 4px rgba(35, 60, 46, 0.12));
        }
        92% {
            transform: rotate(1deg) scale(0.997, 1.009);
            filter: drop-shadow(-1px 3px 4px rgba(35, 60, 46, 0.12));
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .barni-sidebar-egg {
            animation: none;
            transform: none;
            filter: none;
        }
    }

    .barni-sidebar-name {
        color: #173d28;
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: 0.02em;
    }

    .barni-sidebar-subtitle {
        color: #738078;
        font-size: 0.78rem;
        margin-top: 0.15rem;
    }

    .barni-divider {
        height: 1px;
        margin: 0.45rem 0 0.8rem;
        background: rgba(35, 60, 46, 0.12);
    }

    .barni-version {
        color: #8a948d;
        font-size: 0.7rem;
        text-align: center;
        padding-top: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGE_HOME = "Barni"
PAGE_FEED = "קליטה יומית"
PAGE_SEARCH = "חיפוש חשבוניות"
PAGE_KNOWLEDGE = "ספקים"
PAGE_MEMORY = "Business Memory"
PAGE_IDENTITY_REVIEW = "Identity Review"
PAGE_INSIGHTS = "דשבורד"
PAGE_RECIPES = "מתכונים"
PAGE_PILOT = "Pilot Mode"
PAGE_ACCOUNTANT = "Accountant Workspace"

if "current_page" not in st.session_state:
    st.session_state.current_page = PAGE_HOME

st.sidebar.markdown(
    """
    <div class="barni-sidebar-header">
        <div class="barni-sidebar-egg">🥚</div>
        <div class="barni-sidebar-name">Barni</div>
        <div class="barni-sidebar-subtitle">
            Your Business Memory
        </div>
    </div>
    <div class="barni-divider"></div>
    """,
    unsafe_allow_html=True,
)

def navigation_button(
    label: str,
    target: str,
    *,
    key: str,
) -> None:
    active = st.session_state.current_page == target

    if st.sidebar.button(
        label,
        key=key,
        type="primary" if active else "secondary",
        width="stretch",
    ):
        if target == PAGE_PILOT:
            st.session_state.pilot_source_page = st.session_state.current_page
        st.session_state.current_page = target
        st.rerun()


navigation_button(
    "🏠  Home",
    PAGE_HOME,
    key="nav_home",
)
navigation_button(
    "📄  Feed Barni",
    PAGE_FEED,
    key="nav_feed",
)
navigation_button(
    "🔍  Search Invoices",
    PAGE_SEARCH,
    key="nav_search",
)
navigation_button(
    "◫  Knowledge",
    PAGE_KNOWLEDGE,
    key="nav_knowledge",
)
navigation_button(
    "🧠  Business Memory",
    PAGE_MEMORY,
    key="nav_memory",
)
navigation_button(
    "📈  Insights",
    PAGE_INSIGHTS,
    key="nav_insights",
)
navigation_button(
    "🍽️  Recipes",
    PAGE_RECIPES,
    key="nav_recipes",
)
navigation_button(
    "▣  Accountant Workspace",
    PAGE_ACCOUNTANT,
    key="nav_accountant",
)
navigation_button(
    "◇  Pilot Dashboard",
    PAGE_PILOT,
    key="nav_pilot",
)
st.sidebar.markdown(
    '<div class="barni-divider"></div>',
    unsafe_allow_html=True,
)

with st.sidebar.expander("Internal tools"):
    developer_pages = {
        "בדיקת מאגר": "בדיקת מאגר",
        "חילוץ AI": "חילוץ AI",
        "הגירת מאגר": "הגירת מאגר",
        "סגירת חודש": "סגירת חודש",
        "בריאות מסד": "בריאות מסד",
        "העלאה ישנה": "העלאת חשבונית",
        "ארכיון ישן": "ארכיון",
    }

    for label, target in developer_pages.items():
        if st.button(
            label,
            key=f"developer_{target}",
            width="stretch",
        ):
            st.session_state.current_page = target
            st.rerun()

st.sidebar.markdown(
    f'<div class="barni-version">Barni · {APP_VERSION}</div>',
    unsafe_allow_html=True,
)

page = st.session_state.current_page


def render_page_safely(page_name: str, renderer) -> None:
    try:
        renderer()
    except Exception as exc:
        log_runtime_error(page_name, exc)
        st.error("Barni ran into a problem on this page. The details were logged for review.")


if page == PAGE_HOME:
    render_page_safely(PAGE_HOME, render_home)

if page == PAGE_RECIPES:
    render_page_safely(PAGE_RECIPES, render_recipes)

if page == PAGE_MEMORY:
    render_page_safely(PAGE_MEMORY, render_business_memory)

if page == PAGE_IDENTITY_REVIEW:
    render_page_safely(PAGE_IDENTITY_REVIEW, render_identity_review)

if page == PAGE_ACCOUNTANT:
    render_page_safely(PAGE_ACCOUNTANT, render_accountant_workspace)

if page == PAGE_PILOT:
    render_page_safely(
        PAGE_PILOT,
        lambda: render_pilot_mode(st.session_state.get("pilot_source_page", PAGE_HOME)),
    )

if page == "העלאת חשבונית":
    uploaded = st.file_uploader(
        "בחר תמונה או PDF",
        type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "webp"]
    )

    if uploaded:
        stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded.name}"
        stored_path = UPLOAD_DIR / stored_name
        stored_path.write_bytes(uploaded.getbuffer())

        with st.spinner("קורא ומעבד את החשבונית..."):
            try:
                raw_text = extract_text(stored_path)
                guessed = infer_fields(raw_text)
                extracted_items = extract_items(raw_text)
                preview_pages = (
                    convert_pdf_to_images(stored_path)
                    if stored_path.suffix.lower() == ".pdf"
                    else [stored_path]
                )
            except Exception as exc:
                log_runtime_error("העלאת חשבונית", exc)
                st.error(f"שגיאה בעיבוד החשבונית: {exc}")
                st.stop()

        left, right = st.columns([1.2, 1], gap="large")

        with left:
            st.subheader("תצוגת החשבונית")
            if len(preview_pages) == 1:
                st.image(str(preview_pages[0]), width="stretch")
            else:
                page_number = st.selectbox(
                    "עמוד",
                    list(range(1, len(preview_pages) + 1)),
                    format_func=lambda x: f"עמוד {x}"
                )
                st.image(str(preview_pages[page_number - 1]), width="stretch")

        with right:
            st.subheader("הנתונים שחולצו")

            document_types = [
                "חשבונית מס",
                "חשבונית מס/קבלה",
                "קבלה",
                "חשבונית זיכוי",
                "תעודת משלוח",
                "ריכוז חשבון",
                "דרישת תשלום",
                "אחר"
            ]
            default_index = (
                document_types.index(guessed["document_type"])
                if guessed["document_type"] in document_types
                else 0
            )

            document_type = st.selectbox(
                "סוג מסמך", document_types, index=default_index
            )
            supplier = st.text_input("שם ספק", guessed["supplier"])
            supplier_id = st.text_input(
                "ח.פ. / עוסק מורשה", guessed["supplier_id"]
            )
            invoice_number = st.text_input(
                "מספר חשבונית / קבלה", guessed["invoice_number"]
            )
            invoice_date = st.text_input(
                "תאריך חשבונית",
                guessed["invoice_date"],
                placeholder="YYYY-MM-DD"
            )
            due_date = st.text_input(
                "תאריך פירעון",
                guessed["due_date"],
                placeholder="YYYY-MM-DD"
            )

            subtotal = st.number_input(
                "סכום לפני מע״מ",
                value=float(guessed["subtotal"] or 0),
                step=0.01,
                format="%.2f"
            )
            vat = st.number_input(
                "מע״מ",
                value=float(guessed["vat"] or 0),
                step=0.01,
                format="%.2f"
            )
            total = st.number_input(
                "סכום כולל",
                value=float(guessed["total"] or 0),
                step=0.01,
                format="%.2f"
            )
            notes = st.text_area("הערות")

            if subtotal or vat or total:
                expected_total = round(subtotal + vat, 2)
                if abs(expected_total - total) <= 0.02:
                    st.success("בדיקת סכומים תקינה")
                else:
                    st.warning(
                        f"לפי לפני מע״מ + מע״מ, הסכום אמור להיות "
                        f"{expected_total:,.2f} ₪"
                    )

        st.divider()
        st.subheader("שורות מוצרים")

        items_df = pd.DataFrame(extracted_items) if extracted_items else pd.DataFrame([{
            "קוד מוצר": "",
            "תיאור": "",
            "כמות": 1.0,
            "מחיר יחידה": 0.0,
            "סה״כ שורה": 0.0,
        }])

        edited_items = st.data_editor(
            items_df,
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            column_config={
                "קוד מוצר": st.column_config.TextColumn("קוד מוצר"),
                "תיאור": st.column_config.TextColumn("תיאור", width="large"),
                "כמות": st.column_config.NumberColumn("כמות", min_value=0.0),
                "מחיר יחידה": st.column_config.NumberColumn(
                    "מחיר יחידה", format="%.2f ₪"
                ),
                "סה״כ שורה": st.column_config.NumberColumn(
                    "סה״כ שורה", format="%.2f ₪"
                ),
            }
        )

        with st.expander("הצג טקסט שחולץ"):
            st.text_area(
                "טקסט גולמי",
                raw_text,
                height=260,
                label_visibility="collapsed"
            )

        if st.button("שמור חשבונית", type="primary", width="stretch"):
            if not supplier:
                st.error("חסר שם ספק.")
            elif not invoice_date:
                st.error("חסר תאריך חשבונית.")
            else:
                save_invoice(
                    {
                        "document_type": document_type,
                        "supplier": supplier,
                        "supplier_id": supplier_id,
                        "invoice_number": invoice_number,
                        "invoice_date": invoice_date,
                        "due_date": due_date,
                        "subtotal": subtotal,
                        "vat": vat,
                        "total": total,
                        "currency": "ILS",
                        "notes": notes,
                    },
                    edited_items,
                    uploaded.name,
                    stored_path,
                    raw_text
                )
                st.success("החשבונית ושורות המוצרים נשמרו בארכיון.")

if page == "ארכיון":
    render_page_safely(page, render_database_archive)


if page == "בדיקת מאגר":
    render_page_safely(page, render_batch_dashboard)


if page == "חילוץ AI":
    render_page_safely(page, render_ai_dashboard)


if page == "דשבורד":
    render_page_safely(page, render_enhanced_dashboard)


if page == "חיפוש חשבוניות":
    render_page_safely(page, render_database_archive)


if page == "קליטה יומית":
    render_page_safely(page, render_daily_intake)


if page == "הגירת מאגר":
    render_page_safely(page, render_migration_dashboard)


if page == "סגירת חודש":
    render_page_safely(page, render_month_closing)


if page == "בריאות מסד":
    render_page_safely(page, render_database_diagnostics)


if page == "ספקים":
    render_page_safely(page, render_suppliers_page)
