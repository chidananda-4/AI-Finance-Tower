import json
from ap_unified_view import build_ap_view
from kpi_engine import compute_ap_kpis
from finance_crew import run_finance_crew


def make_json_serializable(obj):
    """
    Recursively convert numpy/pandas objects
    into JSON serializable types.
    """

    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]

    elif hasattr(obj, "item"):  # numpy scalar
        return obj.item()

    elif hasattr(obj, "tolist"):  # numpy array
        return obj.tolist()

    else:
        return obj


def run_full_analysis(file_path):
    """
    Main backend orchestrator:
    1. Build unified AP view
    2. Compute deterministic KPIs
    3. Run multi-agent insight generation
    4. Return structured output
    """

    # ==========================
    # STEP 1: BUILD UNIFIED VIEW
    # ==========================
    ap_view = build_ap_view(file_path)

    # ==========================
    # STEP 2: COMPUTE KPIs
    # ==========================
    ap_kpis = compute_ap_kpis(ap_view)

    # Ensure JSON-safe structure
    ap_kpis_clean = make_json_serializable(ap_kpis)

    # ==========================
    # STEP 3: GENERATE INSIGHTS
    # ==========================
    ap_insights = run_finance_crew(ap_kpis_clean)

    # ==========================
    # STEP 4: FINAL OUTPUT
    # ==========================
    final_output = {
        "ap_kpis": ap_kpis_clean,
        "ap_insights": ap_insights
    }

    return final_output




=== Budget Variance %:
== {json.dumps(ap["budget_variance_pct"], indent=2)}