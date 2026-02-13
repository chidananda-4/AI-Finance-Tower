#from ap_unified_view import build_ap_view
from kpi_engine import compute_kpis
from finance_crew import run_finance_crew


def run_full_analysis(ap_df, ar_df):

    # ===============================
    # STEP 1: COMPUTE KPIs
    # ===============================

    kpis = compute_kpis(ap_df, ar_df)

    # ===============================
    # STEP 2: GENERATE INSIGHTS
    # ===============================

    insights = run_finance_crew(kpis)

    # ===============================
    # FINAL STRUCTURE
    # ===============================

    return {
        "ap_kpis": kpis["ap_kpis"],
        "ar_kpis": kpis["ar_kpis"],
        "insights": insights
    }
