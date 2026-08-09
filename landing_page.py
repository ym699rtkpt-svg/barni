import time

import streamlit as st


_TRANSITION_SECONDS = 1.35


def _render_landing_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp:has(.st-key-barni_landing) {
            background: #f7f3e9;
        }
        .stApp:has(.st-key-barni_landing) [data-testid="stSidebar"],
        .stApp:has(.st-key-barni_landing) [data-testid="stHeader"],
        .stApp:has(.st-key-barni_landing) [data-testid="stToolbar"] {
            display: none;
        }
        .stApp:has(.st-key-barni_landing) .block-container {
            max-width: 760px;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .st-key-barni_landing {
            min-height: 88vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
        }
        .barni-landing-brand {
            color: #2f4f37;
            text-align: center;
        }
        .barni-landing-egg {
            display: inline-block;
            margin-bottom: 0.7rem;
            font-size: 5rem;
            line-height: 1;
            filter: drop-shadow(0 7px 9px rgba(45, 70, 53, 0.10));
        }
        .barni-landing-brand h1 {
            margin: 0;
            color: #2f4f37;
            font-size: clamp(2.8rem, 7vw, 4.6rem);
            font-weight: 750;
            letter-spacing: -0.045em;
        }
        .barni-landing-kicker {
            margin-top: 0.45rem;
            color: #3f5b44;
            font-size: 1.05rem;
            font-weight: 650;
            letter-spacing: 0.035em;
        }
        .barni-landing-promise {
            margin: 1.1rem 0 1.8rem;
            color: #738078;
            font-size: 1rem;
        }
        .st-key-barni_enter {
            margin-inline: auto;
        }
        .st-key-barni_enter button {
            width: 180px;
            min-height: 48px;
            border: 1px solid #3f5b44;
            border-radius: 14px;
            background: #3f5b44;
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 700;
            box-shadow: 0 7px 18px rgba(63, 91, 68, 0.18);
        }
        .st-key-barni_enter button:hover {
            border-color: #315b3d;
            background: #315b3d;
            color: #ffffff;
        }
        .barni-transition {
            margin: 1.35rem auto 0;
            text-align: center;
        }
        .barni-transition-track {
            position: relative;
            width: min(390px, 78vw);
            height: 72px;
            margin: 0 auto 0.85rem;
            overflow: hidden;
            border-bottom: 2px solid rgba(63, 91, 68, 0.16);
        }
        .barni-dino-runner {
            position: absolute;
            bottom: 11px;
            left: -34px;
            width: 32px;
            height: 32px;
            animation: barni-dino-travel 1.3s linear forwards;
        }
        .barni-dino-pixel {
            position: absolute;
            top: 4px;
            left: 4px;
            width: 4px;
            height: 4px;
            background: #3f5b44;
            box-shadow:
                4px 0 #3f5b44, 8px 0 #3f5b44, 12px 0 #3f5b44,
                16px 0 #3f5b44, 20px 0 #3f5b44,
                4px 4px #3f5b44, 8px 4px #3f5b44, 12px 4px #3f5b44,
                16px 4px #3f5b44, 20px 4px #3f5b44,
                4px 8px #3f5b44, 8px 8px #3f5b44, 12px 8px #3f5b44,
                0 12px #3f5b44, 4px 12px #3f5b44, 8px 12px #3f5b44,
                12px 12px #3f5b44,
                -4px 16px #3f5b44, 0 16px #3f5b44, 4px 16px #3f5b44,
                8px 16px #3f5b44, 12px 16px #3f5b44,
                -8px 12px #3f5b44, -8px 16px #3f5b44,
                -4px 20px #3f5b44, 8px 20px #3f5b44,
                -4px 24px #3f5b44, 12px 24px #3f5b44;
            animation: barni-dino-hop 0.58s ease-in-out 2;
        }
        .barni-obstacle {
            position: absolute;
            bottom: 9px;
            width: 5px;
            height: 5px;
            border-radius: 1px;
            background: rgba(63, 91, 68, 0.42);
        }
        .barni-obstacle-one { left: 38%; }
        .barni-obstacle-two {
            left: 66%;
            width: 8px;
            height: 12px;
            border: 1px solid rgba(63, 91, 68, 0.42);
            background: #f7f3e9;
        }
        .barni-obstacle-three { left: 70%; }
        .barni-loading-copy {
            color: #3f5b44;
            font-size: 0.9rem;
            font-weight: 600;
        }
        @keyframes barni-dino-travel {
            from { left: -34px; }
            to { left: calc(100% + 8px); }
        }
        @keyframes barni-dino-hop {
            0%, 36%, 100% { transform: translateY(0); }
            56% { transform: translateY(-18px); }
        }
        @media (prefers-reduced-motion: reduce) {
            .barni-dino-runner {
                left: calc(50% - 16px);
                animation: none;
            }
            .barni-dino-pixel { animation: none; }
            .barni-obstacle { opacity: 0.3; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_transition() -> None:
    st.markdown(
        """
        <div class="barni-transition" role="status" aria-live="polite">
            <div class="barni-transition-track" aria-hidden="true">
                <div class="barni-dino-runner">
                    <div class="barni-dino-pixel"></div>
                </div>
                <span class="barni-obstacle barni-obstacle-one"></span>
                <span class="barni-obstacle barni-obstacle-two"></span>
                <span class="barni-obstacle barni-obstacle-three"></span>
            </div>
            <div class="barni-loading-copy">Waking Barni up...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    if st.session_state.get("barni_entered", False):
        return

    _render_landing_styles()
    with st.container(key="barni_landing"):
        st.markdown(
            """
            <div class="barni-landing-brand">
                <div class="barni-landing-egg" aria-label="Barni egg">🥚</div>
                <h1>Barni</h1>
                <div class="barni-landing-kicker">Your Business Memory</div>
                <div class="barni-landing-promise">Your business, remembered.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("barni_enter_transition", False):
            _render_transition()
            time.sleep(_TRANSITION_SECONDS)
            st.session_state["barni_entered"] = True
            st.session_state.pop("barni_enter_transition", None)
            st.rerun()

        if st.button("Enter Barni", key="barni_enter"):
            st.session_state["barni_enter_transition"] = True
            st.rerun()

    st.stop()
