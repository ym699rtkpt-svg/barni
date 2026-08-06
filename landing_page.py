from pathlib import Path

import streamlit as st


IMAGE_PATH = Path(__file__).parent / "assets" / "barni_landing.png"


def render_landing_page() -> None:
    if st.session_state.get("barni_entered", False):
        return

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            display: none;
        }

        .stApp {
            background: #070d19;
        }

        .block-container {
            max-width: 1100px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        div.stButton > button {
            width: 100%;
            min-height: 68px;
            border-radius: 18px;
            border: 1px solid #ffe0a0;
            background: linear-gradient(180deg, #ffd77d, #f4a51c);
            color: #081525;
            font-size: 1.55rem;
            font-weight: 800;
            box-shadow: 0 0 34px rgba(255, 177, 45, 0.38);
        }

        div.stButton > button:hover {
            border-color: #fff0bd;
            transform: translateY(-2px);
            box-shadow: 0 0 44px rgba(255, 177, 45, 0.55);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if IMAGE_PATH.exists():
        st.image(str(IMAGE_PATH), use_container_width=True)
    else:
        st.error("לא נמצאה התמונה assets/barni_landing.png")

    left, center, right = st.columns([1.4, 2, 1.4])

    with center:
        if st.button("→ Enter", key="barni_enter", use_container_width=True):
            st.session_state["barni_entered"] = True
            st.rerun()

    st.stop()
