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

    logo_path = "logo.png"

    def header(title):
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=140, height=55))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 15))

    # ================= PAGE 1 =================
    header("Executive Summary")

    for line in generate_insights(total, avg, top, low, growth, cat_summary):
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 8))

    plt.figure()
    bars = plt.bar(cat_summary.index, cat_summary.values)
    plt.title("Category Sales Overview")
    plt.xticks(rotation=45)

    # ✅ Add value labels
    for bar in bars:
        y = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, y, f'{int(y)}',
                 ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img1.name)
    plt.close()

    elements.append(Image(img1.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 2 =================
    header("Category Distribution")

    plt.figure()
    plt.pie(cat_summary.values,
            labels=cat_summary.index,
            autopct='%1.1f%%',
            startangle=90)

    plt.title("Contribution by Category")
    plt.tight_layout()

    img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img2.name)
    plt.close()

    elements.append(Image(img2.name, width=500, height=350))
    elements.append(PageBreak())

    # ================= PAGE 3 =================
    header("Monthly Trend")

    months = monthly["Month"].dt.strftime('%b')

    plt.figure()
    plt.plot(months, monthly[val_col], marker='o')
    plt.title("Sales Trend Over Time")
    plt.grid(True)

    plt.xticks(rotation=45)

    # ✅ highlight last value
    plt.text(len(months)-1, monthly[val_col].iloc[-1],
             f"{int(monthly[val_col].iloc[-1])}")

    plt.tight_layout()

    img3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img3.name)
    plt.close()

    elements.append(Image(img3.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 4 =================
    header("Month-wise Sales")

    plt.figure()
    bars = plt.bar(months, monthly[val_col])

    plt.title("Monthly Sales Breakdown")
    plt.xticks(rotation=45)

    # ✅ value labels
    for bar in bars:
        y = bar.get_height()
        plt.text(bar.get_x()+bar.get_width()/2, y,
                 f'{int(y)}', ha='center', va='bottom', fontsize=7)

    plt.tight_layout()

    img4 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img4.name)
    plt.close()

    elements.append(Image(img4.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 5 =================
    header("Top Category Performance")

    top_df = df[df[cat_col] == top]
    top_month = complete_months(top_df, date_col, val_col)

    months_top = top_month["Month"].dt.strftime('%b')

    plt.figure()
    plt.plot(months_top, top_month[val_col], marker='o')
    plt.title(f"{top} Monthly Performance")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()

    img5 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img5.name)
    plt.close()

    elements.append(Image(img5.name, width=500, height=300))
    elements.append(PageBreak())

    # ================= PAGE 6 =================
    header("Category Comparison")

    plt.figure()
    bars = plt.barh(cat_summary.index, cat_summary.values)

    plt.title("Category Comparison")

    # ✅ value labels
    for bar in bars:
        x = bar.get_width()
        plt.text(x, bar.get_y()+bar.get_height()/2,
                 f'{int(x)}', va='center')

    plt.tight_layout()

    img6 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img6.name)
    plt.close()

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
    
