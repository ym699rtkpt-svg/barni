from __future__ import annotations

import pandas as pd
import streamlit as st

from services.business_memory import (
    business_memory_data, product_memory_history, product_memory_options,
    supplier_memory_history, supplier_memory_options,
)
from services.business_identity import BusinessIdentityRepository
from services.identity_review import IdentityReviewService


def _render_memory_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-memory_hero {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.45rem 1.65rem;
        }
        [class*="st-key-memory_metric_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.75rem 1rem;
        }
        .st-key-memory_progress,
        .st-key-memory_growth {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 18px;
            padding: 1rem 1.2rem;
        }
        [class*="st-key-memory_category_"] {
            background: #f8f8f4;
            border: 1px solid rgba(45, 70, 53, 0.09);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
        }
        [class*="st-key-memory_recent_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.09);
            border-radius: 16px;
            padding: 0.9rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value: str, caption: str, key: str) -> None:
    with st.container(key=key):
        st.metric(label, value)
        st.caption(caption)


def _display_date(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%d %b %Y") if pd.notna(parsed) else "Date unavailable"


def _has_meaningful_growth(growth: pd.DataFrame) -> bool:
    if growth.empty or "date" not in growth.columns:
        return False
    dates = pd.to_datetime(growth["date"], errors="coerce").dropna()
    return dates.dt.normalize().nunique() >= 2


def _meaningful_categories(categories: pd.DataFrame) -> pd.DataFrame:
    """Suppress category presentation when unknown records are the majority."""
    if categories.empty or not {"category", "count"}.issubset(categories.columns):
        return categories.iloc[0:0].copy()
    values = categories.copy()
    normalized = values["category"].fillna("").astype(str).str.strip().str.casefold()
    unknown = normalized.isin({"", "לא מסווג", "uncategorized", "not classified"})
    unknown_count = int(pd.to_numeric(values.loc[unknown, "count"], errors="coerce").fillna(0).sum())
    meaningful = values[~unknown].copy()
    meaningful_count = int(pd.to_numeric(meaningful["count"], errors="coerce").fillna(0).sum())
    return meaningful if meaningful_count > unknown_count else meaningful.iloc[0:0]


def _open_invoice(invoice_id: int) -> None:
    st.session_state.search_selected_kind = "invoice"
    st.session_state.search_selected_value = int(invoice_id)
    st.session_state.search_show_document = False
    st.session_state.current_page = "חיפוש חשבוניות"


def _open_accountant_workspace() -> None:
    st.session_state.current_page = "Accountant Workspace"


def _open_feed() -> None:
    st.session_state.current_page = "קליטה יומית"


def _render_memory_drill_down() -> None:
    st.markdown("### Explore Business Memory")
    st.caption("Open the history behind Barni's suppliers, products and prices.")
    supplier_tab, product_tab = st.tabs(["Supplier history", "Product & price history"])

    with supplier_tab:
        supplier_names = supplier_memory_options()
        if not supplier_names:
            st.caption("No supplier history yet.")
        else:
            selected_supplier = st.selectbox("Supplier", supplier_names, key="memory_supplier")
            history = supplier_memory_history(selected_supplier)
            if history.empty:
                st.caption("No approved invoices are connected to this supplier yet.")
            for _, invoice in history.head(10).iterrows():
                number = str(invoice.get("invoice_number") or "No invoice number")
                total = invoice.get("total")
                total_text = f"₪{float(total):,.2f}" if pd.notna(total) else "Unknown amount"
                st.button(
                    f"{_display_date(invoice.get('invoice_date'))} · {number} · {total_text}",
                    key=f"memory_supplier_invoice_{int(invoice['id'])}",
                    on_click=_open_invoice,
                    args=(int(invoice["id"]),),
                )

    with product_tab:
        product_names = product_memory_options()
        if not product_names:
            st.caption("No product history yet.")
        else:
            selected_product = st.selectbox("Product", product_names, key="memory_product")
            history = product_memory_history(selected_product)
            if history.empty:
                st.caption("This product does not have a comparable price history yet.")
            else:
                visible = history.head(12)
                st.dataframe(
                    visible[["invoice_date", "supplier", "unit_price", "quantity"]],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "invoice_date": "Date", "supplier": "Supplier",
                        "unit_price": st.column_config.NumberColumn("Price", format="₪%.2f"),
                        "quantity": "Quantity",
                    },
                )
                for invoice_id in visible["invoice_id"].dropna().astype(int).drop_duplicates():
                    st.button(
                        f"Open source invoice #{invoice_id}",
                        key=f"memory_product_invoice_{invoice_id}",
                        on_click=_open_invoice,
                        args=(invoice_id,),
                    )


