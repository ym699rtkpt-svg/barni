from __future__ import annotations

import pandas as pd

from database import connect, dashboard_data, product_price_history, search_invoices
from knowledge_engine.line_classifier import is_product_line
from services.business_identity import BusinessIdentityRepository
from services.invoice_workflow import approved_documents


def _clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _empty_growth() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "Invoices", "Suppliers", "Products"]
    )


def business_memory_data() -> dict:
    identity_health = BusinessIdentityRepository().identity_health()
    data = dashboard_data()
    invoices = approved_documents()
    items = data["items"].copy()
    if not items.empty and "invoice_id" in items.columns:
        approved_ids = set(invoices.get("id", pd.Series(dtype=int)).tolist())
        items = items[items["invoice_id"].isin(approved_ids)].copy()

    if not items.empty:
        product_items = items[
            items.apply(lambda row: is_product_line(row.to_dict()), axis=1)
        ].copy()
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
            # Empty event series can drop the shared index name during concat.
            # Keep the chart contract stable even when an invoice has no items.
            growth.index.name = "date"
            growth = growth.cumsum().reset_index().rename(
                columns={
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


def supplier_memory_options() -> list[str]:
    return [supplier.canonical_name for supplier in BusinessIdentityRepository().suppliers()]


def supplier_memory_history(name: str) -> pd.DataFrame:
    return search_invoices(supplier_query=name, statuses=["approved"])


def product_memory_options() -> list[str]:
    repository = BusinessIdentityRepository()
    all_names = [product.canonical_name for product in repository.products()]
    with connect() as connection:
        rows = connection.execute(
            """SELECT products.canonical_name
               FROM canonical_products products
               JOIN comparable_price_facts prices
                 ON prices.canonical_product_id = products.id
               JOIN business_facts facts ON facts.id = prices.fact_id
               WHERE products.active = 1 AND facts.trust_status = 'TRUSTED'
               GROUP BY products.id
               ORDER BY COUNT(*) DESC, products.canonical_name COLLATE NOCASE"""
        ).fetchall()
    known_names = set(all_names)
    trusted_history = [
        row["canonical_name"]
        for row in rows
        if row["canonical_name"] in known_names
    ]
    return [*trusted_history, *(name for name in all_names if name not in set(trusted_history))]


def product_memory_history(name: str) -> pd.DataFrame:
    return product_price_history(name)
