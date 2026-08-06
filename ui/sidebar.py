import streamlit as st


def render_sidebar():

    st.sidebar.markdown(
        """
        ## 🥚

        # Barni

        **Your Business Memory**
        """
    )

    pages = [
        "🏠 Home",
        "📄 Feed Barni",
        "🔍 Search Invoices",
        "🧠 Business Memory",
        "📈 Insights",
    ]

    page = st.sidebar.radio(
        "",
        pages,
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    with st.sidebar.expander("⚙ System"):

        st.button("Diagnostics")

        st.button("Migration")

        st.button("Database")

    return page
