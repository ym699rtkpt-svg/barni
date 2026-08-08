
from __future__ import annotations

import pandas as pd
import streamlit as st

from database import (
    product_price_change_summary,
    product_price_history,
    supplier_summary,
    suppliers,
)


def _render_knowledge_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-knowledge_header {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.35rem 1.55rem;
        }
        [class*="st-key-knowledge_metric_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.7rem 0.95rem;
        }
        .st-key-knowledge_intelligence,
        .st-key-knowledge_products,
        .st-key-knowledge_history,
        .st-key-knowledge_history_chart,
        .st-key-knowledge_history_table {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 18px;
            padding: 1rem 1.2rem;
        }
        [class*="st-key-knowledge_insight_"] {
            background: #f8f8f4;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            min-height: 8rem;
            padding: 1rem 1.1rem;
        }
        [class*="st-key-knowledge_recommendation_"] {
            background: #f7f4ec;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            min-height: 11rem;
            padding: 1rem 1.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value, key: str, caption: str = "") -> None:
    with st.container(key=key):
        st.metric(label, value)
        if caption:
            st.caption(caption)


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def _build_supplier_product_intelligence(
    items: pd.DataFrame,
    supplier: str,
) -> pd.DataFrame:
    grouped = (
        items.groupby("description")
        .agg(
            purchases=("description", "count"),
            quantity=("quantity", "sum"),
            average_price=("unit_price", "mean"),
            total=("line_total", "sum"),
        )
        .reset_index()
    )

    intelligence_columns = [
        "previous_price",
        "last_price",
        "price_difference",
        "price_change_pct",
        "latest_quantity",
        "savings_extra_cost",
    ]
    for column in intelligence_columns:
        grouped[column] = None
    grouped["latest_purchase_date"] = None

    for index, row in grouped.iterrows():
        price_summary = product_price_change_summary(
            row["description"], supplier=supplier
        )
        grouped.at[index, "previous_price"] = price_summary["previous_price"]
        grouped.at[index, "last_price"] = price_summary["current_price"]
        grouped.at[index, "price_difference"] = price_summary["price_difference"]
        grouped.at[index, "price_change_pct"] = price_summary["price_change_pct"]
        grouped.at[index, "latest_quantity"] = price_summary["latest_quantity"]
        grouped.at[index, "savings_extra_cost"] = price_summary[
            "savings_extra_cost"
        ]
        grouped.at[index, "latest_purchase_date"] = price_summary[
            "latest_purchase_date"
        ]

    for column in intelligence_columns:
        grouped[column] = pd.to_numeric(grouped[column], errors="coerce")

    grouped["trend"] = "⚪ unchanged"
    grouped.loc[grouped["price_difference"] > 0, "trend"] = "🔴 price increased"
    grouped.loc[grouped["price_difference"] < 0, "trend"] = "🟢 price decreased"
    return grouped