def _render_identity_trust() -> None:
    repository = BusinessIdentityRepository()
    health = repository.identity_health()
    review_count = IdentityReviewService(identity_repository=repository).queue_count()

    st.markdown("### What Barni needs help learning")
    if review_count:
        st.write(f"I found {review_count} identity question{'s' if review_count != 1 else ''} where your answer would make future comparisons more trustworthy.")
        if st.button("Help Barni learn", key="open_identity_review"):
            st.session_state.current_page = "Identity Review"
            st.rerun()
    else:
        st.caption("I don’t need help with any important identity right now.")
    st.caption(
        f"Barni currently remembers {health['suppliers']:,} canonical suppliers and "
        f"{health['products']:,} canonical products."
    )


def render_business_memory() -> None:
    _render_memory_styles()
    memory = business_memory_data()

    invoice_count = memory["invoice_count"]
    supplier_count = memory["supplier_count"]
    product_count = memory["product_count"]
    covered_count = memory["covered_product_count"]

    if invoice_count:
        memory_status = (
            f"Barni remembers {invoice_count:,} invoices, "
            f"{supplier_count:,} suppliers and {product_count:,} products."
        )
    else:
        memory_status = "Barni is ready to learn from the first invoice."

    with st.container(key="memory_hero"):
        st.caption("BARNI'S BRAIN")
        st.markdown("## Business Memory")
        st.write(memory_status)

    st.write("")
    st.markdown("### What Barni knows")
    st.caption("Knowledge stored from approved business documents")
    metrics = [
        ("Invoices learned", f"{invoice_count:,}", "Stored invoices"),
        ("Suppliers known", f"{supplier_count:,}", "Named suppliers"),
        ("Products known", f"{product_count:,}", "Real product lines"),
        (
            "Price history coverage",
            f"{covered_count:,} / {product_count:,}",
            "Products with 2+ valid prices",
        ),
    ]
    metric_columns = st.columns(4, gap="medium")
    for index, (column, (label, value, caption)) in enumerate(
        zip(metric_columns, metrics)
    ):
        with column:
            _metric_card(
                label,
                value,
                caption,
                key=f"memory_metric_{index}",
            )

    st.write("")
    _render_memory_drill_down()

    st.write("")
    st.markdown("### Learning progress")
    st.caption("How much repeat price history Barni can currently compare")
    with st.container(key="memory_progress"):
        coverage = covered_count / product_count if product_count else 0.0
        st.progress(coverage)
        if product_count:
            st.write(
                f"{covered_count:,} of {product_count:,} products have at least "
                "two valid stored prices."
            )
        else:
            st.caption("No product history yet. Feed Barni an invoice to begin.")

    st.write("")
    st.markdown("### Business categories")
    st.caption("How stored invoices are currently organized")
    categories = memory["categories"]
    visible_categories = _meaningful_categories(categories).head(6)
    if visible_categories.empty:
        st.caption(
            "Barni does not yet have enough reliable category information."
        )
    else:
        category_columns = st.columns(len(visible_categories), gap="small")
        for index, (column, (_, category)) in enumerate(
            zip(category_columns, visible_categories.iterrows())
        ):
            with column:
                with st.container(key=f"memory_category_{index}"):
                    st.markdown(f"**{category['category']}**")
                    st.caption(f"{int(category['count']):,} invoices")

    st.write("")
    st.markdown("### Knowledge growth over time")
    st.caption("Cumulative knowledge from stored invoices")
    growth = memory["growth"]
    if not _has_meaningful_growth(growth):
        st.caption(
            "Barni is still learning. Growth over time will appear after knowledge "
            "changes on more than one day."
        )
    else:
        with st.container(key="memory_growth"):
            st.line_chart(
                growth,
                x="date",
                y=["Invoices", "Suppliers", "Products"],
                height=280,
            )

    st.write("")
    st.markdown("### Recent things Barni learned")
    st.caption("The latest stored information added to business memory")
    recent = memory["recent"]
    if recent.empty:
        st.caption("Nothing learned yet.")
    else:
        for index, (_, invoice) in enumerate(recent.iterrows()):
            supplier = str(invoice.get("supplier") or "Supplier not specified")
            invoice_number = str(
                invoice.get("invoice_number") or "Number not specified"
            )
            product_lines = int(invoice.get("product_count") or 0)
            with st.container(key=f"memory_recent_{index}"):
                columns = st.columns([3, 1], vertical_alignment="center")
                with columns[0]:
                    st.markdown(f"**{supplier} · {invoice_number}**")
                    st.caption(
                        f"{product_lines:,} product lines learned"
                    )
                with columns[1]:
                    st.caption(_display_date(invoice.get("_learned_at")))

    st.write("")
    _render_identity_trust()

    st.write("")
    destination_label = "Prepare for accountant" if invoice_count else "Feed Barni"
    if st.button(
        destination_label,
        type="primary",
        width="stretch",
        key="memory_to_accountant",
        on_click=_open_accountant_workspace if invoice_count else _open_feed,
    ):
        st.rerun()
