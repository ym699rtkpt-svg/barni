from __future__ import annotations

import streamlit as st

from services.accountant_workspace import (
    accountant_month_status,
    available_accounting_months,
    build_accountant_package,
)
from services.invoice_workflow import invoice_workflow_snapshot
from services.pilot_support import log_runtime_error
from ui.workflow_status import render_workflow_status


def _render_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-accountant_hero,
        .st-key-accountant_readiness,
        .st-key-accountant_export {
            background: #f7f3e9;
            border: 1px solid rgba(45, 70, 53, 0.12);
            border-radius: 20px;
            padding: 1.25rem 1.45rem;
        }
        [class*="st-key-accountant_metric_"] {
            background: #fcfbf7;
            border: 1px solid rgba(45, 70, 53, 0.10);
            border-radius: 16px;
            padding: 0.8rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _open_feed() -> None:
    st.session_state.current_page = "קליטה יומית"


def _prepare_accountant_package(status: dict) -> tuple[bytes | None, str]:
    """Contain local export failures without changing invoice or workflow state."""
    try:
        return build_accountant_package(status), ""
    except Exception as exc:
        log_runtime_error("Accountant Workspace export", exc)
        return None, (
            "Nothing was exported and your invoices are unchanged. "
            "Check that the source files are available, then try again."
        )


def render_accountant_workspace() -> None:
    _render_styles()
    with st.container(key="accountant_hero"):
        st.caption("MONTH-END WORKSPACE")
        st.markdown("## Accountant Workspace")
        st.write("Check the month and prepare one complete local package for the accountant.")

    st.write("")
    st.markdown("### Invoice Workflow")
    st.caption("The same current status shown in Feed and Home")
    render_workflow_status(
        invoice_workflow_snapshot(),
        key_prefix="accountant_workflow",
    )

    st.write("")
    st.markdown("### Month")
    months = available_accounting_months()
    selected_month = st.selectbox("Month selector", months, label_visibility="collapsed")

    with st.spinner("Barni is checking the month..."):
        status = accountant_month_status(selected_month)

    st.write("")
    st.markdown(f"### {selected_month}")
    st.caption("Package coverage for the selected accounting month")
    metrics = [
        ("Documents included", len(status["documents"])),
        ("Missing source files", status["missing"]),
        ("Ready documents", status["ready"]),
    ]
    columns = st.columns(3, gap="medium")
    for index, (column, (label, value)) in enumerate(zip(columns, metrics)):
        with column:
            with st.container(key=f"accountant_metric_{index}"):
                st.metric(label, value)

    st.write("")
    st.markdown("### Readiness Check")
    with st.container(key="accountant_readiness"):
        checks = [
            (status["duplicate"] == 0, "No duplicate invoices in this month",
             f"{status['duplicate']} duplicate invoice(s) need attention in this month"),
            (status["missing_supplier_names"] == 0, "No missing supplier names",
             f"{status['missing_supplier_names']} invoice(s) are missing supplier names"),
            (status["needs_review"] == 0, "No dated invoices await review in this month",
             f"{status['needs_review']} dated invoice(s) await review in this month"),
            (status["missing"] == 0, "All approved source files are available",
             f"{status['missing']} approved source file(s) are unavailable"),
        ]
        for passed, success_label, failure_label in checks:
            st.write(f"{'✓' if passed else '•'} {success_label if passed else failure_label}")
        if status["ready_for_accountant"]:
            st.success("✓ Ready for accountant")
        elif not len(status["documents"]):
            st.caption("No stored invoices are available for this month yet.")
        else:
            st.caption("Still requires attention:")
            for issue in status["issues"]:
                st.write(f"• {issue}")

    st.write("")
    st.markdown("### Export package")
    with st.container(key="accountant_export"):
        if not len(status["documents"]):
            st.write("There are no approved invoices to export for this month yet.")
            st.button("Feed Barni", type="primary", width="stretch", on_click=_open_feed)
        else:
            st.write("The ZIP contains invoice files, Summary CSV, Summary PDF, and Metadata JSON.")
            st.caption("The package is generated locally. Barni will not send email or transmit it.")
            if st.button(
                "Prepare Accountant Package",
                type="primary",
                width="stretch",
            ):
                with st.spinner("Barni is preparing the accountant package..."):
                    package_bytes, recovery = _prepare_accountant_package(status)
                    if package_bytes is None:
                        st.session_state.pop("accountant_package", None)
                        st.session_state.pop("accountant_package_month", None)
                        st.error("I couldn't prepare the accountant package.")
                        st.write(recovery)
                    else:
                        st.session_state["accountant_package"] = package_bytes
                        st.session_state["accountant_package_month"] = selected_month

        package = st.session_state.get("accountant_package")
        package_month = st.session_state.get("accountant_package_month")
        if len(status["documents"]) and package and package_month == selected_month:
            st.download_button(
                "Download Accountant Package",
                data=package,
                file_name=f"barni-accountant-{selected_month}.zip",
                mime="application/zip",
                width="stretch",
            )
            st.caption("Package prepared successfully on this device.")

    with st.expander("Status definitions"):
        st.caption(
            "Uploaded includes stored invoices and open Feed uploads dated in the selected month. "
            "Missing means an approved invoice source file is unavailable. Duplicate counts stored "
            "invoice groups sharing supplier ID, invoice number, and document type. Ready means an "
            "approved invoice has a supplier name, an available source file, and no duplicate match."
        )
