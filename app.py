import streamlit as st
import pandas as pd

st.title("✅ HOI Annotation Sheet Viewer")

# Your published CSV link
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzsSbNZ7bh894PTHiwMdXdiK395mkWTuLigdhd9DGTkyjp4nfvgtzOYkj5CUVxwAMEL6ERERgX2jp7/pub?gid=0&single=true&output=csv"

try:
    df = pd.read_csv(csv_url)
    st.success("✅ Loaded Google Sheet successfully!")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Failed to load sheet: {e}")