def _display_date(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%d %b %Y") if pd.notna(parsed) else "-"


def _render_supplier_invoices(documents: pd.DataFrame) -> None:
    if documents.empty:
        return

    with st.expander("כל החשבוניות"):
        document_table = documents[
            [
                "invoice_date",
                "invoice_number",
                "document_type",
                "category",
                "subcategory",
                "total",
                "vat",
                "status",
            ]
        ].copy()
        document_table["invoice_date"] = pd.to_datetime(
            document_table["invoice_date"], errors="coerce"
        )
        st.dataframe(
            document_table,
            hide_index=True,
            width="stretch",
            column_config={
                "invoice_date": st.column_config.DateColumn(
                    "תאריך", format="DD MMM YYYY"
                ),
                "invoice_number": "מספר",
                "document_type": "סוג",
                "category": "קטגוריה",
                "subcategory": "תת־קטגוריה",
                "total": st.column_config.NumberColumn("סה״כ", format="₪%.2f"),
                "vat": st.column_config.NumberColumn("מע״מ", format="₪%.2f"),
                "status": "סטטוס",
            },
        )


def render_suppliers_page():
    _render_knowledge_styles()
    st.markdown("## Knowledge")
    st.caption("מה Barni למד על הספקים, המוצרים והמחירים שלכם.")

    names = suppliers()
    if not names:
        st.markdown(
            '<div class="barni-empty-state">עדיין אין מספיק מידע על ספקים. העלו חשבונית כדי להתחיל לבנות את הידע העסקי.</div>',
            unsafe_allow_html=True,
        )
        return

    selected = st.selectbox(
        "בחר ספק",
        options=names,
    )

    summary = supplier_summary(selected)
    items = summary["items"]
    grouped = (
        _build_supplier_product_intelligence(items, selected)
        if not items.empty
        else pd.DataFrame()
    )

    comparable_changes = (
        grouped["price_change_pct"].dropna()
        if not grouped.empty
        else pd.Series(dtype=float)
    )
    supplier_is_stable = (
        not comparable_changes.empty
        and bool(comparable_changes.abs().le(2).all())
    )

    with st.container(key="knowledge_header"):
        st.markdown(f"### {selected}")
        st.caption("Supplier overview")
        if supplier_is_stable:
            st.markdown(
                "<span style='display:inline-block;padding:0.2rem 0.65rem;"
                "border:1px solid #d8dfce;border-radius:999px;"
                "background:#f3f5ef;color:#536246;font-size:0.8rem;'>"
                "Stable</span>",
                unsafe_allow_html=True,
            )

    st.write("")
    overview_cols = st.columns(4, gap="medium")
    overview_cards = [
        ("Invoices", summary["invoice_count"]),
        ("Total Purchases", f"₪{summary['total_spend']:,.2f}"),
        ("Average Invoice", f"₪{summary['average_invoice']:,.2f}"),
        ("Last Invoice", _display_date(summary["last_invoice_date"])),
    ]
    for index, (column, (label, value)) in enumerate(zip(overview_cols, overview_cards)):
        with column:
            _metric_card(
                label,
                value,
                key=f"knowledge_metric_overview_{index}",
                caption=(
                    f"מע״מ: ₪{summary['vat_total']:,.2f}"
                    if label == "Total Purchases"
                    else ""
                ),
            )

    if not grouped.empty:
        increased_count = int((grouped["price_difference"] > 0).sum())
        decreased_count = int((grouped["price_difference"] < 0).sum())
        cost_impact = grouped["savings_extra_cost"].dropna()
        potential_extra_cost = float(cost_impact[cost_impact > 0].sum())
        potential_savings = abs(float(cost_impact[cost_impact < 0].sum()))

        with st.container(key="knowledge_intelligence"):
            st.markdown("#### Supplier Intelligence")
            intelligence_cols = st.columns(4)
            intelligence_cols[0].metric("Products Increased", increased_count)
            intelligence_cols[1].metric("Products Decreased", decreased_count)
            intelligence_cols[2].metric(
                "Potential Extra Cost", f"₪{potential_extra_cost:,.2f}"
            )
            intelligence_cols[3].metric(
                "Potential Savings", f"₪{potential_savings:,.2f}"
            )

    if items.empty:
        st.write("")
        st.markdown("### Barni Insights")
        st.caption("What changed since previous purchases")
        st.caption("No significant supplier changes detected yet.")

        st.write("")
        st.markdown("### Barni Recommendations")
        st.caption("Actions worth considering")
        st.caption("No purchasing actions recommended yet.")

        st.write("")
        st.markdown("### Products from this supplier")
        st.caption("Current products and price movement")
        st.caption("No product lines yet.")
        _render_supplier_invoices(summary["documents"])

        st.write("")
        st.markdown("#### Product History")
        st.caption("Purchase and price history over time")
        st.caption("No product history available yet.")

    else:
        price_changes = grouped["price_change_pct"].dropna()
        up = int((price_changes > 0).sum())
        down = int((price_changes < 0).sum())
        average_change = float(price_changes.mean()) if not price_changes.empty else 0.0

        cols = st.columns(4, gap="medium")
        product_metrics = [
            ("Products Tracked", len(grouped)),
            ("Price Increases", up),
            ("Price Decreases", down),
            ("Average Change", f"{average_change:.2f}%"),
        ]
        for index, (column, (label, value)) in enumerate(zip(cols, product_metrics)):
            with column:
                _metric_card(
                    label,
                    value,
                    key=f"knowledge_metric_products_{index}",
                )

        insights = []
        increase_rows = grouped[grouped["price_difference"] > 0]
        if not increase_rows.empty:
            top_increase = increase_rows.sort_values(
                "price_change_pct", ascending=False
            ).iloc[0]
            insights.append(
                {
                    "icon": "🔺",
                    "title": "Price Increase",
                    "text": (
                        f"{top_increase['description']} increased by "
                        f"{top_increase['price_change_pct']:.1f}% compared to "
                        "the previous purchase."
                    ),
                }
            )

        decrease_rows = grouped[grouped["price_difference"] < 0]
        if not decrease_rows.empty:
            top_decrease = decrease_rows.sort_values(
                "price_difference", ascending=True
            ).iloc[0]
            insights.append(
                {
                    "icon": "🔻",
                    "title": "Price Decrease",
                    "text": (
                        f"{top_decrease['description']} dropped by "
                        f"₪{abs(top_decrease['price_difference']):,.2f} per unit."
                    ),
                }
            )

        latest_dates = pd.to_datetime(
            grouped["latest_purchase_date"], errors="coerce"
        )
        current_month = pd.Timestamp.now().to_period("M")
        increased_this_month = int(
            (
                (grouped["price_difference"] > 0)
                & (latest_dates.dt.to_period("M") == current_month)
            ).sum()
        )
        if increased_this_month:
            insights.append(
                {
                    "icon": "📊",
                    "title": "Monthly Supplier Movement",
                    "text": (
                        f"This supplier increased prices on "
                        f"{_count_phrase(increased_this_month, 'product')} this month."
                    ),
                }
            )

        if not insights:
            insights.append(
                {
                    "icon": "✅",
                    "title": "Stable Purchasing",
                    "text": "No supplier price movements require attention yet.",
                }
            )

        st.write("")
        st.markdown("### Barni Insights")
        st.caption("What changed since previous purchases")
        visible_insights = insights[:3]
        insight_cols = st.columns(len(visible_insights), gap="medium")
        for index, (column, insight) in enumerate(
            zip(insight_cols, visible_insights)
        ):
            with column:
                with st.container(key=f"knowledge_insight_{index}"):
                    st.caption(insight["title"])
                    st.write(insight["text"])

        recommendation_rows = grouped[
            (grouped["purchases"] > 1)
            & grouped["last_price"].notna()
            & grouped["previous_price"].notna()
            & grouped["price_change_pct"].notna()
            & (
                (grouped["price_change_pct"] >= 5)
                | (grouped["price_change_pct"] < -5)
            )
        ].copy()
        recommendation_rows["absolute_change"] = recommendation_rows[
            "price_change_pct"
        ].abs()
        recommendation_rows = recommendation_rows.sort_values(
            "absolute_change", ascending=False
        )

        recommendations = []
        for _, product in recommendation_rows.head(3).iterrows():
            change = float(product["price_change_pct"])
            if change > 10:
                title = "Review supplier price"
                action = (
                    f"Consider negotiating {product['description']} prices or "
                    "comparing quotes from an alternative supplier."
                )
            elif change >= 5:
                title = "Monitor price"
                action = "Keep monitoring this product on the next purchase."
            else:
                title = "Favorable price movement"
                action = "No action required."

            recommendations.append(
                {
                    "title": title,
                    "product": product["description"],
                    "current_price": float(product["last_price"]),
                    "previous_price": float(product["previous_price"]),
                    "change": change,
                    "action": action,
                }
            )

        st.write("")
        st.markdown("### Barni Recommendations")
        st.caption("Actions worth considering")
        if recommendations:
            recommendation_cols = st.columns(len(recommendations), gap="medium")
            for index, (column, recommendation) in enumerate(
                zip(recommendation_cols, recommendations)
            ):
                with column:
                    with st.container(
                        key=f"knowledge_recommendation_{index}"
                    ):
                        st.markdown(f"**{recommendation['title']}**")
                        st.write(
                            f"{recommendation['product']} changed from "
                            f"₪{recommendation['previous_price']:,.2f} to "
                            f"₪{recommendation['current_price']:,.2f} "
                            f"({recommendation['change']:+.1f}%)."
                        )
                        st.caption(recommendation["action"])
        else:
            st.caption("No purchasing actions recommended yet.")

        st.write("")
        st.markdown("### Products from this supplier")
        st.caption("Current products and price movement")
        product_table = grouped[
            [
                "description",
                "purchases",
                "quantity",
                "average_price",
                "total",
                "previous_price",
                "last_price",
                "price_difference",
                "price_change_pct",
                "savings_extra_cost",
                "trend",
            ]
        ]
        with st.container(key="knowledge_products"):
            st.dataframe(
                product_table,
                hide_index=True,
                width="stretch",
                column_order=[
                "description",
                "purchases",
                "quantity",
                "average_price",
                "previous_price",
                "last_price",
                "price_difference",
                "price_change_pct",
                "trend",
                ],
                column_config={
                "description": "Product",
                "purchases": "Purchases",
                "quantity": "Quantity",
                "average_price": st.column_config.NumberColumn(
                    "Average Price", format="₪%.2f"
                ),
                "total": st.column_config.NumberColumn(
                    "Total Purchased", format="₪%.2f"
                ),
                "previous_price": st.column_config.NumberColumn(
                    "Previous Price", format="₪%.2f"
                ),
                "last_price": st.column_config.NumberColumn(
                    "Latest Price", format="₪%.2f"
                ),
                "price_difference": st.column_config.NumberColumn(
                    "Price Change", format="₪%.2f"
                ),
                "price_change_pct": st.column_config.NumberColumn(
                    "Change", format="%.1f%%"
                ),
                "savings_extra_cost": st.column_config.NumberColumn(
                    "Savings / Extra Cost", format="₪%.2f"
                ),
                "trend": "Trend",
                },
            )

        st.write("")
        _render_supplier_invoices(summary["documents"])

        st.write("")
        st.markdown("#### Product History")
        st.caption("Purchase and price history over time")
        product_options = [
            description for description in grouped["description"].dropna().tolist()
        ]
        selected_product = st.selectbox(
            "View product history",
            options=product_options,
            key=f"product_history_{selected}",
        )

        history = product_price_history(selected_product)
        if history.empty:
            st.caption("No purchase history available for this product yet.")
        else:
            latest = history.iloc[-1]
            latest_price = (
                float(latest["unit_price"])
                if pd.notna(latest["unit_price"])
                else None
            )
            previous_price = (
                float(latest["previous_price"])
                if pd.notna(latest["previous_price"])
                else None
            )
            price_difference = (
                float(latest["price_difference"])
                if pd.notna(latest["price_difference"])
                else None
            )
            price_change_pct = (
                float(latest["price_change_pct"])
                if pd.notna(latest["price_change_pct"])
                else None
            )

            with st.container(key="knowledge_history"):
                st.markdown(f"#### {selected_product}")
                st.caption(
                    f"{len(history)} purchases · Latest on "
                    f"{_display_date(latest['invoice_date'])}"
                )
                detail_cols = st.columns(4, gap="medium")
                detail_metrics = [
                    (
                        "Latest price",
                        f"₪{latest_price:,.2f}" if latest_price is not None else "-",
                    ),
                    (
                        "Previous price",
                        f"₪{previous_price:,.2f}"
                        if previous_price is not None
                        else "-",
                    ),
                    (
                        "Price difference",
                        f"₪{price_difference:,.2f}"
                        if price_difference is not None
                        else "-",
                    ),
                    (
                        "Percentage change",
                        f"{price_change_pct:.1f}%"
                        if price_change_pct is not None
                        else "-",
                    ),
                ]
                for index, (column, (label, value)) in enumerate(
                    zip(detail_cols, detail_metrics)
                ):
                    with column:
                        _metric_card(
                            label,
                            value,
                            key=f"knowledge_metric_history_{index}",
                        )

            if len(history) == 1:
                st.caption("Barni needs another purchase to calculate a reliable trend.")
            elif latest_price is None or previous_price is None:
                st.caption("Price history is incomplete for this product.")
            else:
                st.caption("Barni is tracking the product's price trend across purchases.")

            st.markdown("##### Price history")
            history_chart = history[["invoice_date", "unit_price"]].copy()
            history_chart["invoice_date"] = pd.to_datetime(
                history_chart["invoice_date"], errors="coerce"
            )
            history_chart = history_chart.dropna(subset=["invoice_date", "unit_price"])
            if not history_chart.empty:
                with st.container(key="knowledge_history_chart"):
                    st.line_chart(
                        history_chart,
                        x="invoice_date",
                        y="unit_price",
                        height=240,
                    )
            else:
                st.caption("Price data is not available for this product yet.")

            display_columns = [
                "invoice_date",
                "supplier",
                "invoice_number",
                "quantity",
                "unit",
                "unit_price",
                "line_total",
            ]
            st.markdown("##### Purchase history")
            purchase_table = history[display_columns].rename(columns={
                "invoice_date": "Date",
                "supplier": "Supplier",
                "invoice_number": "Invoice number",
                "quantity": "Quantity",
                "unit": "Unit",
                "unit_price": "Unit price",
                "line_total": "Line total",
            }).copy()
            purchase_table["Date"] = pd.to_datetime(
                purchase_table["Date"], errors="coerce"
            )
            with st.container(key="knowledge_history_table"):
                st.dataframe(
                    purchase_table,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Date": st.column_config.DateColumn(format="DD MMM YYYY"),
                        "Unit price": st.column_config.NumberColumn(format="₪%.2f"),
                        "Line total": st.column_config.NumberColumn(format="₪%.2f"),
                    },
                )
