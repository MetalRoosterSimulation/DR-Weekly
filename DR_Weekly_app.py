from flask import Flask, render_template, request, jsonify
import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
import os

app = Flask(__name__)

# ─────────────────────────────────────────────
# COLUMN CONFIGURATION — edit these to match
# the exact column headers in your spreadsheet
# ─────────────────────────────────────────────
COLUMN_CONFIG = {
    "partner":      "Primary Partner Account",
    "customer":     "Opportunity Name",
    "sales_price":  "Total ACV (converted)",
    "close_date":   "Close Date",
    "created_date": "Created Date",
}

@app.route("/")
def index():
    return render_template("index.html", config=COLUMN_CONFIG)

@app.route("/process", methods=["POST"])
def process():
    try:
        file = request.files.get("spreadsheet")
        start_date = request.form.get("start_date")
        end_date   = request.form.get("end_date")

        if not file:
            return jsonify({"error": "No file uploaded."}), 400

        # Read .xls or .xlsx
        filename = file.filename.lower()
        if filename.endswith(".xls"):
            df = pd.read_excel(file, engine="xlrd")
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        elif filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            return jsonify({"error": "Unsupported file type. Please upload .xls, .xlsx, or .csv"}), 400

        # Validate required columns exist
        missing = [v for v in COLUMN_CONFIG.values() if v not in df.columns]
        if missing:
            available = ", ".join(df.columns.tolist())
            return jsonify({
                "error": f"Missing columns: {', '.join(missing)}. "
                         f"Available columns in your file: {available}"
            }), 400

        # Parse and filter by created date
        df[COLUMN_CONFIG["created_date"]] = pd.to_datetime(
            df[COLUMN_CONFIG["created_date"]], errors="coerce"
        )

        if start_date:
            df = df[df[COLUMN_CONFIG["created_date"]] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[COLUMN_CONFIG["created_date"]] <= pd.to_datetime(end_date)]

        if df.empty:
            return jsonify({"error": "No rows found in the selected date range."}), 400

        # Build plain text report
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("  SALES REPORT")
        if start_date or end_date:
            report_lines.append(f"  Created Date Range: {start_date or 'any'} → {end_date or 'any'}")
        report_lines.append(f"  Total Records: {len(df)}")
        report_lines.append("=" * 60)
        report_lines.append("")

        for _, row in df.iterrows():
            partner    = row.get(COLUMN_CONFIG["partner"],     "N/A")
            customer   = row.get(COLUMN_CONFIG["customer"],    "N/A")
            price      = row.get(COLUMN_CONFIG["sales_price"], "N/A")
            close_date = row.get(COLUMN_CONFIG["close_date"],  "N/A")

            # Format price
            try:
                price = f"${float(price):,.2f}"
            except (ValueError, TypeError):
                price = str(price)

            # Format close date
            try:
                close_date = pd.to_datetime(close_date).strftime("%B %d, %Y")
            except Exception:
                close_date = str(close_date)

            report_lines.append(f"  Partner:         {partner}")
            report_lines.append(f"  Customer:        {customer}")
            report_lines.append(f"  Sales Price:     {price}")
            report_lines.append(f"  Est. Close Date: {close_date}")
            report_lines.append("-" * 60)

        report_text = "\n".join(report_lines)

        # Build pie chart — sales by partner
        partner_col = COLUMN_CONFIG["partner"]
        price_col   = COLUMN_CONFIG["sales_price"]

        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        partner_totals = df.groupby(partner_col)[price_col].sum().sort_values(ascending=False)

        fig, ax = plt.subplots(figsize=(8, 7), facecolor="#0d1117")
        ax.set_facecolor("#0d1117")

        colors = [
            "#00d4ff", "#ff6b6b", "#ffd93d", "#6bcb77",
            "#a78bfa", "#fb923c", "#34d399", "#f472b6",
            "#60a5fa", "#facc15"
        ]

        wedges, texts, autotexts = ax.pie(
            partner_totals.values,
            labels=None,
            autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
            colors=colors[:len(partner_totals)],
            startangle=90,
            pctdistance=0.75,
            wedgeprops={"edgecolor": "#0d1117", "linewidth": 2}
        )

        for at in autotexts:
            at.set_color("white")
            at.set_fontsize(10)
            at.set_fontweight("bold")

        legend_labels = [
            f"{name}  (${val:,.0f})"
            for name, val in zip(partner_totals.index, partner_totals.values)
        ]
        ax.legend(
            wedges, legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=2,
            frameon=False,
            fontsize=9,
            labelcolor="white"
        )

        ax.set_title(
            "Sales by Partner",
            color="white", fontsize=15, fontweight="bold", pad=20
        )

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight",
                    facecolor="#0d1117", dpi=150)
        plt.close(fig)
        buf.seek(0)
        chart_b64 = base64.b64encode(buf.read()).decode("utf-8")

        return jsonify({
            "report": report_text,
            "chart":  chart_b64,
            "count":  len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
