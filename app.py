import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="SAM SMART ANALYTICS", layout="wide")

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
# MATPLOTLIB CHARTS FOR PDF
# =====================================================
def save_bar_chart(cat_summary, cat_col, val_col):
    img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.figure()
    cat_summary.plot(kind='bar')
    plt.title("Category Analysis")
    plt.xlabel(cat_col)
    plt.ylabel(val_col)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img.name)
    plt.close()
    return img.name

def save_line_chart(monthly, val_col):
    img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.figure()
    plt.plot(monthly["Month"], monthly[val_col], marker='o')
    plt.title("Monthly Trend")
    plt.xlabel("Month")
    plt.ylabel(val_col)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(img.name)
    plt.close()
    return img.name

# =====================================================
# PDF REPORT
# =====================================================
def generate_full_report(df, cat_col, val_col, date_col):

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # PAGE 1
    elements.append(Paragraph("EXECUTIVE SUMMARY", styles["Title"]))
    elements.append(Spacer(1, 10))

    for line in generate_insights(total, avg, top, low, growth, cat_summary):
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 15))

    img1 = save_bar_chart(cat_summary, cat_col, val_col)
    elements.append(Image(img1, width=500, height=300))
    elements.append(PageBreak())

    # PAGE 2
    img2 = save_bar_chart(cat_summary, cat_col, val_col)
    elements.append(Image(img2, width=500, height=300))
    elements.append(PageBreak())

    # PAGE 3
    img3 = save_line_chart(monthly, val_col)
    elements.append(Image(img3, width=500, height=300))
    elements.append(PageBreak())

    # PAGE 4
    top_df = df[df[cat_col] == top]
    top_month = complete_months(top_df, date_col, val_col)
    img4 = save_line_chart(top_month, val_col)
    elements.append(Image(img4, width=500, height=300))

    doc.build(elements)
    return pdf_path

# =====================================================
# UI
# =====================================================
st.title("📊 SAM Smart Analytics")

file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if file is not None:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
else:
    st.info("Using sample dataset")
    df = pd.read_csv("sample_data.csv")

df = clean_data(df)
st.success("Data Loaded")

try:
    date_col = st.selectbox("Date Column", df.columns)
    cat_col = st.selectbox("Category Column", df.columns)
    val_col = st.selectbox("Value Column", df.columns)

    if not pd.api.types.is_numeric_dtype(df[val_col]):
        st.error("Value column must be numeric")
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

    if st.button("Download PDF Report"):
        pdf = generate_full_report(df, cat_col, val_col, date_col)
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="SAM_REPORT.pdf")

except Exception as e:
    st.error(f"Error: {e}")
