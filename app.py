import streamlit as st

# ... (your existing code)

st.markdown("""
<style>
    /* --- Force dark blue on all containers and the main app view --- */
    .stApp {
        background-color: #0B1B2B;
    }

    /* Target the main content container */
    .main .block-container {
        background-color: #0B1B2B;
        padding-top: 2rem;
    }

    /* Override any remaining white containers (e.g., st.dataframe, st.metric backgrounds) */
    div[data-testid="stVerticalBlock"] > div,
    div[data-testid="stHorizontalBlock"] > div,
    section[data-testid="stSidebar"] {
        background-color: #0B1B2B !important;
    }

    /* Ensure sidebar items blend in */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stRadio label {
        color: #F0F4F8 !important;
    }

    /* Style for chat input container */
    .stChatInput textarea {
        background-color: #1A2E44 !important;
        color: #F0F4F8 !important;
        border: 1px solid #2563eb !important;
    }
    
    /* Style for buttons to ensure they stand out */
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)
