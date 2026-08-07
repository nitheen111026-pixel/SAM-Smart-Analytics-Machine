import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile, os
import pyttsx3

# ---------------- CONFIG ----------------
st.set_page_config(page_title="SAM", layout="wide")

# ---------------- THEME ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color:white;
}
.card {
    background: rgba(255,255,255,0.05);
    padding:20px;
    border-radius:15px;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 20px rgba(0,255,255,0.2);
}
button:hover {
    box-shadow: 0 0 15px cyan;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 SAM Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u=="admin" and p=="admin":
            st.session_state.auth=True
        else:
            st.error("Invalid")
    st.stop()

# ---------------- HEADER ----------------
st.title("🚀 SAM – Smart Analytics Machine")
st.caption("Turning Raw Data into Smart Decisions Instantly")

# ---------------- SIDEBAR ----------------
page = st.sidebar.radio("Navigation", [
    "Home","Upload","Dashboard","Insights","Forecast","Ask SAM","Report"
])

# ---------------- UTIL ----------------
def clean(df):
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates().fillna(0)
    return df

def detect(df):
    date = [c for c in df.columns if "date" in c.lower()]
    num = df.select_dtypes(include=np.number).columns.tolist()
    cat = df.select_dtypes(include='object').columns.tolist()
    return date, num, cat

# ---------------- AI STORY ----------------
def storytelling(df, val, cat):
    total = df[val].sum()
    top = df.groupby(cat)[val].sum().idxmax()
    growth = ((df[val].iloc[-1] - df[val].iloc[0])/(df[val].iloc[0]+1))*100

    return f"""
📊 The business generated a total revenue of {total:.2f}.  

📈 Growth trend shows a change of {growth:.2f}%, indicating evolving market dynamics.  

🏆 The leading category is **{top}**, contributing the highest share.  

⚠️ Fluctuations suggest possible seasonal or demand-driven variations.  

🚀 Strategic focus on **{top}** can maximize future growth.
"""

# ---------------- VOICE ----------------
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# ---------------- FORECAST ----------------
def forecast(df, val):
    model = ARIMA(df[val], order=(1,1,1))
    fit = model.fit()
    return fit.forecast(6)

# ---------------- PDF ----------------
def generate_pdf(df, val, cat):
    file = tempfile.NamedTemporaryFile(delete=False).name
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()
    elements = []

    # PAGE 1
    elements.append(Paragraph("SAM Executive Report", styles['Title']))
    elements.append(Spacer(1,20))
    elements.append(Paragraph("Premium Business Insights Report", styles['Normal']))
    elements.append(PageBreak())

    # PAGE 2 KPI
    total = df[val].sum()
    elements.append(Paragraph("KPI Summary", styles['Heading2']))
    elements.append(Paragraph(f"Total Revenue: {total:.2f}", styles['Normal']))
    elements.append(PageBreak())

    # PAGE 3 CHART
    img = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    df.groupby(cat)[val].sum().plot(kind='bar')
    plt.savefig(img)
    plt.close()
    elements.append(Paragraph("Category Performance", styles['Heading2']))
    elements.append(Image(img))
    elements.append(PageBreak())

    # PAGE 4 TREND
    img2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    df[val].plot()
    plt.savefig(img2)
    plt.close()
    elements.append(Paragraph("Trend Analysis", styles['Heading2']))
    elements.append(Image(img2))
    elements.append(PageBreak())

    # PAGE 5 INSIGHTS
    elements.append(Paragraph("AI Insights", styles['Heading2']))
    elements.append(Paragraph(storytelling(df,val,cat), styles['Normal']))
    elements.append(PageBreak())

    # PAGE 6 FORECAST
    pred = forecast(df,val)
    img3 = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    pd.Series(pred).plot()
    plt.savefig(img3)
    plt.close()
    elements.append(Paragraph("Forecast", styles['Heading2']))
    elements.append(Image(img3))

    doc.build(elements)
    return file

# ---------------- HOME ----------------
if page=="Home":
    st.markdown("## Welcome to SAM 🚀")
    st.info("Upload data → Get Insights → Generate Reports")

# ---------------- UPLOAD ----------------
if page=="Upload":
    file = st.file_uploader("Upload CSV/Excel", ["csv","xlsx"])
    if file:
        df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)
        st.session_state.df = df

        st.subheader("Raw Data")
        st.dataframe(df.head())

        clean_df = clean(df)
        st.subheader("Cleaned Data")
        st.dataframe(clean_df.head())

# ---------------- DASHBOARD ----------------
if page=="Dashboard" and "df" in st.session_state:
    df = clean(st.session_state.df)
    date,num,cat = detect(df)

    val = num[0]
    cat = cat[0]

    col1,col2,col3 = st.columns(3)
    col1.metric("Total", f"{df[val].sum():.2f}")
    col2.metric("Average", f"{df[val].mean():.2f}")
    col3.metric("Top", df.groupby(cat)[val].sum().idxmax())

    st.plotly_chart(px.line(df, y=val, title="Trend"))
    st.plotly_chart(px.bar(df, x=cat, y=val, color=cat))
    st.plotly_chart(px.pie(df, names=cat, values=val))
    st.plotly_chart(px.density_heatmap(df, x=cat, y=val))

# ---------------- INSIGHTS ----------------
if page=="Insights" and "df" in st.session_state:
    df = clean(st.session_state.df)
    _,num,cat = detect(df)

    text = storytelling(df,num[0],cat[0])
    st.write(text)

    if st.button("🔊 Voice"):
        speak(text)

# ---------------- FORECAST ----------------
if page=="Forecast" and "df" in st.session_state:
    df = clean(st.session_state.df)
    _,num,_ = detect(df)

    pred = forecast(df,num[0])
    st.line_chart(pred)

# ---------------- ASK SAM ----------------
if page=="Ask SAM" and "df" in st.session_state:
    df = clean(st.session_state.df)
    q = st.text_input("Ask your data")

    if q:
        col = df.select_dtypes(include=np.number).columns[0]
        if "highest" in q:
            st.success(df[col].max())
        elif "average" in q:
            st.success(df[col].mean())
        else:
            st.info("Try: highest, average")

# ---------------- REPORT ----------------
if page=="Report" and "df" in st.session_state:
    df = clean(st.session_state.df)
    _,num,cat = detect(df)

    if st.button("Generate Premium Report"):
        pdf = generate_pdf(df,num[0],cat[0])
        with open(pdf,"rb") as f:
            st.download_button("Download PDF", f, "SAM_Report.pdf")

# ---------------- EMPTY ----------------
if "df" not in st.session_state:
    st.warning("Upload dataset to start 🚀")
