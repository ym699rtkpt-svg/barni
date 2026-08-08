from __future__ import annotations

import streamlit as st

from services.invoice_workflow import (
    InvoiceWorkflowSnapshot,
    InvoiceWorkflowStatus,
    STATUS_LABELS,
)


def render_workflow_status(
    snapshot: InvoiceWorkflowSnapshot,
    *,
    key_prefix: str,
    include_approved: bool = True,
) -> None:
    statuses = [
        InvoiceWorkflowStatus.PENDING_REVIEW,
        InvoiceWorkflowStatus.LEARNING,
        InvoiceWorkflowStatus.NEEDS_ATTENTION,
        InvoiceWorkflowStatus.DUPLICATE,
    ]
    if include_approved:
        statuses.insert(2, InvoiceWorkflowStatus.APPROVED)

    columns = st.columns(len(statuses), gap="small")
    for column, status in zip(columns, statuses):
        with column:
            with st.container(key=f"{key_prefix}_{status.value}"):
                st.metric(STATUS_LABELS[status], snapshot.count(status))

