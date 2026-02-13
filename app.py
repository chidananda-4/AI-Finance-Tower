import streamlit as st
import pandas as pd
import os

from backend import run_full_analysis
from ppt_generator import generate_ppt


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Finance Control Tower",
    layout="wide"
)

st.title("📊 Finance Control Tower Dashboard")


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Finance Excel File",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:
        # Load Excel
        xls = pd.ExcelFile(uploaded_file)

        # REQUIRED SHEETS
        required_sheets = ["AP_Spend_Invoices", "AR_Invoices_Collections","Vendor_Master","CostCenter_Master","Budget_Plan_Monthly"]

        for sheet in required_sheets:
            if sheet not in xls.sheet_names:
                st.error(f"Missing required sheet: {sheet}")
                st.stop()

        #ap_df = pd.read_excel(uploaded_file, sheet_name="ap_spend_invoices")
        ap_df = pd.read_excel(uploaded_file, sheet_name="AP_Spend_Invoices")
        vendor = pd.read_excel(uploaded_file, sheet_name="Vendor_Master")
        costcenter = pd.read_excel(uploaded_file, sheet_name="CostCenter_Master")
        budget = pd.read_excel(uploaded_file, sheet_name="Budget_Plan_Monthly")

        ap_df['yyyy-mm'] = ap_df['txn_date'].dt.strftime('%Y-%m')
        budget['yyyy-mm'] = budget['month'].dt.strftime('%Y-%m')
        ap_df = pd.merge(ap_df,budget,on=['cost_center','yyyy-mm','business_unit','region','category'],how='left')
        ap_df = pd.merge(ap_df,vendor[['vendor_id','vendor_risk_score','vendor_name']],on='vendor_id',how='left')
        ap_df = pd.merge(ap_df,costcenter[['cost_center','owner']],on='cost_center',how='left')
        ar_df = pd.read_excel(uploaded_file, sheet_name="AR_Invoices_Collections")

        st.success("Excel file loaded successfully.")

        # ============================================================
        # RUN ANALYSIS BUTTON
        # ============================================================

        if st.button("Run Full Finance Analysis"):

            with st.spinner("Running KPI engine and multi-agent analysis..."):

                results = run_full_analysis(ap_df, ar_df)

            st.success("Analysis Completed Successfully")

            # ============================================================
            # DISPLAY KPIs
            # ============================================================

            st.subheader("AP KPI Keys")
            st.json(list(results["ap_kpis"].keys()))

            st.subheader("AR KPI Keys")
            st.json(list(results["ar_kpis"].keys()))

            # ============================================================
            # DISPLAY INSIGHTS
            # ============================================================

            st.subheader("Generated Insights")
            st.json(results.get("insights", {}))

            # ============================================================
            # GENERATE PPT
            # ============================================================

            try:
                ppt_path = generate_ppt(results)

                st.success("PPT Generated Successfully")

                with open(ppt_path, "rb") as file:
                    st.download_button(
                        label="Download Finance Control Tower PPT",
                        data=file,
                        file_name="Finance_Control_Tower.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )

            except Exception as e:
                st.error(f"PPT generation failed: {e}")

    except Exception as e:
        st.error(f"Error processing file: {e}")
