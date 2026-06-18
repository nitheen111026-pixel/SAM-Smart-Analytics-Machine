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
# APP HEADER (LOGO + TITLE)
# =====================================================
col1, col2 = st.columns([1, 4])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)

with col2:
    st.title("📊 SAM Smart Analytics")

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
# PDF REPORT
# =====================================================
def generate_full_report(df, cat_col, val_col, date_col):

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    def header(title):
        if os.path.exists("logo.png"):
            elements.append(Image("logo.png", width=150, height=60))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 10))

    # ================= PAGE 1 =================
    header("Executive Summary")

    # ✅ FIX: show insights properly
    for line in generate_insights(total, avg, top, low, growth, cat_summary):
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 6))

    fig1 = px.bar(
        cat_summary.reset_index(),
        x=cat_col,
        y=val_col,
        text=val_col,
        color=cat_col,
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig1.update_traces(textposition='outside')
    fig1.update_layout(
        title="Category Sales Overview",
        xaxis_title=cat_col,
        yaxis_title=val_col,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig1.write_image(img1.name, scale=3)

    elements.append(Image(img1.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 2 =================
    header("Category Distribution")

    fig2 = px.pie(
        cat_summary.reset_index(),
        names=cat_col,
        values=val_col,
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig2.update_layout(title="Category Contribution", paper_bgcolor="white")

    img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig2.write_image(img2.name, scale=3)

    elements.append(Image(img2.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 3 =================
    header("Monthly Trend")

    monthly["MonthName"] = monthly["Month"].dt.strftime('%b')

    fig3 = px.line(
        monthly,
        x="MonthName",
        y=val_col,
        markers=True,
        color_discrete_sequence=["#E74C3C"]   # 🔴 RED
    )

    fig3.update_layout(
        title="Sales Trend Over Time",
        xaxis_title="Month",
        yaxis_title=val_col,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    img3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig3.write_image(img3.name, scale=3)

    elements.append(Image(img3.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 4 =================
    header("Month-wise Sales")

    fig4 = px.bar(
        monthly,
        x="MonthName",
        y=val_col,
        text=val_col,
        color_discrete_sequence=["#28B463"]   # 🟢 GREEN
    )

    fig4.update_traces(textposition='outside')

    fig4.update_layout(
        title="Monthly Sales Breakdown",
        xaxis_title="Month",
        yaxis_title=val_col,
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    img4 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig4.write_image(img4.name, scale=3)

    elements.append(Image(img4.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 5 =================
    header("Top Category Performance")

    top_df = df[df[cat_col] == top]
    top_month = complete_months(top_df, date_col, val_col)
    top_month["MonthName"] = top_month["Month"].dt.strftime('%b')

    fig5 = px.line(
        top_month,
        x="MonthName",
        y=val_col,
        markers=True,
        color_discrete_sequence=["#8E44AD"]   # 🟣 PURPLE
    )

    fig5.update_layout(
        title=f"{top} Monthly Performance",
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    img5 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig5.write_image(img5.name, scale=3)

    elements.append(Image(img5.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 6 =================
    header("Category Comparison")

    fig6 = px.bar(
        cat_summary.sort_values().reset_index(),
        x=val_col,
        y=cat_col,
        orientation='h',
        text=val_col,
        color_discrete_sequence=["#F39C12"]   # 🟠 ORANGE
    )

    fig6.update_traces(textposition='outside')

    fig6.update_layout(
        title="Category Comparison",
        paper_bgcolor="white",
        plot_bgcolor="white"
    )

    img6 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig6.write_image(img6.name, scale=3)

    elements.append(Image(img6.name, width=500, height=300))

    doc.build(elements)

    return pdf_path
# =====================================================
# FILE INPUT
# =====================================================
file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

if file is not None:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
else:
    st.info("Using sample dataset")
    df = pd.read_csv("sample_data.csv")

df = clean_data(df)
st.success("Data Loaded")

# =====================================================
# MAIN LOGIC
# =====================================================
try:
    date_col = st.selectbox("Date Column", df.columns)
    cat_col = st.selectbox("Category Column", df.columns)
    val_col = st.selectbox("Value Column", df.columns)

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

    if st.button("Download PDF Report"):
        pdf = generate_full_report(df, cat_col, val_col, date_col)
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="SAM_REPORT.pdf")

except Exception as e:
    st.error(f"⚠️ Error: {e}")
    
