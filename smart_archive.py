from __future__ import annotations

import calendar
import html
import re
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from services.business_identity import BusinessIdentityRepository

from services.barni_thinking import think_about_invoice
from services.invoice_workflow import (
    STATUS_LABELS,
    database_record_lifecycle,
    database_status_label,
)
from services.search_matching import (
    SearchSuggestion,
    build_search_suggestions,
    contains_search_match,
    search_suggestion_catalog,
)
from ui.barni_thinking import render_barni_thinking
from ui.design_system import primary_workspace, render_page_header

from database import (
    all_tags,
    invoice_history,
    invoice_items,
    invoice_tags,
    search_invoices,
    search_suggestion_rows,
    set_invoice_tags,
    suppliers,
    update_invoice,
)


DOCUMENT_TYPES = [
    "חשבונית מס", "חשבונית מס/קבלה", "קבלה", "חשבונית זיכוי",
    "תעודת משלוח", "ריכוז חשבון", "דרישת תשלום", "אחר",
]


def _memory_suggestions(product_names: list[str], supplier_names: list[str]) -> list[str]:
    values = [
        str(value).strip()
        for value in [*product_names, *supplier_names]
        if str(value).strip() and len(str(value).strip()) <= 36
    ]
    return list(dict.fromkeys(values))[:4]


