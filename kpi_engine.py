import pandas as pd
import numpy as np


# ============================================================
# JSON SAFE CONVERTER
# ============================================================

def _make_json_safe(obj):

    if isinstance(obj, dict):
        return {str(k): _make_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]

    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)

    elif pd.isna(obj):
        return 0

    else:
        return obj


# ============================================================
# MAIN KPI ENGINE (AP + AR)
# ============================================================

def compute_kpis(ap_df, ar_df):

    # ============================================================
    # ======================== AP SECTION ========================
    # ============================================================

    ap_df = ap_df.copy()

    ap_df["txn_date"] = pd.to_datetime(ap_df["txn_date"])
    ap_df["month_str"] = ap_df["txn_date"].dt.strftime("%Y-%m")

    # ---------------- SLIDE 1 – SPEND ----------------

    monthly_spend = (
        ap_df.groupby("month_str")["amount_inr"]
        .sum()
        .sort_index()
        .to_dict()
    )

    #--------------- Monthly Budget ----------------------------
    df_g = ap_df.groupby(['month_str','cost_center','business_unit','region','category']).agg({'amount_inr':'sum','planned_budget_inr':'max'}).reset_index()
    df_g = df_g.reset_index()
    df_g = df_g.groupby("month_str")['planned_budget_inr'].sum().sort_index()
    monthly_budget = df_g.to_dict()

    bu_region_combo = {}

    for bu in ap_df["business_unit"].dropna().unique():

        temp = ap_df[ap_df["business_unit"] == bu]

        monthly_total = (
            temp.groupby("month_str")["amount_inr"]
            .sum()
            .sort_index()
            .to_dict()
        )

        region_sum = (
            temp.groupby(["month_str", "region"])["amount_inr"]
            .sum()
            .reset_index()
        )

        if not region_sum.empty:

            region_sum["pct"] = (
                region_sum.groupby("month_str")["amount_inr"]
                .transform(lambda x: (x / x.sum()) * 100 if x.sum() != 0 else 0)
            )

            region_mix = (
                region_sum.pivot(
                    index="month_str",
                    columns="region",
                    values="pct"
                )
                .fillna(0)
                .sort_index()
            )

            region_pct = {
                str(m): {
                    str(r): float(region_mix.loc[m, r])
                    for r in region_mix.columns
                }
                for m in region_mix.index
            }

        else:
            region_pct = {}

        bu_region_combo[str(bu)] = {
            "monthly_total": monthly_total,
            "monthly_region_pct": region_pct
        }

    # ---------------- SLIDE 2 – OPERATIONAL ----------------

    processing_time_trend = (
        ap_df.groupby("month_str")["invoice_processing_days"]
        .mean()
        .sort_index()
        .to_dict()
    )

    late_payment_pct = (
        ap_df.groupby("month_str")["late_payment_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    dispute_pct = (
        ap_df.groupby("month_str")["dispute_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    # ---------------- SLIDE 3 – COMPLIANCE ----------------

    maverick_pct = (
        ap_df.groupby("month_str")["maverick_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    preferred_vendor_pct = (
        ap_df.groupby("month_str")["preferred_vendor_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    vendor_concentration_pct = (
        ap_df.groupby("vendor_name")["amount_inr"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .div(ap_df["amount_inr"].sum())
        .mul(100)
        .to_dict()
    )

    vendor_risk_avg = (
        ap_df.groupby("month_str")["vendor_risk_score"]
        .mean()
        .sort_index()
        .to_dict()
    )

    # ---------------- SLIDE 4 – WORKING CAPITAL ----------------

    ap_df["invoice_received_date"] = pd.to_datetime(ap_df["invoice_received_date"])
    ap_df["invoice_paid_date"] = pd.to_datetime(ap_df["invoice_paid_date"])
    ap_df["due_date"] = pd.to_datetime(ap_df["due_date"])

    ap_df["payment_days"] = (
        ap_df["invoice_paid_date"] - ap_df["invoice_received_date"]
    ).dt.days

    dpo_trend = (
        ap_df.groupby("month_str")["payment_days"]
        .mean()
        .sort_index()
        .to_dict()
    )

    ap_df["on_time_flag"] = (
        ap_df["invoice_paid_date"] <= ap_df["due_date"]
    ).astype(int)

    on_time_pct = (
        ap_df.groupby("month_str")["on_time_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    # monthly_budget = (
    #     ap_df.groupby("month_str")["planned_budget_inr"]
    #     .sum()
    #     .sort_index()
    # )

    monthly_actual = (
        ap_df.groupby("month_str")["amount_inr"]
        .sum()
        .sort_index()
    )

    # budget_variance_pct = (
    #     ((monthly_actual - monthly_budget) / monthly_budget.replace(0, np.nan)) * 100
    # ).fillna(0).to_dict()

    ap_kpis = {
        "monthly_spend_trend": monthly_spend,
        "monthly_budget": monthly_budget,
        "bu_region_combo": bu_region_combo,
        "processing_time_trend": processing_time_trend,
        "late_payment_pct": late_payment_pct,
        "dispute_pct": dispute_pct,
        "maverick_pct": maverick_pct,
        "preferred_vendor_pct": preferred_vendor_pct,
        "vendor_concentration_pct": vendor_concentration_pct,
        "vendor_risk_avg": vendor_risk_avg,
        "dpo_trend": dpo_trend,
        "on_time_pct": on_time_pct,
        # "budget_variance_pct": budget_variance_pct
    }

    # ============================================================
    # ======================== AR SECTION ========================
    # ============================================================

    ar_df = ar_df.copy()

    ar_df["invoice_date"] = pd.to_datetime(ar_df["invoice_date"])
    ar_df["month_str"] = ar_df["invoice_date"].dt.strftime("%Y-%m")

    # ---------------- Revenue Trend ----------------

    revenue_trend = (
        ar_df.groupby("month_str")["invoice_amount_inr"]
        .sum()
        .sort_index()
        .to_dict()
    )

    # ---------------- Collection Trend ----------------

    collection_trend = (
        ar_df.groupby("month_str")["paid_amount_inr"]
        .sum()
        .sort_index()
        .to_dict()
    )

    # ---------------- Collection Rate % ----------------

    collection_rate_pct = {}

    for m in revenue_trend:
        revenue = revenue_trend.get(m, 0)
        collection = collection_trend.get(m, 0)
        collection_rate_pct[m] = (collection / revenue * 100) if revenue != 0 else 0

    # ---------------- Segment Mix ----------------

    segment_revenue = (
        ar_df.groupby("segment")["invoice_amount_inr"]
        .sum()
    )

    segment_mix_pct = (
        segment_revenue /
        segment_revenue.sum() * 100
    ).to_dict()

    # ---------------- Segment Collection Rate ----------------

    segment_summary = ar_df.groupby("segment").agg({
        "invoice_amount_inr": "sum",
        "paid_amount_inr": "sum"
    })

    segment_summary["collection_rate_pct"] = (
        segment_summary["paid_amount_inr"] /
        segment_summary["invoice_amount_inr"] * 100
    )

    segment_collection_rate_pct = (
        segment_summary["collection_rate_pct"]
        .to_dict()
    )

    # ---------------- DSO ----------------

    ar_df["paid_date"] = pd.to_datetime(ar_df["paid_date"])

    ar_df["collection_days"] = (
        ar_df["paid_date"] - ar_df["invoice_date"]
    ).dt.days

    dso = ar_df["collection_days"].mean()

    # ---------------- Aging Distribution ----------------

    def aging_bucket(days):
        if days <= 30:
            return "0-30"
        elif days <= 60:
            return "31-60"
        elif days <= 90:
            return "61-90"
        else:
            return "90+"

    ar_df["aging_bucket"] = ar_df["days_overdue"].apply(aging_bucket)

    aging_distribution_pct = (
        ar_df.groupby("aging_bucket")["invoice_amount_inr"]
        .sum()
        .div(ar_df["invoice_amount_inr"].sum())
        .mul(100)
        .to_dict()
    )

    # ---------------- Late Payment % ----------------

    late_payment_pct = (
        ar_df.groupby("month_str")["late_payment_flag"]
        .mean()
        .mul(100)
        .sort_index()
        .to_dict()
    )

    ar_kpis = {
        "revenue_trend": revenue_trend,
        "collection_trend": collection_trend,
        "collection_rate_pct": collection_rate_pct,
        "segment_mix_pct": segment_mix_pct,
        "segment_collection_rate_pct": segment_collection_rate_pct,
        "dso": dso,
        "aging_distribution_pct": aging_distribution_pct,
        "late_payment_pct": late_payment_pct
    }


    return _make_json_safe({
        "ap_kpis": ap_kpis,
        "ar_kpis": ar_kpis
    })
