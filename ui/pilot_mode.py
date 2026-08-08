from __future__ import annotations

import pandas as pd
import streamlit as st

from services.pilot_support import (
    APP_VERSION,
    debug_export_bytes,
    pilot_dashboard_data,
    save_feedback,
)


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-pilot_hero {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.35rem 1.55rem;
        }
        [class*="st-key-pilot_metric_"],
        [class*="st-key-pilot_health_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.8rem 1rem;
        }
        .st-key-pilot_confidence,
        .st-key-pilot_errors {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 18px;
            padding: 1rem 1.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label: str, value, caption: str, key: str) -> None:
    with st.container(key=key):
        st.metric(label, value)
        st.caption(caption)


def _feedback_form(kind: str, title: str, prompt: str, current_page: str) -> None:
    with st.form(f"pilot_{kind}", clear_on_submit=True):
        st.markdown(f"#### {title}")
        message = st.text_area(prompt, height=120)
        contact = st.text_input("Contact details (optional)")
        submitted = st.form_submit_button("Save feedback", type="primary")
        if submitted:
            try:
                save_feedback(kind, message, current_page, contact)
            except ValueError as exc:
                st.warning(str(exc))
            else:
                st.success("Feedback saved on this Barni device for pilot review.")


def _render_dashboard() -> None:
    data = pilot_dashboard_data()

    st.markdown("### Pilot activity")
    st.caption("Upload quality comes from Feed Barni's stored processing queue.")
    activity_metrics = [
        ("Uploaded invoices", data["uploaded_invoices"], "All recorded Feed uploads"),
        (
            "Successfully processed",
            data["successfully_processed"],
            "Uploads with extracted document data",
        ),
        ("Failed invoices", data["failed_invoices"], "Processing failures"),
        ("Needs review", data["needs_review"], "Open uncertain invoices"),
    ]
    activity_columns = st.columns(4, gap="medium")
    for index, (column, (label, value, caption)) in enumerate(
        zip(activity_columns, activity_metrics)
    ):
        with column:
            _metric_card(label, value, caption, f"pilot_metric_activity_{index}")

    st.write("")
    st.markdown("### Business Memory learned")
    st.caption("Cumulative approved knowledge currently stored by Barni.")
    memory_metrics = [
        ("New suppliers learned", data["new_suppliers_learned"], "Known suppliers"),
        ("New products learned", data["new_products_learned"], "Real product lines"),
        ("New price points", data["new_price_points"], "Valid stored prices"),
        (
            "Duplicates detected",
            data["duplicate_invoices_detected"],
            "Tracked from this dashboard release",
        ),
    ]
    memory_columns = st.columns(4, gap="medium")
    for index, (column, (label, value, caption)) in enumerate(
        zip(memory_columns, memory_metrics)
    ):
        with column:
            _metric_card(label, value, caption, f"pilot_metric_memory_{index}")

    st.write("")
    st.markdown("### Health")
    health = data["health"]
    health_columns = st.columns(3, gap="medium")
    health_cards = [
        (
            "System Health",
            health["system"],
            f"Database schema {health['schema_version']} · "
            f"{len(data['recent_errors'])} recent logged errors",
        ),
        (
            "Data Quality",
            health["data_quality"],
            f"{data['needs_review']} need review · {data['failed_invoices']} failed",
        ),
        (
            "Business Memory Growth",
            health["business_memory"],
            f"{health['invoice_count']:,} invoices · Price coverage "
            f"{health['price_history_coverage']}",
        ),
    ]
    for index, (column, (label, value, caption)) in enumerate(
        zip(health_columns, health_cards)
    ):
        with column:
            _metric_card(label, value, caption, f"pilot_health_{index}")

    st.write("")
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.markdown("### OCR confidence distribution")
        st.caption("Only confidence stored by the existing extraction is shown.")
        distribution = pd.DataFrame(
            {
                "Range": list(data["confidence_distribution"].keys()),
                "Invoices": list(data["confidence_distribution"].values()),
            }
        )
        with st.container(key="pilot_confidence"):
            if distribution["Invoices"].sum() == 0:
                st.caption("No OCR confidence has been recorded yet.")
            else:
                st.bar_chart(distribution, x="Range", y="Invoices", height=260)

    with right:
        st.markdown("### Recent errors")
        st.caption("The latest locally logged runtime errors.")
        with st.container(key="pilot_errors"):
            if not data["recent_errors"]:
                st.caption("No runtime errors have been logged yet.")
            else:
                error_table = pd.DataFrame(
                    [
                        {
                            "Time": error.get("created_at", ""),
                            "Page": error.get("page", ""),
                            "Type": error.get("error_type", ""),
                            "Message": error.get("message", ""),
                        }
                        for error in reversed(data["recent_errors"])
                    ]
                )
                error_table["Time"] = pd.to_datetime(
                    error_table["Time"], errors="coerce"
                )
                st.dataframe(
                    error_table,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Time": st.column_config.DatetimeColumn(
                            format="DD MMM YYYY, HH:mm"
                        ),
                    },
                )

    with st.expander("Metric definitions"):
        st.caption(
            "Successfully processed means extraction produced document data. "
            "Learned metrics are cumulative approved Business Memory totals. "
            "Duplicate detections are counted from the pilot event log starting "
            "with this dashboard release. Stored duplicate groups currently in "
            f"Business Memory: {data['stored_duplicate_groups']}."
        )


def _render_feedback(current_page: str) -> None:
    problem_tab, improvement_tab = st.tabs(
        ["Report Problem", "Suggest Improvement"]
    )
    with problem_tab:
        _feedback_form(
            "problem",
            "What went wrong?",
            "Tell us what you expected and what happened.",
            current_page,
        )
    with improvement_tab:
        _feedback_form(
            "improvement",
            "What would make Barni better?",
            "Share one improvement that would help your work.",
            current_page,
        )


def _render_support() -> None:
    st.markdown("### Support information")
    st.caption(
        "The export contains version and technical health information. "
        "It excludes invoice contents, uploaded files, and credentials."
    )
    st.download_button(
        "Export Debug Information",
        data=debug_export_bytes(),
        file_name="barni-debug-alpha-0.3.json",
        mime="application/json",
    )
    st.caption(f"Current version · Barni {APP_VERSION}")


def render_pilot_mode(current_page: str) -> None:
    _render_styles()
    with st.container(key="pilot_hero"):
        st.caption("INTERNAL · FIRST RESTAURANT PILOT")
        st.markdown("## Pilot Dashboard")
        st.write("Monitor processing quality, Business Memory growth, and system health.")

    st.write("")
    dashboard_tab, feedback_tab, support_tab = st.tabs(
        ["Dashboard", "Feedback", "Support"]
    )
    with dashboard_tab:
        _render_dashboard()
    with feedback_tab:
        _render_feedback(current_page)
    with support_tab:
        _render_support()