def _render_search_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-barni_primary_workspace_search input {
            font-size: 1.18rem;
            min-height: 3.65rem;
        }
        .st-key-search_form [data-testid="stHorizontalBlock"] {
            gap: 0;
            align-items: stretch;
        }
        .st-key-search_form [data-testid="stTextInput"] {
            margin-bottom: 0;
        }
        .st-key-search_form [data-baseweb="input"] {
            border-radius: 14px 0 0 14px;
            border: 1px solid rgba(49, 91, 61, 0.24);
            border-right: 0;
            background: #fcfbf7;
            box-shadow: none;
            transition: border-color 150ms ease, box-shadow 150ms ease;
        }
        .st-key-search_form [data-baseweb="select"] > div {
            min-height: 3.65rem;
            border-radius: 14px 0 0 14px;
            border: 1px solid rgba(49, 91, 61, 0.24);
            border-right: 0;
            background: #fcfbf7;
            box-shadow: none;
            transition: border-color 150ms ease, box-shadow 150ms ease;
        }
        .st-key-search_form [data-baseweb="input"]:hover {
            border-color: rgba(49, 91, 61, 0.38);
            border-right: 0;
        }
        .st-key-search_form [data-baseweb="select"] > div:hover {
            border-color: rgba(49, 91, 61, 0.38);
            border-right: 0;
        }
        .st-key-search_form [data-baseweb="input"]:focus-within {
            border-color: #3f5b44;
            border-right: 0;
            box-shadow: 0 0 0 2px rgba(63, 91, 68, 0.12);
        }
        .st-key-search_form [data-baseweb="select"]:focus-within > div {
            border-color: #3f5b44;
            border-right: 0;
            box-shadow: 0 0 0 2px rgba(63, 91, 68, 0.12);
        }
        .st-key-search_form .stButton button {
            min-height: 3.65rem;
            border-radius: 0 14px 14px 0;
            padding: 0 1.35rem;
            font-weight: 700;
            box-shadow: none;
        }
        .st-key-search_filter_control {
            margin-top: .55rem;
        }
        .st-key-search_filter_control [data-testid="stExpander"] {
            border: 0;
            background: transparent;
            box-shadow: none;
        }
        .st-key-search_filter_control [data-testid="stExpander"] details,
        .st-key-search_filter_control [data-testid="stExpander"] summary {
            border: 0;
            background: transparent;
        }
        .st-key-search_filter_control [data-testid="stExpander"] summary {
            width: fit-content;
            min-height: 2.15rem;
            padding: .3rem .65rem;
            color: #405248;
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.15);
            border-radius: 9px;
            font-size: .8rem;
            font-weight: 600;
        }
        .st-key-search_filter_control [data-testid="stExpander"] summary:hover {
            color: #315b3d;
            background: #f1f4ed;
            border-color: rgba(49, 91, 61, 0.24);
        }
        .st-key-search_filter_control [data-testid="stExpanderDetails"] {
            margin-top: .65rem;
            padding: .75rem .05rem .05rem;
            border-top: 1px solid rgba(45, 70, 53, 0.10);
        }
        .st-key-search_summary {
            max-width: 760px;
            margin: 1rem 0 .25rem;
            padding: .75rem .95rem;
            color: #354b3b;
            background: #f1f4ed;
            border: 1px solid rgba(49, 91, 61, 0.11);
            border-radius: 14px;
        }
        .st-key-search_summary p { margin: 0; }
        .st-key-search_live_suggestions {
            max-width: 760px;
            margin: -.35rem 0 .8rem;
        }
        .st-key-search_live_suggestions .stButton button {
            justify-content: flex-start;
            min-height: 2.35rem;
            padding: .35rem .7rem;
            border-color: rgba(45, 70, 53, 0.10);
            background: #fcfbf7;
            color: #315b3d;
            font-weight: 500;
        }
        [class*="st-key-search_card_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: .65rem .9rem .55rem;
            margin-bottom: .55rem;
        }
        [class*="st-key-search_card_"] p { margin-bottom: .15rem; }
        [class*="st-key-search_card_"] .stButton button {
            justify-content: flex-start;
            min-height: 2rem;
            padding: 0;
            border: 0;
            background: transparent;
            color: #315b3d;
            font-size: 1rem;
        }
        .st-key-recent_result_stack {
            width: min(100%, 520px);
        }
        [class*="st-key-recent_result_"] {
            position: relative;
            width: 100%;
            margin: 0 0 .45rem 0;
        }
        [class*="st-key-recent_result_"] .recent-card-body {
            min-height: 80px;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: .02rem;
            padding: .55rem 2.5rem .55rem .9rem;
            overflow: hidden;
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.11);
            border-radius: 15px;
            box-shadow: 0 1px 2px rgba(36, 54, 43, 0.04);
            transition: transform 150ms ease, box-shadow 150ms ease,
                        border-color 150ms ease, background 150ms ease;
        }
        [class*="st-key-recent_result_"] .recent-card-supplier {
            color: #24362b;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.25;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        [class*="st-key-recent_result_"] .recent-card-number {
            color: #59675e;
            font-size: .82rem;
            line-height: 1.2;
        }
        [class*="st-key-recent_result_"] .recent-card-purchase {
            color: #66736b;
            font-size: .83rem;
            line-height: 1.25;
        }
        [class*="st-key-recent_result_"] .recent-card-amount {
            color: #315b3d;
            font-weight: 750;
        }
        [class*="st-key-recent_result_"] .recent-card-type {
            color: #7a857e;
            font-size: .69rem;
            line-height: 1.15;
        }
        [class*="st-key-recent_result_"] .recent-card-chevron {
            position: absolute;
            right: .95rem;
            top: 50%;
            transform: translateY(-50%);
            color: #9aa39d;
            font-size: 1.15rem;
            transition: color 150ms ease, transform 150ms ease;
        }
        [class*="st-key-recent_result_"] .stButton {
            position: absolute;
            inset: 0;
            z-index: 2;
        }
        [class*="st-key-recent_result_"] .stButton > div,
        [class*="st-key-recent_result_"] .stButton button {
            width: 100%;
            height: 100%;
        }
        [class*="st-key-recent_result_"] .stButton button {
            min-height: 80px;
            padding: 0;
            cursor: pointer;
            opacity: 0;
        }
        [class*="st-key-recent_result_"]:has(.stButton button:hover) .recent-card-body {
            transform: translateY(-2px);
            background: #fffefa;
            border-color: rgba(49, 91, 61, 0.22);
            box-shadow: 0 7px 18px rgba(36, 54, 43, 0.10);
        }
        [class*="st-key-recent_result_"]:has(.stButton button:hover) .recent-card-chevron {
            color: #315b3d;
            transform: translate(2px, -50%);
        }
        [class*="st-key-recent_result_"]:has(.stButton button:focus-visible) .recent-card-body {
            outline: 3px solid rgba(49, 91, 61, 0.22);
            outline-offset: 2px;
        }
        .search-section-label {
            color: #6f7b73;
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .09em;
            margin: 1.45rem 0 .55rem;
        }
        .search-detail {
            background: #f8f4ea;
            border: 1px solid rgba(45, 70, 53, 0.11);
            border-radius: 18px;
            padding: 1rem 1.2rem .7rem;
        }
        .st-key-search_detail_shell {
            max-width: 1040px;
            margin-top: 1rem;
        }
        .st-key-search_detail_metadata {
            background: #f8f4ea;
            border: 1px solid rgba(45, 70, 53, 0.11);
            border-radius: 18px;
            padding: 1rem 1.15rem .55rem;
            margin-bottom: 1rem;
        }
        .st-key-invoice_insights {
            background: #f1f4ed;
            border: 1px solid rgba(49, 91, 61, 0.12);
            border-radius: 16px;
            padding: .85rem 1rem .65rem;
            margin-bottom: 1rem;
        }
        .st-key-invoice_insights h3 {
            margin: 0 0 .35rem;
            font-size: 1rem;
        }
        .st-key-invoice_insights [data-testid="stMarkdownContainer"] p {
            margin-bottom: .38rem;
            color: #405248;
            font-size: .88rem;
            line-height: 1.4;
        }
        [class*="st-key-invoice_insight_"] {
            background: rgba(252, 251, 247, 0.72);
            border: 1px solid rgba(49, 91, 61, 0.09);
            border-radius: 12px;
            padding: .55rem .7rem .42rem;
            margin-bottom: .45rem;
        }
        [class*="st-key-invoice_insight_"] p:first-child {
            margin-bottom: .12rem;
            color: #24362b;
        }
        .st-key-invoice_preview {
            max-width: 900px;
            margin-bottom: .55rem;
        }
        .st-key-invoice_preview img {
            max-height: 460px;
            object-fit: contain;
            object-position: left top;
        }
        .st-key-search_detail_shell h3 {
            margin-top: 1rem;
        }
        .st-key-search_detail_shell [data-testid="stExpander"] {
            margin-top: .35rem;
        }
        .search-empty {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 18px;
            padding: 1.2rem 1.35rem;
            margin-top: 1.2rem;
        }
        .st-key-search_filters [data-testid="stVerticalBlock"] {
            gap: .55rem;
        }
        .st-key-search_filters [data-testid="stHorizontalBlock"] {
            gap: .65rem;
        }
        .st-key-search_filters [data-testid="stWidgetLabel"] {
            margin-bottom: .12rem;
        }
        .st-key-search_filters [data-testid="stSelectbox"],
        .st-key-search_filters [data-testid="stTextInput"],
        .st-key-search_filters [data-testid="stMultiSelect"],
        .st-key-search_filters [data-testid="stNumberInput"] {
            margin-bottom: 0;
        }
        .st-key-search_suggestions {
            width: min(100%, 620px);
            margin: -.1rem 0 .75rem;
        }
        .st-key-search_suggestions [data-testid="stHorizontalBlock"] {
            gap: .45rem;
        }
        .st-key-search_suggestions .stButton button {
            min-height: 1.95rem;
            padding: .25rem .65rem;
            border-radius: 9px;
            background: transparent;
            border-color: rgba(49, 91, 61, 0.12);
            color: #59675e;
            font-size: .77rem;
            font-weight: 500;
        }
        .st-key-search_suggestions .stButton button:hover {
            background: #f1f4ed;
            border-color: rgba(49, 91, 61, 0.20);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _money(value: object) -> str:
    amount = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "Unknown amount" if pd.isna(amount) else f"₪{float(amount):,.2f}"


def _count_phrase(count: int, singular: str) -> str:
    return f"{count} {singular if count == 1 else singular + 's'}"


def _display_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return str(value or "Unknown date") if pd.isna(parsed) else parsed.strftime("%d %b %Y")


def _invoice_label(value: object) -> str:
    invoice_number = str(value or "").strip()
    return f"Invoice #{invoice_number}" if invoice_number else "No invoice number"


def _date_query(query: str, available: pd.DataFrame) -> tuple[str, str, str]:
    value = query.strip()
    exact = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", value)
    if exact:
        iso_date = exact.group(0)
        return iso_date, iso_date, iso_date

    lowered = value.casefold()
    month = next(
        (index for index, name in enumerate(calendar.month_name) if name and name.casefold() in lowered),
        0,
    )
    if not month:
        return "", "", ""

    year_match = re.search(r"\b(20\d{2})\b", value)
    if year_match:
        year = int(year_match.group(1))
    else:
        dates = pd.to_datetime(available.get("invoice_date"), errors="coerce")
        matching_years = dates[dates.dt.month == month].dt.year.dropna()
        year = int(matching_years.max()) if not matching_years.empty else date.today().year
    last_day = calendar.monthrange(year, month)[1]
    label = f"{calendar.month_name[month]} {year}"
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}", label


