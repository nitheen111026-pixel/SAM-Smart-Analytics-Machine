import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import matplotlib.pyplot as plt
import base64

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="SAM SMART ANALYTICS MACHINE", layout="wide")

# =====================================================
# BACKGROUND IMAGE
# =====================================================
def set_bg(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url("data:image/jpg;base64,{encoded}") no-repeat center center fixed;
                background-size: cover;
            }}
            section[data-testid="stAppViewContainer"] {{
                background: transparent;
            }}
            section[data-testid="stHeader"] {{
                background: transparent;
            }}
            .main {{
                background-color: rgba(255,255,255,0.92);
                padding: 20px;
                border-radius: 10px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

set_bg("background.jpg")

# =====================================================
# HEADER
# =====================================================
col1, col2 = st.columns([1, 4])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)

with col2:
    st.title("📊 SAM  -  SMART  ANALYTICS  MACHINE")

# =====================================================
# CLEAN DATA
# =====================================================
def clean_data(df):
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates().fillna(0)
    return df

# =====================================================
# COMPLETE MONTHS
# =====================================================
def complete_months(df, date_col, val_col):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    full_range = pd.date_range(
        start=df[date_col].min(),
        end=df[date_col].max(),
        freq="MS"
    )

    full_df = pd.DataFrame({"Month": full_range})

    monthly = df.groupby(pd.Grouper(key=date_col, freq="MS"))[val_col].sum().reset_index()
    monthly.columns = ["Month", val_col]

    monthly = full_df.merge(monthly, on="Month", how="left").fillna(0)

    return monthly

# =====================================================
# ANALYSIS
# =====================================================
def analyze(df, cat_col, val_col, date_col):
    cat_summary = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)
    monthly = complete_months(df, date_col, val_col)

    total = df[val_col].sum()
    avg = df[val_col].mean()
    top = cat_summary.idxmax()
    low = cat_summary.idxmin()

    growth = 0
    if len(monthly) > 1:
        growth = ((monthly[val_col].iloc[-1] - monthly[val_col].iloc[0]) / (monthly[val_col].iloc[0] + 1)) * 100

    return total, avg, top, low, growth, cat_summary, monthly

# =====================================================
# INSIGHTS
# =====================================================
def generate_insights(total, avg, top, low, growth, cat_summary):
    contribution = (cat_summary.max() / cat_summary.sum()) * 100

    return [
        f"Total Revenue: ₹{total:,.0f}",
        f"Average Value: ₹{avg:,.0f}",
        f"Top Category: {top} ({contribution:.1f}%)",
        f"Lowest Category: {low}",
        f"Growth: {growth:.2f}% ({'increasing' if growth>0 else 'decreasing'})"
    ]

# =====================================================
# PDF REPORT (UNCHANGED)
# =====================================================
def generate_full_report(df, cat_col, val_col, date_col):
    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    logo_path = "logo.png"

    def header(title):
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=150, height=60))
        else:
            elements.append(Paragraph("SAM SMART ANALYTICS", styles["Title"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 10))

    header("Executive Summary")

    for line in generate_insights(total, avg, top, low, growth, cat_summary):
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 8))

    plt.figure()
    cat_summary.plot(kind='bar')
    plt.xticks(rotation=45)
    plt.tight_layout()
    img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img1.name)
    plt.close()

    elements.append(Image(img1.name, width=500, height=300))
    elements.append(PageBreak())

    doc.build(elements)
    return pdf_path

# =====================================================
# FILE INPUT
# =====================================================
file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if file is not None:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
else:
    if os.path.exists("sample_data.csv"):
        st.info("📊 Using Sample Dataset (Demo Mode)")
        df = pd.read_csv("sample_data.csv")
    else:
        st.error("❌ sample_data.csv not found")
        st.stop()

df = clean_data(df)
st.success("Data Loaded")

# =====================================================
# MAIN LOGIC (UPDATED ONLY HERE)
# =====================================================
try:
    st.markdown("### 📌 Select Column Type")

    mode = st.selectbox("Choose Type", ["Date Column", "Category Column", "Value Column"])

    if mode == "Date Column":
        date_col = st.selectbox("Select Date", ["Order_Date"])
        cat_col = "Category"
        val_col = "Quantity"

    elif mode == "Category Column":
        cat_col = st.selectbox("Select Category", ["City", "Category", "Product"])
        date_col = "Order_Date"
        val_col = "Sales"

    elif mode == "Value Column":
        val_col = st.selectbox("Select Value", ["Sales", "Profit", "Quantity"])
        date_col = "Order_Date"
        cat_col = "Category"

    # =====================================================

    if not pd.api.types.is_numeric_dtype(df[val_col]):
        st.error("❌ Value column must be numeric")
        st.stop()

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", f"₹{total:,.0f}")
    c2.metric("Top", top)
    c3.metric("Growth %", f"{growth:.2f}%")

    st.plotly_chart(px.bar(cat_summary.reset_index(), x=cat_col, y=val_col, color=cat_col))
    st.plotly_chart(px.line(monthly, x="Month", y=val_col, markers=True))

    st.subheader("Insights")
    for line in generate_insights(total, avg, top, low, growth, cat_summary):
        st.write(line)

    if st.button("Generate PDF Report"):
        pdf = generate_full_report(df, cat_col, val_col, date_col)
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="SAM_REPORT.pdf")

except Exception as e:
    st.error(f"⚠️ Error: {e}")
