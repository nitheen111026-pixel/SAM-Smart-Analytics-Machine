import streamlit as st
import pandas as pd
import plotly.express as px
import tempfile
import os
import matplotlib.pyplot as plt
import base64
import json
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="SAM SMART ANALYTICS MACHINE", layout="wide")

# ===========================
# LOGIN STORAGE
# ===========================
LOG_FILE = "user_logs.json"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

# ===========================
# LOGIN FUNCTION
# ===========================
def login_box():
    st.markdown("### 🔐 Login Required to Upload")

    email = st.text_input("Enter your Gmail")

    if st.button("Login"):
        if "@gmail.com" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.success("✅ Login Successful")
        else:
            st.error("❌ Enter valid Gmail ID")

# ===========================
# SAVE LOG
# ===========================
def save_log(email, filename):
    with open(LOG_FILE, "r") as f:
        data = json.load(f)

    data.append({
        "email": email,
        "file": filename,
        "time": str(datetime.datetime.now())
    })

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =====================================================
# BACKGROUND IMAGE + TEXT + MOBILE FIX
# =====================================================
def set_bg(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        st.markdown(f"""
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

        html, body, [class*="css"] {{
            color: white !important;
        }}

        @media (max-width: 768px) {{
            img {{
                max-width: 80px !important;
                height: auto !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)

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

    if os.path.exists(logo_path):
        elements.append(Spacer(1, 150))
        elements.append(Image(logo_path, width=300, height=200))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph('<font name="Times-Roman" size="20">SMART ANALYTICS MACHINE</font>', styles["Title"]))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph('<font name="Times-Roman" size="30">DEVELOPED BY NITHEEN.M</font>', styles["Title"]))
    elements.append(PageBreak())

    def header(title):
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=150, height=100))
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

    header("Category Distribution")

    plt.figure()
    cat_summary.plot(kind='pie', autopct='%1.1f%%')
    plt.ylabel("")
    plt.tight_layout()
    img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img2.name)
    plt.close()

    elements.append(Image(img2.name, width=500, height=350))
    elements.append(PageBreak())

    header("Sales Trend with Average")

    months = monthly["Month"].dt.strftime('%b')
    values = monthly[val_col]
    avg_line = values.mean()

    plt.figure()
    plt.plot(months, values, marker='o', label="Sales")
    plt.axhline(avg_line, linestyle='--', label=f"Avg ({int(avg_line)})")

    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    img3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img3.name)
    plt.close()

    elements.append(Image(img3.name, width=500, height=300))
    elements.append(PageBreak())

    header("Top Performing Months")

    monthly_copy = monthly.copy()
    monthly_copy["MonthName"] = monthly_copy["Month"].dt.strftime('%b')

    top_months = monthly_copy.sort_values(by=val_col, ascending=False).head(5)

    plt.figure()
    bars = plt.bar(top_months["MonthName"], top_months[val_col])

    for bar in bars:
        y = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, y, f'{int(y)}',
                 ha='center', va='bottom')

    plt.tight_layout()

    img4 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img4.name)
    plt.close()

    elements.append(Image(img4.name, width=500, height=300))
    elements.append(PageBreak())

    header("Top Category Trend")

    top_df = df[df[cat_col] == top]
    top_month = complete_months(top_df, date_col, val_col)

    plt.figure()
    plt.plot(top_month["Month"].dt.strftime('%b'), top_month[val_col], marker='o')
    plt.xticks(rotation=45)
    plt.tight_layout()

    img5 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img5.name)
    plt.close()

    elements.append(Image(img5.name, width=500, height=300))
    elements.append(PageBreak())

    header("Category Comparison")

    plt.figure()
    cat_summary.sort_values().plot(kind='barh')
    plt.tight_layout()

    img6 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(img6.name)
    plt.close()

    elements.append(Image(img6.name, width=500, height=300))

    doc.build(elements)
    return pdf_path

# =====================================================
# FILE INPUT + LOGIN CONTROL
# =====================================================
file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

# 🚨 LOGIN ONLY WHEN USER TRIES TO UPLOAD
if file is not None and not st.session_state.logged_in:
    login_box()
    st.stop()

if file is not None:
    save_log(st.session_state.user_email, file.name)
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
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
# MAIN LOGIC
# =====================================================
try:
    date_col = st.selectbox("Date Column", [c for c in df.columns if c.lower() == "order_date"])
    cat_col = st.selectbox("Category Column", [c for c in df.columns if c.lower() in ["city", "category", "product"]])
    val_col = st.selectbox("Value Column", [c for c in df.columns if c.lower() in ["sales", "profit", "quantity"]])

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
# ===========================
# ADMIN PANEL (VIEW USERS)
# ===========================
st.sidebar.title("🔒 Admin Panel")

admin_pass = st.sidebar.text_input("Enter Admin Password", type="password")

if admin_pass == "sam5512":
    st.sidebar.success("Admin Access Granted")

    st.subheader("📊 User Upload Logs")

    if os.path.exists("user_logs.json"):
        with open("user_logs.json", "r") as f:
            data = json.load(f)

        if data:
            df_logs = pd.DataFrame(data)
            st.dataframe(df_logs)
        else:
            st.info("No users yet")
    else:
        st.error("Log file not found")