def _set_selection(kind: str, value: object) -> None:
    st.session_state.search_selected_kind = kind
    st.session_state.search_selected_value = value
    st.session_state.search_show_document = False


def _clear_selection() -> None:
    st.session_state.search_selected_kind = None
    st.session_state.search_selected_value = None
    st.session_state.search_show_document = False


def _open_business_memory() -> None:
    st.session_state.current_page = "Business Memory"


def _apply_search_suggestion(query: str) -> None:
    st.session_state.search_query = query
    st.session_state.search_memory_input = query
    _clear_selection()


def _open_live_suggestion(invoice_id: int) -> None:
    _set_selection("invoice", invoice_id)


def _format_memory_search_option(value: SearchSuggestion | str) -> str:
    if isinstance(value, SearchSuggestion):
        return f"{value.label} · {value.kind}"
    return str(value)


def _apply_memory_search_input() -> None:
    value = st.session_state.get("search_memory_input")
    if isinstance(value, SearchSuggestion):
        st.session_state.search_query = value.label
        _open_live_suggestion(value.invoice_id)
        return
    st.session_state.search_query = str(value or "").strip()
    _clear_selection()


def _submit_memory_search() -> None:
    _apply_memory_search_input()


def _search_summary(
    query: str,
    results: pd.DataFrame,
    supplier_matches: list[str],
    products: list[dict],
) -> str:
    if results.empty:
        return "I couldn't find any matching invoices."
    exact_supplier = next(
        (name for name in supplier_matches if name.casefold() == query.casefold()),
        None,
    )
    if exact_supplier:
        count = int((results["supplier"] == exact_supplier).sum())
        return f"I found {count} {'invoice' if count == 1 else 'invoices'} from {exact_supplier}."
    purchase_count = sum(len(product["purchases"]) for product in products)
    if query and purchase_count:
        return f"I found {purchase_count} {query} {'purchase' if purchase_count == 1 else 'purchases'}."
    count = len(results)
    return f"I found {count} {'invoice' if count == 1 else 'invoices'} matching your search."


