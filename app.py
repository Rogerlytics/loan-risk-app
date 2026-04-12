import streamlit as st
import pickle
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="AI Loan Risk System", layout="wide")

# ==============================
#
