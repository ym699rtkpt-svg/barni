from __future__ import annotations

from pathlib import Path

import streamlit as st


_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def render_original_source(
    source: Path,
    *,
    file_name: str = "",
    height: int = 620,
    key_prefix: str = "original_source",
) -> bool:
    """Render the exact preserved upload inline and retain a download fallback."""
    if not source.exists() or not source.is_file():
        st.caption("The original file is unavailable, but the extracted details remain.")
        return False

    try:
        source_bytes = source.read_bytes()
    except OSError:
        st.caption("I couldn't open the original here. Try Open Original again.")
        return False

    suffix = source.suffix.lower()
    display_name = file_name or source.name
    rendered_inline = False
    if suffix == ".pdf":
        try:
            st.pdf(source_bytes, height=height)
            rendered_inline = True
        except Exception:
            st.caption("I couldn't show this PDF inline. Use Open Original below.")
    elif suffix in _IMAGE_SUFFIXES:
        try:
            st.image(source_bytes, width="stretch")
            rendered_inline = True
        except Exception:
            st.caption("I couldn't show this image inline. Use Open Original below.")
    else:
        st.caption("This file format cannot be shown inline. Use Open Original below.")

    st.download_button(
        "Open Original",
        data=source_bytes,
        file_name=display_name,
        mime=_MIME_TYPES.get(suffix, "application/octet-stream"),
        width="stretch",
        key=f"{key_prefix}_download",
    )
    return rendered_inline
