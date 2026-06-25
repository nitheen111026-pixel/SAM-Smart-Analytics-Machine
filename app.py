def generate_full_report(df, cat_col, val_col, date_col):

    total, avg, top, low, growth, cat_summary, monthly = analyze(df, cat_col, val_col, date_col)

    pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    logo_path = "logo.png"

    # =====================================================
    # PAGE 1 (NEW COVER PAGE)
    # =====================================================
    if os.path.exists(logo_path):
        elements.append(Spacer(1, 150))
        elements.append(Image(logo_path, width=300, height=200))

    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        '<font name="Times-Roman" size="40">SMART ANALYTICS MACHINE</font>',
        styles["Title"]
    ))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        '<font name="Times-Roman" size="30">DEVELOPED BY NITHEEN.M</font>',
        styles["Title"]
    ))

    elements.append(PageBreak())

    # =====================================================
    # OLD FUNCTION (UNCHANGED)
    # =====================================================
    def header(title):
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=150, height=100))
        else:
            elements.append(Paragraph("SAM SMART ANALYTICS", styles["Title"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 10))

    # PAGE 2
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

    # PAGE 3
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

    # PAGE 4
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

    # PAGE 5
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

    # PAGE 6
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

    # PAGE 7
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
