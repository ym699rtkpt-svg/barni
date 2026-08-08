from __future__ import annotations

import pandas as pd

from database import dashboard_data
from services.business_identity import BusinessIdentityRepository


def _clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _empty_growth() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "Invoices", "Suppliers", "Products"]
    )


def business_memory_data() -> dict:
    identity_health = BusinessIdentityRepository().identity_health()
    data = dashboard_data()
    invoices = data["documents"].copy()
    items = data["items"].copy()

    if not items.empty and "line_type" in items.columns:
        product_items = items[items["line_type"] == "product"].copy()
    else:
        product_items = pd.DataFrame(columns=items.columns)

    if "description" in product_items.columns:
        product_items["_product"] = (
            _clean_text(product_items["description"]).str.lower()
        )
        product_items = product_items[product_items["_product"] != ""]
    else:
        product_items["_product"] = pd.Series(dtype=str)

    known_products = identity_health["products"]
    covered_products = identity_health["covered_products"]
    price_point_count = identity_health["price_points"]

    if invoices.empty:
        supplier_count = 0
        categories = pd.DataFrame(columns=["category", "count"])
        recent = pd.DataFrame()
        growth = _empty_growth()
    else:
        suppliers = _clean_text(invoices["supplier"])
        supplier_count = identity_health["suppliers"]

        category_values = _clean_text(invoices["category"])
        category_values = category_values.replace("", "Uncategorized")
        categories = (
            category_values.value_counts()
            .rename_axis("category")
            .reset_index(name="count")
        )

        invoices["_learned_at"] = pd.to_datetime(
            invoices["created_at"], errors="coerce"
        ).fillna(pd.to_datetime(invoices["invoice_date"], errors="coerce"))
        invoices["_learned_date"] = invoices["_learned_at"].dt.normalize()

        product_counts = (
            product_items.groupby("invoice_id")["_product"].nunique()
            if not product_items.empty and "invoice_id" in product_items.columns
            else pd.Series(dtype=int)
        )
        recent = invoices.sort_values(
            ["_learned_at", "id"],
            ascending=[False, False],
            na_position="last",
        ).head(5).copy()
        recent["product_count"] = (
            recent["id"].map(product_counts).fillna(0).astype(int)
        )

        dated_invoices = invoices.dropna(subset=["_learned_date"])
        invoice_events = (
            dated_invoices.groupby("_learned_date")
            .size()
            .rename("invoices_new")
        )

        supplier_events = pd.Series(dtype=int, name="suppliers_new")
        supplier_rows = dated_invoices.assign(
            _supplier=_clean_text(dated_invoices["supplier"])
        )
        supplier_rows = supplier_rows[supplier_rows["_supplier"] != ""]
        if not supplier_rows.empty:
            supplier_events = (
                supplier_rows.groupby("_supplier")["_learned_date"]
                .min()
                .value_counts()
                .rename("suppliers_new")
            )

        product_events = pd.Series(dtype=int, name="products_new")
        if not product_items.empty and "invoice_id" in product_items.columns:
            product_rows = product_items.merge(
                dated_invoices[["id", "_learned_date"]],
                left_on="invoice_id",
                right_on="id",
                how="inner",
            )
            if not product_rows.empty:
                product_events = (
                    product_rows.groupby("_product")["_learned_date"]
                    .min()
                    .value_counts()
                    .rename("products_new")
                )

        growth = pd.concat(
            [invoice_events, supplier_events, product_events], axis=1
        ).fillna(0).sort_index()
        if growth.empty:
            growth = _empty_growth()
        else:
            growth = growth.cumsum().reset_index().rename(
                columns={
                    "_learned_date": "date",
                    "invoices_new": "Invoices",
                    "suppliers_new": "Suppliers",
                    "products_new": "Products",
                }
            )

    return {
        "invoice_count": int(len(invoices)),
        "supplier_count": supplier_count,
        "product_count": known_products,
        "covered_product_count": covered_products,
        "price_point_count": price_point_count,
        "categories": categories,
        "growth": growth,
        "recent": recent,
    }