def _section_label(label: str) -> None:
    st.markdown(f'<div class="search-section-label">{label}</div>', unsafe_allow_html=True)


def _result_card(key: str, title: str, lines: list[str], kind: str, value: object) -> None:
    with st.container(key=f"search_card_{key}"):
        if st.button(title, key=f"open_{key}", width="stretch"):
            _set_selection(kind, value)
            st.rerun()
        for line in lines:
            st.caption(line)


def _recent_invoice_card(invoice: pd.Series) -> None:
    invoice_id = int(invoice["id"])
    supplier = str(invoice.get("supplier") or "Missing supplier")
    invoice_label = _invoice_label(invoice.get("invoice_number"))
    invoice_date = _display_date(invoice.get("invoice_date"))
    amount = _money(invoice.get("total"))
    document_type = str(invoice.get("document_type") or "Document type unavailable")
    with st.container(key=f"recent_result_{invoice_id}"):
        st.markdown(
            f"""
            <div class="recent-card-body" aria-hidden="true">
              <div class="recent-card-supplier">{html.escape(supplier)}</div>
              <div class="recent-card-number">{html.escape(invoice_label)}</div>
              <div class="recent-card-purchase">
                {html.escape(invoice_date)} •
                <span class="recent-card-amount">{html.escape(amount)}</span>
              </div>
              <div class="recent-card-type">{html.escape(document_type)}</div>
              <div class="recent-card-chevron" aria-hidden="true">›</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            f"Open {supplier}, {invoice_label}",
            key=f"open_recent_{invoice_id}",
            help=f"Open {supplier}",
        ):
            _set_selection("invoice", invoice_id)
            st.rerun()


def _matching_products(results: pd.DataFrame, query: str) -> list[dict]:
    if results.empty or not query.strip():
        return []
    matches: dict[str, list[dict]] = {}
    for _, invoice in results.iterrows():
        for _, item in invoice_items(int(invoice["id"])).iterrows():
            description = str(item.get("description") or "").strip()
            code = str(item.get("item_code") or "").strip()
            canonical_name = str(item.get("canonical_product_name") or "").strip()
            if not any(
                contains_search_match(value, query)
                for value in (description, code, canonical_name)
            ):
                continue
            matches.setdefault(canonical_name or description or code or "Product", []).append(
                {**item.to_dict(), "invoice": invoice.to_dict()}
            )

    products = []
    for name, rows in matches.items():
        rows.sort(key=lambda row: str(row["invoice"].get("invoice_date") or ""), reverse=True)
        latest = rows[0]
        products.append({"name": name, "latest": latest, "purchases": rows})
    return sorted(products, key=lambda product: product["name"].casefold())[:12]


def _render_invoice_thinking(
    invoice: pd.Series,
    items: pd.DataFrame,
    all_invoices: pd.DataFrame,
) -> None:
    thinking = think_about_invoice(
        invoice.to_dict(),
        items.to_dict("records"),
        all_invoices.to_dict("records"),
    )
    render_barni_thinking(
        thinking,
        key_prefix="invoice_detail",
        on_open_evidence=lambda invoice_id: _set_selection("invoice", invoice_id),
    )


def _render_invoice_detail(invoice: pd.Series, all_invoices: pd.DataFrame) -> None:
    invoice_id = int(invoice["id"])
    items = invoice_items(invoice_id)
    invoice_number = str(invoice.get("invoice_number") or "").strip()
    title = f"Invoice #{invoice_number}" if invoice_number else "No invoice number"

    with st.container(key="search_detail_shell"):
        st.button("← Back to search", key=f"back_from_invoice_{invoice_id}", on_click=_clear_selection)
        st.markdown(f"## {invoice.get('supplier') or 'Missing supplier'}")
        st.caption(f"{title} · {invoice.get('document_type') or 'Invoice'}")

        _render_invoice_thinking(invoice, items, all_invoices)

        st.markdown("### Original invoice")
        with st.container(key="invoice_preview"):
            _render_document_viewer(invoice, show_heading=False, height=440)

        st.markdown("### Key Invoice Information")
        with st.container(key="search_detail_metadata"):
            details = st.columns(4)
            details[0].markdown(f"**Invoice number**  \n{invoice_number or 'No invoice number'}")
            details[1].markdown(f"**Date**  \n{_display_date(invoice.get('invoice_date'))}")
            details[2].markdown(f"**Total**  \n{_money(invoice.get('total'))}")
            lifecycle = database_record_lifecycle(invoice.to_dict())
            status_label = (
                STATUS_LABELS[lifecycle.customer_state]
                if lifecycle.customer_state is not None
                else "Not in active workflow"
            )
            details[3].markdown(f"**Status**  \n{status_label}")

        st.markdown("### Products")
        if items.empty:
            st.caption("No extracted items are stored for this invoice.")
        else:
            product_view = items[["description", "quantity", "unit", "unit_price", "line_total"]].copy()
            st.dataframe(
                product_view,
                hide_index=True,
                width="stretch",
                height=min(330, 38 + (len(product_view) * 35)),
                column_config={
                    "description": "Product", "quantity": "Qty", "unit": "Unit",
                    "unit_price": st.column_config.NumberColumn("Price", format="₪%.2f"),
                    "line_total": st.column_config.NumberColumn("Total", format="₪%.2f"),
                },
            )

        with st.expander("Advanced Details", expanded=False):
            if st.button("View supplier", key=f"view_supplier_{invoice_id}", width="stretch"):
                _set_selection("supplier", str(invoice.get("supplier") or ""))
                st.rerun()
            _render_invoice_management(invoice)

        with st.expander("Technical Details", expanded=False):
            _render_invoice_technical(invoice, items)


def _render_document_viewer(
    invoice: pd.Series,
    *,
    show_heading: bool = True,
    height: int = 620,
) -> None:
    if show_heading:
        st.markdown("### Invoice document")
        st.caption("The original is contained here so you can keep your search context.")
    path = Path(str(invoice.get("archived_path") or ""))
    if not path.exists():
        st.info("The original document is not available to preview.")
        return
    if path.suffix.lower() == ".pdf":
        try:
            source_bytes = path.read_bytes()
        except OSError:
            st.info(
                "I couldn't open the original PDF. The saved invoice details are still "
                "available; return to the results or try opening it again."
            )
            return
        st.download_button("Download PDF", source_bytes, path.name, "application/pdf")
        try:
            st.pdf(source_bytes, height=height)
        except Exception:
            st.info("I couldn't show the PDF preview here. Use Download PDF to open the original invoice.")
    else:
        st.image(str(path), width="stretch")


def _render_invoice_management(invoice: pd.Series) -> None:
    invoice_id = int(invoice["id"])
    edit_tab, tags_tab = st.tabs(["Edit", "Tags"])
    with edit_tab:
        with st.form(f"database_edit_{invoice_id}"):
            col1, col2 = st.columns(2)
            supplier = col1.text_input("Supplier", value=str(invoice.get("supplier") or ""))
            supplier_id = col2.text_input("Supplier ID", value=str(invoice.get("supplier_id") or ""))
            invoice_number = col1.text_input("Invoice number", value=str(invoice.get("invoice_number") or ""))
            invoice_date = col2.text_input("Date", value=str(invoice.get("invoice_date") or ""))
            tax_options = ["חייב במע״מ", "פטור ממע״מ", "מעורב", "לא רלוונטי", "לא ברור"]
            current_tax = str(invoice.get("tax_treatment") or "לא ברור")
            tax_treatment = col1.selectbox(
                "VAT treatment", tax_options,
                index=tax_options.index(current_tax) if current_tax in tax_options else 4,
            )
            taxable_amount = col2.number_input(
                "Taxable amount", value=float(invoice.get("taxable_amount") or 0.0)
            )
            exempt_amount = col1.number_input(
                "VAT-exempt amount", value=float(invoice.get("exempt_amount") or 0.0)
            )
            vat = col2.number_input("VAT", value=float(invoice.get("vat") or 0.0))
            total = col1.number_input("Total", value=float(invoice.get("total") or 0.0))
            submitted = st.form_submit_button("Save changes", type="primary")
        if submitted:
            update_invoice(invoice_id, {
                "supplier": supplier, "supplier_id": supplier_id,
                "invoice_number": invoice_number, "invoice_date": invoice_date,
                "tax_treatment": tax_treatment, "taxable_amount": taxable_amount,
                "exempt_amount": exempt_amount, "vat": vat, "total": total,
            })
            st.success("Changes saved.")
            st.rerun()
    with tags_tab:
        current_tags = invoice_tags(invoice_id)
        tags_input = st.multiselect(
            "Tags", options=sorted(set(all_tags() + current_tags)), default=current_tags,
            accept_new_options=True,
        )
        if st.button("Save tags", key=f"save_tags_{invoice_id}"):
            set_invoice_tags(invoice_id, tags_input)
            st.success("Tags saved.")
            st.rerun()


def _render_invoice_technical(invoice: pd.Series, items: pd.DataFrame) -> None:
    invoice_id = int(invoice["id"])
    raw_text = str(invoice.get("raw_text") or "").strip()
    item_tab, history_tab, ocr_tab = st.tabs(["Product details", "History", "OCR text"])
    with item_tab:
        if items.empty:
            st.caption("No product lines are stored for this invoice.")
        else:
            st.dataframe(
                items,
                hide_index=True,
                width="stretch",
                column_config={
                    "item_code": "Product code", "description": "Description",
                    "quantity": "Quantity", "unit": "Unit",
                    "unit_price": st.column_config.NumberColumn("Unit price", format="₪%.2f"),
                    "line_total": st.column_config.NumberColumn("Line total", format="₪%.2f"),
                    "line_type": "Line type",
                },
            )
    with history_tab:
        history = invoice_history(invoice_id)
        if history.empty:
            st.caption("No recorded changes yet.")
        else:
            st.dataframe(history, hide_index=True, width="stretch")
    with ocr_tab:
        if raw_text:
            st.text(raw_text)
        else:
            st.caption("No OCR text is stored for this invoice.")


def _render_supplier_detail(name: str, results: pd.DataFrame) -> None:
    invoices = results[results["supplier"].fillna("").astype(str) == name]
    if invoices.empty:
        invoices = search_invoices(supplier_query=name, statuses=[])
    st.markdown(f"### {name or 'Missing supplier'}")
    st.caption(
        f"{len(invoices)} invoices · Last purchase: "
        f"{_display_date(invoices['invoice_date'].max()) if not invoices.empty else '—'}"
    )
    for _, invoice in invoices.head(8).iterrows():
        _result_card(
            f"supplier_invoice_{int(invoice['id'])}",
            _invoice_label(invoice.get("invoice_number")),
            [_display_date(invoice.get("invoice_date")), _money(invoice.get("total"))],
            "invoice", int(invoice["id"]),
        )


def _render_product_detail(product: dict) -> None:
    latest = product["latest"]
    st.markdown(f"### {product['name']}")
    st.caption(
        f"Latest price: {_money(latest.get('unit_price'))} · "
        f"Supplier: {latest['invoice'].get('supplier') or 'Missing supplier'}"
    )
    for row in product["purchases"][:8]:
        invoice = row["invoice"]
        _result_card(
            f"product_invoice_{int(invoice['id'])}",
            _invoice_label(invoice.get("invoice_number")),
            [_display_date(invoice.get("invoice_date")), _money(row.get("unit_price"))],
            "invoice", int(invoice["id"]),
        )


def _render_empty_state() -> None:
    st.markdown(
        """
        <div class="search-empty">
          Try a supplier name · Try a product · Try an invoice number · Try a date
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_database_archive() -> None:
    _render_search_styles()
    render_page_header(
        "Search",
        "Search suppliers, products, invoices or dates.",
        key="search",
    )

    st.session_state.setdefault("search_query", "")
    all_supplier_names = suppliers()
    identities = BusinessIdentityRepository()
    identities.sync_existing_memory()
    memory_catalog = search_suggestion_catalog(search_suggestion_rows())
    with primary_workspace(key="search"):
        with st.container(key="search_form"):
            search_field, search_action = st.columns([6, 1.15], gap="small")
            search_field.selectbox(
                "Search",
                memory_catalog,
                index=None,
                key="search_memory_input",
                placeholder="Search invoices, suppliers, products or dates...",
                label_visibility="collapsed",
                accept_new_options=True,
                filter_mode="fuzzy",
                format_func=_format_memory_search_option,
                on_change=_apply_memory_search_input,
            )
            search_action.button(
                "Search",
                type="primary",
                width="stretch",
                on_click=_submit_memory_search,
            )
            query = str(st.session_state.get("search_query") or "").strip()

        with st.container(key="search_filter_control"):
            with st.expander(
                "Advanced filters",
                expanded=False,
                icon=":material/tune:",
            ):
                with st.container(key="search_filters"):
                    row0 = st.columns(4)
                    supplier_choice = row0[0].selectbox(
                        "Supplier",
                        ["All suppliers"] + all_supplier_names,
                    )
                    invoice_query = row0[1].text_input(
                        "Invoice number",
                        autocomplete="off",
                    )
                    selected_tags = row0[2].multiselect("Tags", options=all_tags())
                    document_types = row0[3].multiselect(
                        "Document type",
                        DOCUMENT_TYPES,
                    )

                    row1 = st.columns([1.25, 1.15, .8, .95, 1, 1, 1, 1])
                    statuses = row1[0].multiselect(
                        "Status",
                        ["approved", "review", "rejected"],
                        default=["approved"],
                        format_func=database_status_label,
                    )
                    sort_label = row1[1].selectbox(
                        "Sort by",
                        ["Date", "Supplier", "Amount", "Invoice number"],
                    )
                    descending = row1[2].toggle("Newest first", value=True)
                    date_mode = row1[3].checkbox("Date range")
                    start_date = row1[4].date_input("From", disabled=not date_mode)
                    end_date = row1[5].date_input("To", disabled=not date_mode)
                    min_total = row1[6].number_input(
                        "Minimum",
                        value=0.0,
                        step=1.0,
                    )
                    max_total = row1[7].number_input(
                        "Maximum",
                        value=10_000_000.0,
                        step=100.0,
                    )

    if query and st.session_state.get("search_selected_kind") is None:
        live_suggestions = build_search_suggestions(query, search_suggestion_rows())
        if live_suggestions:
            with st.container(key="search_live_suggestions"):
                st.caption("Suggestions")
                for index, suggestion in enumerate(live_suggestions):
                    detail = f" · {suggestion.detail}" if suggestion.detail else ""
                    st.button(
                        f"{suggestion.kind} · {suggestion.label}{detail}",
                        key=f"open_live_suggestion_{index}_{suggestion.invoice_id}",
                        on_click=_open_live_suggestion,
                        args=(suggestion.invoice_id,),
                        width="stretch",
                    )

    if not query:
        with st.container(key="search_suggestions"):
            st.caption("Suggested searches")
            product_names = [value.canonical_name for value in identities.products()]
            supplier_names = suppliers()
            suggestions = _memory_suggestions(product_names, supplier_names)
            suggestion_columns = st.columns(max(1, len(suggestions)))
            for index, suggestion in enumerate(suggestions):
                suggestion_columns[index].button(
                    suggestion,
                    key=f"search_suggestion_{index}",
                    on_click=_apply_search_suggestion,
                    args=(suggestion,),
                    width="stretch",
                )

    has_filters = any([
        supplier_choice != "All suppliers", invoice_query.strip(), selected_tags,
        document_types, date_mode, min_total > 0, max_total < 10_000_000,
    ])

    if st.session_state.get("search_selected_kind") == "invoice":
        selected_id = int(st.session_state.get("search_selected_value"))
        invoice_memory = search_invoices(statuses=[])
        selected_rows = invoice_memory[invoice_memory["id"] == selected_id]
        if not selected_rows.empty:
            _render_invoice_detail(selected_rows.iloc[0], invoice_memory)
            return
        _clear_selection()

    if not query and not has_filters:
        recent = search_invoices(statuses=statuses).head(5)
        _section_label("RECENT INVOICES")
        if recent.empty:
            st.caption("No invoices yet. Your recent invoices will appear here.")
        with st.container(key="recent_result_stack"):
            for _, invoice in recent.iterrows():
                _recent_invoice_card(invoice)
        if not recent.empty:
            st.button(
                "Open Business Memory",
                key="search_to_memory_default",
                on_click=_open_business_memory,
            )
        return

    all_invoices = search_invoices(statuses=[])
    query_start, query_end, period_label = _date_query(query, all_invoices)
    matched_doc_types = [
        kind for kind in DOCUMENT_TYPES if contains_search_match(kind, query)
    ] if query else []
    text_query = "" if query_start or matched_doc_types else query
    sort_map = {"Date": "invoice_date", "Supplier": "supplier", "Amount": "total", "Invoice number": "invoice_number"}
    results = search_invoices(
        free_text=text_query,
        supplier_query="" if supplier_choice == "All suppliers" else supplier_choice,
        invoice_number=invoice_query.strip(),
        document_types=document_types or matched_doc_types,
        statuses=statuses,
        tags=selected_tags,
        start_date=start_date.isoformat() if date_mode and start_date else query_start,
        end_date=end_date.isoformat() if date_mode and end_date else query_end,
        min_total=min_total,
        max_total=max_total,
        sort_by=sort_map[sort_label],
        descending=descending,
    )

    products = _matching_products(results, query) if text_query else []
    supplier_matches = []
    if query:
        supplier_matches = [
            name for name in all_supplier_names if contains_search_match(name, query)
        ]

    with st.container(key="search_summary"):
        st.write(_search_summary(query, results, supplier_matches, products))

    if results.empty:
        _render_empty_state()
        return

    if supplier_matches:
        _section_label("SUPPLIERS")
        for index, name in enumerate(supplier_matches[:8]):
            supplier_invoices = search_invoices(supplier_query=name, statuses=statuses)
            _result_card(
                f"supplier_{index}", name,
                [_count_phrase(len(supplier_invoices), "invoice"),
                 f"Last purchase: {_display_date(supplier_invoices['invoice_date'].max())}"],
                "supplier", name,
            )

    ocr_matches = pd.DataFrame()
    if "raw_text" in results.columns and query:
        ocr_matches = results[
            results["raw_text"].fillna("").astype(str).map(
                lambda value: contains_search_match(value, query)
            )
        ]
    invoice_results = results
    if not ocr_matches.empty:
        invoice_results = results[~results["id"].isin(ocr_matches["id"])]

    if not invoice_results.empty:
        _section_label("INVOICES")
    if period_label:
        st.caption(f"{period_label} · {len(results)} invoices")
    for _, invoice in invoice_results.head(30).iterrows():
        _result_card(
            f"invoice_{int(invoice['id'])}",
            _invoice_label(invoice.get("invoice_number")),
            [str(invoice.get("supplier") or "Missing supplier"),
             f"{_display_date(invoice.get('invoice_date'))} · {_money(invoice.get('total'))}"],
            "invoice", int(invoice["id"]),
        )

    if products:
        _section_label("PRODUCTS")
        for index, product in enumerate(products):
            latest = product["latest"]
            _result_card(
                f"product_{index}", product["name"],
                [f"Latest price: {_money(latest.get('unit_price'))}",
                 f"Supplier: {latest['invoice'].get('supplier') or 'Missing supplier'}"],
                "product", product["name"],
            )

    if not ocr_matches.empty:
        _section_label("OCR MATCHES")
        for _, invoice in ocr_matches.head(12).iterrows():
            _result_card(
                f"ocr_{int(invoice['id'])}",
                _invoice_label(invoice.get("invoice_number")),
                [str(invoice.get("supplier") or "Missing supplier"),
                 f"{_display_date(invoice.get('invoice_date'))} · {_money(invoice.get('total'))}"],
                "invoice", int(invoice["id"]),
            )

    selected_kind = st.session_state.get("search_selected_kind")
    selected_value = st.session_state.get("search_selected_value")
    if selected_kind == "supplier":
        st.write("")
        _render_supplier_detail(str(selected_value), all_invoices)
    elif selected_kind == "product":
        product = next((item for item in products if item["name"] == selected_value), None)
        if product:
            st.write("")
            _render_product_detail(product)

    st.button(
        "Open Business Memory",
        key="search_to_memory_results",
        on_click=_open_business_memory,
    )
