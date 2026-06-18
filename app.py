import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import plotly.io as pio

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

    return f"""
Total Revenue: ₹{total:,.0f}

Average Value: ₹{avg:,.0f}

Top Category: {top} ({contribution:.1f}%)

Lowest Category: {low}

Growth: {growth:.2f}% ({'increasing' if growth>0 else 'decreasing'})
"""

# =====================================================
# PDF REPORT
# =====================================================
def generate_full_report(df, cat_col, val_col, date_col):

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    def header():
        if os.path.exists("logo.png"):
            elements.append(Image("logo.png", width=160, height=70))
        elements.append(Spacer(1, 10))

    # PAGE 1
    header()
    elements.append(Paragraph("EXECUTIVE SUMMARY", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(generate_insights(total, avg, top, low, growth, cat_summary), styles["Normal"]))
    elements.append(Spacer(1, 20))

    fig1 = px.bar(cat_summary.reset_index(), x=cat_col, y=val_col, color=cat_col)
    fig1.update_layout(paper_bgcolor="white", plot_bgcolor="white")

    img1 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig1.write_image(img1.name, scale=3)

    elements.append(Image(img1.name, width=500, height=300))
    elements.append(PageBreak())

    # PAGE 2
    header()

    fig2 = px.pie(cat_summary.reset_index(), names=cat_col, values=val_col)
    fig3 = px.bar(cat_summary.reset_index(), x=cat_col, y=val_col, text_auto=True)

    img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    fig2.write_image(img2.name, scale=3)
    fig3.write_image(img3.name, scale=3)

    elements.append(Image(img2.name, width=500, height=250))
    elements.append(Spacer(1, 10))
    elements.append(Image(img3.name, width=500, height=250))
    elements.append(PageBreak())

    # PAGE 3
    header()

    fig4 = px.line(monthly, x="Month", y=val_col, markers=True)
    img4 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig4.write_image(img4.name, scale=3)

    elements.append(Image(img4.name, width=500, height=350))
    elements.append(PageBreak())

    # PAGE 4
    header()

    top_df = df[df[cat_col] == top]
    top_month = complete_months(top_df, date_col, val_col)

    fig5 = px.bar(top_month, x="Month", y=val_col)
    img5 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig5.write_image(img5.name, scale=3)

    elements.append(Image(img5.name, width=500, height=350))

    doc.build(elements)

    return pdf_path

# =====================================================
# UI
# =====================================================
st.title("📊 SAM Smart Analytics")

file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

# ✅ SAMPLE DATA SUPPORT
if file is not None:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
else:
    st.info("Using sample dataset (no file uploaded)")
    df = pd.read_csv("sample_data.csv")

df = clean_data(df)
st.success("Data Loaded")

# ✅ ERROR HANDLING
try:
    date_col = st.selectbox("Date Column", df.columns)
    cat_col = st.selectbox("Category Column", df.columns)
    val_col = st.selectbox("Value Column", df.columns)

    # Validate numeric column
    if not pd.api.types.is_numeric_dtype(df[val_col]):
        st.error("❌ Value column must be numeric")
        st.stop()

    # Validate date column
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except:
        st.error("❌ Invalid Date column")
        st.stop()

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", f"₹{total:,.0f}")
    c2.metric("Top", top)
    c3.metric("Growth %", f"{growth:.2f}%")

    st.plotly_chart(px.bar(cat_summary.reset_index(), x=cat_col, y=val_col, color=cat_col))

    fig = px.line(monthly, x="Month", y=val_col, markers=True)
    fig.update_layout(xaxis=dict(dtick="M1", tickformat="%b"))
    st.plotly_chart(fig)

    st.subheader("Insights")
    st.write(generate_insights(total, avg, top, low, growth, cat_summary))

    if st.button("Download PDF Report"):
        pdf = generate_full_report(df, cat_col, val_col, date_col)
        with open(pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="SAM_REPORT.pdf")

except Exception as e:
    st.error(f"⚠️ Error: {e}")
