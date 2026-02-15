import streamlit as st
import pandas as pd
import os
import time
from backend import run_full_analysis
from ppt_generator import generate_ppt

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Finance Control Tower",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# PREMIUM CSS
# =====================================================
st.markdown("""
<style>

.main-title{
    font-size:48px;
    font-weight:800;
    text-align:center;
    background: linear-gradient(90deg,#1E88E5,#42A5F5);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.subtitle{
    text-align:center;
    color:#777;
    margin-bottom:30px;
}

.card{
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow:0 4px 14px rgba(0,0,0,0.06);
    margin-bottom:20px;
}

.metric-card{
    background:white;
    padding:18px;
    border-radius:10px;
    text-align:center;
    box-shadow:0 2px 10px rgba(0,0,0,0.05);
}

.success-banner{
    background:#E8F5E9;
    padding:15px;
    border-radius:10px;
    border-left:6px solid #4CAF50;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown('<div class="main-title">Finance Control Tower</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Autonomous Agentic Financial Intelligence Platform</div>', unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.title("📊 Finance Control Tower")
    st.markdown("---")

    st.markdown("""
### Capabilities

✅ KPI Monitoring  
✅ Anomaly Detection  
✅ Agent-driven Insights  
✅ Automatic PPT  

---

### Hackathon Mode

Upload dataset  
Run AI  
Download board-ready PPT
""")

# =====================================================
# FILE UPLOAD SECTION
# =====================================================
st.markdown('<div class="card">', unsafe_allow_html=True)

st.subheader("📂 Upload Finance Excel File")

uploaded_file = st.file_uploader(
    "",
    type=["xlsx"]
)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# IF FILE UPLOADED
# =====================================================
if uploaded_file:

    temp = "temp.xlsx"
    with open(temp,"wb") as f:
        f.write(uploaded_file.getbuffer())

    xls = pd.ExcelFile(temp)

    required = [
        "AP_Spend_Invoices",
        "AR_Invoices_Collections",
        "Vendor_Master",
        "CostCenter_Master",
        "Budget_Plan_Monthly"
    ]

    missing = [s for s in required if s not in xls.sheet_names]

    if missing:
        st.error(f"Missing sheets: {missing}")
        st.stop()

    # LOAD
    ap_df = pd.read_excel(temp, sheet_name="AP_Spend_Invoices")
    ar_df = pd.read_excel(temp, sheet_name="AR_Invoices_Collections")
    vendor = pd.read_excel(temp, sheet_name="Vendor_Master")
    costcenter = pd.read_excel(temp, sheet_name="CostCenter_Master")
    budget = pd.read_excel(temp, sheet_name="Budget_Plan_Monthly")

    # =====================================================
    # DATA SUMMARY CARDS
    # =====================================================
    st.markdown("### Dataset Overview")

    c1,c2,c3 = st.columns(3)

    c1.markdown(f"<div class='metric-card'><h2>{len(ap_df)}</h2>AP Rows</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><h2>{len(ar_df)}</h2>AR Rows</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><h2>{len(vendor)}</h2>Vendors</div>", unsafe_allow_html=True)

    st.write("")

    # =====================================================
    # RUN BUTTON
    # =====================================================
    if st.button("🚀 Run Autonomous Financial Analysis", use_container_width=True):

        # progress animation
        prog = st.progress(0)
        status = st.empty()

        try:

            # ======================
            # DATA PREP
            # ======================
            status.text("Preparing data…")

            ap_df['yyyy-mm'] = pd.to_datetime(ap_df['txn_date']).dt.strftime('%Y-%m')
            budget['yyyy-mm'] = pd.to_datetime(budget['month']).dt.strftime('%Y-%m')

            ap_df = pd.merge(ap_df,budget,on=['cost_center','yyyy-mm','business_unit','region','category'],how='left')
            ap_df = pd.merge(ap_df,vendor[['vendor_id','vendor_risk_score','vendor_name']],on='vendor_id',how='left')
            ap_df = pd.merge(ap_df,costcenter[['cost_center','owner']],on='cost_center',how='left')

            prog.progress(25)

            # ======================
            # RUN AGENT SYSTEM
            # ======================
            status.text("Running AI agents…")
            results = run_full_analysis(ap_df, ar_df)

            prog.progress(70)

            # ======================
            # GENERATE PPT
            # ======================
            status.text("Generating executive PPT…")
            ppt_path = generate_ppt(results)

            prog.progress(100)
            status.empty()
            prog.empty()

            st.markdown('<div class="success-banner">✅ Autonomous Analysis Completed</div>', unsafe_allow_html=True)

            # =====================================================
            # RESULTS TABS
            # =====================================================
            tab1,tab2,tab3,tab4 = st.tabs(["📊 KPIs","💡 Insights","⚠️ Logs","⬇️ Download"])

            # KPI
            with tab1:

                st.subheader("AP KPI Keys")
                st.write(list(results["ap_kpis"].keys()))

                st.subheader("AR KPI Keys")
                st.write(list(results["ar_kpis"].keys()))

            # INSIGHTS
            with tab2:

                ins = results.get("insights",{})

                if "executive_summary" in ins:
                    st.markdown("### Executive Summary")
                    for x in ins["executive_summary"]:
                        st.markdown(f"• {x}")

                if "ap" in ins:
                    st.markdown("### AP Insights")
                    for slide,bul in ins["ap"].items():
                        with st.expander(slide):
                            for b in bul:
                                st.markdown(f"• {b}")

                if "ar" in ins:
                    st.markdown("### AR Insights")
                    for slide,bul in ins["ar"].items():
                        with st.expander(slide):
                            for b in bul:
                                st.markdown(f"• {b}")

            # LOG PANEL (JUDGES LOVE THIS)
            with tab3:

                st.write("Debug Snapshot")
                st.json(results)

            # DOWNLOAD
            with tab4:

                if os.path.exists(ppt_path):
                    with open(ppt_path,"rb") as f:
                        st.download_button(
                            "📥 Download Executive PPT",
                            f,
                            "Finance_Control_Tower.pptx"
                        )

        except Exception as e:
            st.error(str(e))

else:
    st.info("Upload finance Excel to begin.")
