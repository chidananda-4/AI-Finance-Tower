# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
from openai import OpenAI
import os
import matplotlib.pyplot as plt
# %matplotlib inline
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.dml.color import RGBColor
from io import BytesIO
import io
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches
import matplotlib.ticker as ticker
from pptx.enum.text import MSO_AUTO_SIZE,MSO_VERTICAL_ANCHOR
import seaborn as sns
import json

def slide1_content(ap,ar_summary,budget,kpi,client):
    # 1.1  — Monthly Spend with Trendline
    img1a = BytesIO()
    monthly_spend = ap.groupby('month')['amount_inr'].sum()
    #monthly_spend.index = monthly_spend.index.to_timestamp()

    x = np.arange(len(monthly_spend))
    y = monthly_spend.values

    # Linear trend
    z = np.polyfit(x, y, 1)
    trend = np.poly1d(z)
    y_billion = y / 1e9
    trend_billion = trend(x) / 1e9

    plt.figure(figsize=(10,5))
    plt.plot(monthly_spend.index, y_billion, marker='o', label="Monthly Spend")
    plt.plot(monthly_spend.index, trend_billion, linestyle='--', linewidth=2, color='red', label="Trend Direction")

    for date, value in zip(monthly_spend.index, y_billion):
        plt.text(date, value + 0.001, f"{value:.2f}Bn", ha='center', va='bottom', fontsize=8)

    plt.title("Monthly Spend Trend with Direction")
    plt.ylabel("Spend (Billion INR)")
    plt.xlabel("Month")
    plt.legend()
    plt.grid(True)
    plt.xticks(monthly_spend.index, [d for d in monthly_spend.index], rotation=45)

    plt.tight_layout()
    plt.savefig(img1a, bbox_inches='tight',dpi=300)
    plt.close()
    img1a.seek(0)

    img1b = BytesIO()
    monthly_bu = ap.groupby(['month','business_unit'])['amount_inr'].sum().reset_index()

    pivot = monthly_bu.pivot(index='month', columns='business_unit', values='amount_inr').fillna(0)
    pivot = pivot.sort_index()

    # ======================
    # Plot Chart
    # ======================
    plt.figure(figsize=(10,5))

    # Convert PeriodIndex to string for plotting
    x_labels = [str(x) for x in pivot.index]

    for col in pivot.columns:
        # Convert spend to billions
        y_billion = pivot[col] / 1e9
        plt.plot(x_labels, y_billion, marker='o', label=col)
        # Annotate each point
        for i, value in enumerate(y_billion):
            plt.text(i, value + 0.002, f"{value:.2f}bn", ha='center', va='bottom', fontsize=8, color='black')

    plt.title("Monthly Spend Trend by Business Unit")
    plt.xlabel("Month")
    plt.ylabel("Spend (Billion INR)")
    plt.legend()
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(img1b, dpi=300,bbox_inches='tight')
    plt.close()
    img1b.seek(0)
    monthly_spend = ap.groupby('month').agg({'amount_inr':'sum'}).reset_index()
    monthly_spend['amount_inr'] = monthly_spend['amount_inr']/1e9

    months = sorted(monthly_bu['month'].unique())
    latest = months[-1]
    prev = months[-2]
    latest_month_spends_by_unit = monthly_bu[monthly_bu['month']==latest]
    prev_month_spends_by_unit = monthly_bu[monthly_bu['month']==prev]
    avg_monthly_spend = float(monthly_spend['amount_inr'].mean())

    summary_data = {
                "monthly_spend_data": monthly_spend.to_dict(orient="records"),
                "monthly_spend_by_business_unit_data": monthly_bu.to_dict(orient="records"),
                "latest_month_spends_by_unit":latest_month_spends_by_unit.to_dict(orient="records"),
                "prev_month_spends_by_unit":prev_month_spends_by_unit.to_dict(orient="records"),
                "average_monthly_spend" :avg_monthly_spend
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:

            - Identify peak month in spends and key business unit driver in spends and provide the percentage increase from the average monthly spend.
            - Identify lowest month in spends and get the reason by which the spends are low based on business unit and  provide the percentage decrease from the average monthly spend
            - Mention any structural pattern in business unit spends monthly
            - Mention the  trend in values and changes in each segment in INR
            - Compare the latest month spends by unit with previous month spends and give us the trend in values

            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights": [{{'peak_month': '',
       'key_business_unit_driver': '',
       'percentage_increase_from_average': ''}},
      {{'lowest_month': '',
       'reason_for_low_spend': '',
       'percentage_decrease_from_average': ''}},
      {{'structural_pattern': ''}},
      {{'trend_in_values': ''}},
      {{'latest_month_vs_previous': ''}} ]
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    insight1 = json.loads(response.choices[0].message.content)
    slide1_insight = f'''Spending was peak in {insight1['insights'][0]['peak_month']} with {insight1['insights'][0]['percentage_increase_from_average']} increase from average with key business unit driver as  {insight1['insights'][0]['key_business_unit_driver']}
    Due to  {insight1['insights'][1]['reason_for_low_spend']} ,observed  low spend in {insight1['insights'][1]['lowest_month']} with {insight1['insights'][1]['percentage_decrease_from_average']}
    {insight1['insights'][2]['structural_pattern']}
    {insight1['insights'][3]['trend_in_values']}
    {insight1['insights'][4]['latest_month_vs_previous']}'''

    return [img1a,img1b],slide1_insight

def slide2_content(ap,ar_summary,budget,kpi,client):

    region_colors = {
        'East':  '#5fa2ce',  # medium blue
        'West':  '#ff9900',  # medium orange
        'North': '#60b35a',  # medium green
        'South': '#e15759'   # medium red
    }
    
    agg = ap.groupby(['business_unit', 'month', 'region'])['amount_inr'].sum().reset_index()
    
    slide2_insight = ''
    images = []
    
    for bu in agg['business_unit'].dropna().unique():
    
        img_bu = BytesIO()
    
        seg_region_data = agg[agg['business_unit'] == bu]
        seg_data = seg_region_data.groupby(['business_unit','month'])['amount_inr'].sum().reset_index()
    
        # Pivot table (Actual Spend Values)
        pivot = seg_region_data.pivot_table(
            index='month',
            columns='region',
            values='amount_inr',
            aggfunc='sum',
            fill_value=0
        ).sort_index()
    
        # Ensure consistent region order
        pivot = pivot.reindex(columns=region_colors.keys(), fill_value=0)
    
        # -------------------------------
        # ✅ Total Spend (Actual bn INR)
        # -------------------------------
        total_spend_bn = pivot.sum(axis=1) / 1e9
    
        # -------------------------------
        # ✅ Convert to 100% Stacked Values
        # -------------------------------
        pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
        # -------------------------------
        # Plot Chart
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))
    
        # ✅ 100% Stacked Bar Plot
        pivot_percent.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            legend=True,
            color=[region_colors[r] for r in pivot_percent.columns]
        )
    
        # -------------------------------
        # ✅ Total Spend Line (bn INR)
        # -------------------------------
        ax.plot(
            range(len(total_spend_bn)),
            total_spend_bn.values,
            marker='o',
            linestyle='--',
            linewidth=2,
            color='black',
            label='Total Spend (bn INR)'
        )
    
        # -------------------------------
        # ✅ Add % Labels inside Bars
        # -------------------------------
        for i, row in enumerate(pivot_percent.values):
            bottom = 0
            for j, val in enumerate(row):
                if val > 0:
                    ax.text(
                        i,
                        bottom + val / 2,
                        f"{val:.0f}%",
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='white'
                    )
                bottom += val
    
        # -------------------------------
        # ✅ Annotate Total Spend on Line
        # -------------------------------
        for i, value in enumerate(total_spend_bn.values):
            ax.text(
                i,
                102,   # slightly above 100%
                f"{value:.2f}bn",
                ha='center',
                va='bottom',
                fontsize=8,
                color='black'
            )
    
        # -------------------------------
        # Titles and Labels
        # -------------------------------
        ax.set_title(f"Monthly Spend Share by Region (100%) — {bu}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Region Share (%)")
    
        ax.set_ylim(0, 110)  # 100% + space for total labels
    
        ax.set_xticks(range(len(pivot_percent.index)))
        ax.set_xticklabels(pivot_percent.index, rotation=45)
    
        # -------------------------------
        # Legend Fix (Bottom Center)
        # -------------------------------
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.18),
            ncol=5,
            fontsize=9
        )
    
        ax.grid(axis='y', linestyle='--', alpha=0.5)
    
        plt.tight_layout()
    
        # -------------------------------
        # Save Chart Image
        # -------------------------------
        plt.savefig(img_bu, dpi=300)
        plt.close()
    
        img_bu.seek(0)
        images.append(img_bu)
  
        seg_region_data['region_pct'] = (
            seg_region_data['amount_inr'] /
            seg_region_data.groupby(['business_unit', 'month'])['amount_inr'].transform('sum')) * 100
        summary_data = {
                    'segment_name':bu,
                    "segment_monthly_data": seg_data.to_dict(orient="records"),
                    "segment_region_monthly_data": seg_region_data.to_dict(orient="records")}
        prompt = f"""
                You are a senior financial analyst.

                Analyze the Monthly Spend performance data in the given segment which contains regions below.

                DATA:
                {json.dumps(summary_data)}

                Generate insights for a PowerPoint slide:

                - Identify the  peak and lowest  spend percentages across regions mix.

                Return the above insights as a paragraph.

                Return ONLY JSON in this format:

                {{
                  "segment_name": "",
                  "insights": ''
                }}

                Keep insights concise and executive-level.
                No markdown.
                """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        seg_insight = json.loads(response.choices[0].message.content)
        insights = f'''{seg_insight['segment_name']} : {seg_insight['insights']}'''+'\n'
        slide2_insight = slide2_insight + insights

    return images,slide2_insight

def slide3_content(ap,ar_summary,budget,kpi,client):
    # Filter for month 2025-12
    img3a = BytesIO()
    latest = sorted(ap['month'].unique())[-1]
    ap_latest = ap[ap['month'] == latest ]

    # Prepare data
    cat_sub = ap_latest.groupby(['category', 'sub_category'])['amount_inr'].sum().reset_index()
    pivot = cat_sub.pivot(index='category', columns='sub_category', values='amount_inr').fillna(0)

    # Convert spend to millions
    pivot_million = pivot / 1e6

    fig, ax = plt.subplots(figsize=(12, 7))

    bottom = np.zeros(len(pivot_million))
    x = np.arange(len(pivot_million.index))

    for sub_cat in pivot_million.columns:
        values = pivot_million[sub_cat].values
        bars = ax.bar(x, values, bottom=bottom, label=sub_cat)
        # Add sub-category name above amount and % in the middle of each segment (horizontal)
        for i, (b, v) in enumerate(zip(bars, values)):
            if v > 0:
                total = pivot_million.iloc[i].sum()
                percent = v / total * 100
                label = f"{sub_cat}\n{v:,.2f} Mn, ({percent:.1f}%)"
                ax.text(
                    b.get_x() + b.get_width()/2,
                    bottom[i] + v/2,
                    label,
                    ha='center', va='center', fontsize=9, color='white', rotation=0
                )
        bottom += values

    ax.set_xticks(x)
    ax.set_xticklabels(pivot_million.index)
    ax.set_title("Spend by Category and Sub-Category (Stacked) — Dec 2025")
    ax.set_xlabel("Category")
    ax.set_ylabel("Spend (Million INR)")
    ax.legend(title="Sub-Category")
    plt.tight_layout()
    plt.savefig(img3a, dpi=300)
    img3a.seek(0)
    plt.close()

    # 2. Spend by Category (Donut Chart) for December
    img3b = BytesIO()

    cat_spend_dec = ap_latest.groupby('category')['amount_inr'].sum().sort_values(ascending=False)

    plt.figure(figsize=(7,7))
    plt.pie(cat_spend_dec, labels=cat_spend_dec.index, autopct='%1.1f%%', startangle=90)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.title("Spend by Category — Dec 2025")
    plt.savefig(img3b, dpi=300)
    img3b.seek(0)
    plt.close()


    img3c = BytesIO()

    heat_cat = ap.groupby(['category','month'])['amount_inr'].sum().unstack().fillna(0)

    plt.figure(figsize=(10,6))
    sns.heatmap(heat_cat, cmap="YlOrRd")
    plt.title("Spend Heatmap — Category vs Month")
    plt.tight_layout()
    plt.savefig(img3c, dpi=300)
    img3c.seek(0)
    plt.close()

    summary_data = {
                "Spend_by_category_dec25": cat_spend_dec.reset_index().to_dict(orient="records"),
                "monthly_spend_by_business_unit_data": heat_cat.reset_index().to_dict(orient="records"),
                "latest_month":latest
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:
            - Identify top 3 spender category for latest_month and mention % of total spend & amount spend in million
            - Mention the  trend in values and changes in each category month-on-month in INR

            Return the above insights as a paragraph.
            Return ONLY JSON in this format:

            {{
              "insights": ''
            }}

            Keep insights concise and executive-level.
            give response in 5 lines
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    insight3 = json.loads(response.choices[0].message.content)
    slide3_insight = insight3['insights'].replace('. ', '.\n')

    return [img3c,img3b,img3a],slide3_insight

def slide4_content(ap,ar_summary,budget,kpi,client):

    latest = sorted(ap['month'].unique())[-1]
    prev = sorted(ap['month'].unique())[-2]

    # Aggregate Actual Spend
    actual = ap.groupby(
        ['month','cost_center','business_unit','region','category']
    )['amount_inr'].sum().reset_index()
    # Convert 'month' to string/object in both DataFrames
    budget['month'] = budget['month'].astype(str)
    actual['month'] = actual['month'].astype(str)

    # Merge Budget & Actual
    merged = actual.merge(
        budget,
        on=['month','cost_center','business_unit','region','category'],
        how='left'
    )

    merged['variance'] = merged['amount_inr'] - merged['planned_budget_inr']
    merged['utilization_pct'] = merged['amount_inr'] / merged['planned_budget_inr']

    # Group by month and convert to billions
    monthly = merged.groupby('month')[['amount_inr','planned_budget_inr']].sum() / 1e9

    # Linear trend for actual spend
    x = np.arange(len(monthly))
    y = monthly['amount_inr'].values
    z = np.polyfit(x, y, 1)
    trend = np.poly1d(z)
    trend_line = trend(x)

    plt.figure(figsize=(10,5))
    plt.plot(monthly.index, monthly['amount_inr'], marker='o', label='Actual Spend')
    plt.plot(monthly.index, monthly['planned_budget_inr'], marker='o', label='Budget')
    plt.plot(monthly.index, trend_line, linestyle='--', linewidth=2, color='orange', label='Actual Spend Trend')

    # Annotate spend for each month (Actual)
    for i, (month, row) in enumerate(monthly.iterrows()):
        plt.text(month, row['amount_inr'] + 0.002, f"{row['amount_inr']:.2f}Bn",
                 ha='center', va='bottom', fontsize=9, color='blue')

    # Annotate budget for each month (Budget)
    for i, (month, row) in enumerate(monthly.iterrows()):
        plt.text(month, row['planned_budget_inr'] + 0.002, f"{row['planned_budget_inr']:.2f}Bn",
                 ha='center', va='bottom', fontsize=9, color='green')

    plt.title("Monthly Budget vs Actual (Line Chart)")
    plt.ylabel("INR (Billion)")
    plt.xlabel("Month")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    img4a = BytesIO()
    plt.savefig(img4a, dpi=300)
    img4a.seek(0)
    plt.close()
    # Chart 2 — Variance Heatmap (Cost Center × Month)
    img4b = BytesIO()

    heat = merged.pivot_table(
        values='variance',
        index='cost_center',
        columns='month',
        aggfunc='sum'
    )

    plt.figure(figsize=(10,6))
    sns.heatmap(heat, cmap="RdYlGn", center=0)
    plt.title("Budget Variance Heatmap (Cost Center vs Month)")

    plt.savefig(img4b, dpi=300)
    img4b.seek(0)
    plt.close()

    img4c = BytesIO()

    # Filter for Nov and Dec only
    months_to_plot = [prev, latest]
    filtered = merged[merged['month'].isin(months_to_plot)]

    # Group and calculate utilization
    cat = filtered.groupby(['category', 'month'])[['amount_inr', 'planned_budget_inr']].sum().reset_index()
    cat['utilization_pct'] = cat['amount_inr'] / cat['planned_budget_inr'] * 100

    # Pivot for plotting
    pivot = cat.pivot(index='category', columns='month', values='utilization_pct').fillna(0)

    # Plot grouped horizontal bar chart
    categories = pivot.index
    y = np.arange(len(categories))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.barh(y - bar_width/2, pivot[months_to_plot[0]], bar_width, label=f'Utilization {months_to_plot[0]}')
    bars2 = ax.barh(y + bar_width/2, pivot[months_to_plot[1]], bar_width, label=f'Utilization {months_to_plot[1]}')

    # Annotate utilization values at the end of each bar
    for bars in [bars1, bars2]:
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}%', va='center', ha='left', fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(categories)
    ax.set_xlabel('Utilization (%)')
    ax.set_title('Budget Utilization by Category (Nov & Dec 2025)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(img4c, dpi=300)
    img4c.seek(0)
    plt.close()
    budget_monthly = merged.groupby('month')[['amount_inr','planned_budget_inr']].sum() / 1e9
    cost_heat_df = (
        merged
        .groupby(['cost_center', 'month'], as_index=False)['amount_inr']
        .sum()
    )
    cat_budget_util=cat[['category','month','utilization_pct']]

    summary_data = {
                "month_spend_by_planned_budget": budget_monthly.to_dict(orient="records"),
                "month_spend_in_risk_bucket_by_region_by_costcenter": cost_heat_df.to_dict(orient="records"),
                "monhtly Budget utilization by category ": cat_budget_util.to_dict(orient="records"),
                "latest_month":latest,
                "previous_month":prev
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:
            - Trend comparsion of budget and monhtly spend month on month in 1 line
            - what are the top 5 cost center leading to exceed of budget covering how much overspend in percentage
            - Whats are the categories which are over utilising the budget
            - Compare the latest month budget utilization by category with previous

            Return the above insights as a paragraph.
            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights":''
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    insight4 = json.loads(response.choices[0].message.content)
    slide4_insight = insight4['insights'].replace('. ', '.\n')

    return [img4a,img4b,img4c],slide4_insight

def slide5_content(ap,ar_summary,budget,kpi,client):
    img5b = BytesIO()
    latest = sorted(ap['month'].unique())[-1]
    prev = sorted(ap['month'].unique())[-2]

    # Calculate thresholds using all data
    low_thresh = ap['vendor_risk_score'].quantile(1/3)
    med_thresh = ap['vendor_risk_score'].quantile(2/3)

    def risk_bucket(x):
        if x <= low_thresh:
            return "Low"
        elif x <= med_thresh:
            return "Medium"
        else:
            return "High"

    ap['risk_bucket'] = ap['vendor_risk_score'].apply(risk_bucket)
    ap['month'] = ap['txn_date'].dt.to_period('M')

    # Filter for Nov and Dec 2025
    ap['month'] = ap['month'].astype(str).str.strip()
    ap_nov_dec = ap[ap['month'].isin(['2025-11', '2025-12'])].copy()
    ap_nov_dec['amount_inr_million'] = ap_nov_dec['amount_inr'] / 1e6

    # Ensure all combinations exist
    regions = ap_nov_dec['region'].unique()
    risk_buckets = ['Low', 'Medium', 'High']
    months = ['2025-11', '2025-12']

    # Pivot: Region × Risk × Month
    heat = ap_nov_dec.pivot_table(
        values='amount_inr_million',
        index='region',
        columns=['month', 'risk_bucket'],
        aggfunc='sum'
    ).reindex(index=regions, columns=pd.MultiIndex.from_product([months, risk_buckets]), fill_value=0)

    # Plot heatmaps for Nov and Dec side by side
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for i, month in enumerate(months):
        data = heat[month]
        if data.size == 0 or data.isnull().all().all():
            axes[i].set_title(f"No data for {month}")
            axes[i].axis('off')
        else:
            sns.heatmap(
                data,
                annot=True, fmt=".2f", cmap="Reds",
                ax=axes[i], cbar=i==1
            )
            axes[i].set_title(f"Risk Exposure by Region — {month} (INR Million)")
            axes[i].set_xlabel("Risk Bucket")
            if i == 0:
                axes[i].set_ylabel("Region")
            else:
                axes[i].set_ylabel("")

    plt.tight_layout()
    plt.savefig(img5b, dpi=300)
    img5b.seek(0)
    plt.close()


    # --- Calculate % contribution within each month ---
    img5a = BytesIO()

    pivot = ( ap.groupby(['month','payment_terms_days'])['amount_inr'] .sum() .unstack() ) / 1e9
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    ax = pivot.plot(kind='bar', stacked=True, figsize=(10,5))

    # --- Annotate % inside bars ---
    for i, month in enumerate(pivot.index):
        cumulative = 0
        for j, col in enumerate(pivot.columns):
            val = pivot.loc[month, col]
            pct = pivot_pct.loc[month, col]

            if val > 0:   # avoid labeling empty segments
                y_pos = cumulative + val/2
                ax.text(i, y_pos, f"{pct:.1f}%", ha='center', va='center', fontsize=8, color='white')
                cumulative += val

    plt.title("Spend Composition by Payment Terms (Monthly)")
    plt.ylabel("Total Spend (Billions)")
    plt.xlabel("Month")
    plt.tight_layout()
    plt.savefig(img5a, dpi=300)
    img5a.seek(0)
    plt.close()

    spend_compo = (
        ap.groupby(['payment_terms_days','month'])['amount_inr']
        .sum()
        .reset_index()
    )

    spend_compo['amount_prop_pct'] = (
        spend_compo['amount_inr'] /
        spend_compo.groupby('month')['amount_inr'].transform('sum')
    ) * 100

    heat_risk = (
        ap_nov_dec
        .groupby(['region', 'month', 'risk_bucket'], as_index=False)['amount_inr_million']
        .sum()
        .fillna(0)
    )

    summary_data = {
                "month_spend_by_payment_terms_days": spend_compo.to_dict(orient="records"),
                "month_spend_in_risk_bucket_by_region": heat_risk.to_dict(orient="records"),
                "latest_month":latest,
                "previous_month":prev
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:
            - Identify the payment_terms_days having most spends, give % in 2 decimals & amounts in billion
             and Identify peak month in spends and key business unit driver in spends and provide the percentage increase from the average monthly spend.
             and Compare the latest month spends with previous month spends within by payment_terms_days and give us the trend in values & percentage as well .
            and Identify the regions spending in high & low risk bucket and comparing it with latest month

            Return the above insights as a paragraph.

            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights":""
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    insight5 = json.loads(response.choices[0].message.content)
    slide5_insight = insight5['insights'].replace('. ', '.\n')

    return [img5a,img5b],slide5_insight

def slide6_content(ap,ar_summary,budget,kpi,client):
    img6a = BytesIO()
    # --- Create Month column ---
    kpi['month'] = pd.to_datetime(kpi['week_start']).dt.to_period('M').astype(str)

    # --- Aggregate monthly ---
    monthly = (
        kpi.groupby('month')[['total_spend_inr', 'maverick_spend_inr']]
        .sum()
        .sort_index()   # ensures months are in order
    )

    # --- Non-Maverick spend ---
    monthly['non_maverick_spend'] = (
        monthly['total_spend_inr'] - monthly['maverick_spend_inr']
    )

    # --- Convert to % of total spend ---
    pct = monthly[['maverick_spend_inr', 'non_maverick_spend']].div(
        monthly['total_spend_inr'], axis=0
    ) * 100

    # =========================================================
    # Plot 100% stacked bar (Maverick at TOP, Non-Maverick bottom)
    # =========================================================
    ax = pct[['non_maverick_spend', 'maverick_spend_inr']].plot(
        kind='bar',
        stacked=True,
        figsize=(10, 5),
    )

    # --- Add % labels inside bars ---
    for i, month in enumerate(pct.index):
        cum_val = 0
        for col in ['non_maverick_spend', 'maverick_spend_inr']:  # order matters
            val = pct.loc[month, col]
            if val > 0:
                ax.text(
                    i,
                    cum_val + val / 2,
                    f"{val:.1f}%",
                    ha='center',
                    va='center',
                    fontsize=9,
                    color='white'
                )
                cum_val += val

    # --- Formatting ---
    plt.title("Monthly Spend Composition (Maverick vs Non-Maverick)")
    plt.ylabel("% of Total Spend")
    plt.xlabel("Month")
    plt.ylim(0, 100)
    plt.legend(["Non-Maverick %", "Maverick %"])
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()

    # --- Save ---
    plt.savefig(img6a, dpi=300)
    img6a.seek(0)
    plt.close()

    img6b = BytesIO()
    # --- Aggregate spend ---
    bu_pref = (
        ap.groupby(['region','preferred_vendor_flag'])['amount_inr']
        .sum()
        .unstack(fill_value=0)
    )

    # --- Convert spend to Millions for plotting ---
    bu_pref_mn = bu_pref / 1_000_000

    # --- % split within each Business Unit (for labels only) ---
    bu_pref_pct = bu_pref.div(bu_pref.sum(axis=1), axis=0) * 100

    # --- Plot stacked bar (absolute spend in Millions) ---
    ax = bu_pref_mn.plot(
        kind='bar',
        stacked=True,
        figsize=(8,5)
    )

    plt.title("Spend by region (Preferred vs Non-Preferred)")
    plt.ylabel("Spend (INR Millions)")

    # -------------------------------------------------
    # Add % labels inside bars
    # -------------------------------------------------
    for i, bu in enumerate(bu_pref.index):
        cum_val = 0
        for col in bu_pref.columns:   # 0 then 1
            height = bu_pref_mn.loc[bu, col]
            pct_val = bu_pref_pct.loc[bu, col]

            if height > 0:
                ax.text(
                    i,
                    cum_val + height/2,
                    f"{pct_val:.1f}%",
                    ha='center',
                    va='center',
                    color='white',
                    fontsize=9,
                    fontweight='bold'
                )
                cum_val += height

    # --- Formatting ---
    plt.legend(["Non-Preferred (0)", "Preferred (1)"])
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()

    # --- Save ---
    plt.savefig(img6b, dpi=300)
    img6b.seek(0)
    plt.close()

    img6c = BytesIO()
    # --- Prepare data (remove duplicate transactions) ---
    plot_data = ap.drop_duplicates('txn_id')

    plt.figure(figsize=(8,6))

    sns.countplot(
        data=plot_data,
        x="preferred_vendor_flag",
        hue="maverick_flag"
    )

    plt.title("Transaction Count by Preferred Vendor and Maverick Flag")
    plt.xlabel("Preferred Vendor Flag")
    plt.ylabel("Number of Transactions")

    plt.legend(title="Maverick Flag", labels=["0", "1"])

    plt.tight_layout()
    plt.savefig(img6c, dpi=300)
    img6c.seek(0)
    plt.close()

    region_pref = (
        ap.groupby(['region','preferred_vendor_flag'])['amount_inr']
        .sum()
        .reset_index()
    )
    region_pref['pct_within_region'] = (
        region_pref['amount_inr'] /
        region_pref.groupby('region')['amount_inr'].transform('sum')
    ) * 100

    maverick_vendor = (
        ap.groupby(['preferred_vendor_flag', 'maverick_flag'])['txn_id']
        .nunique()
        .reset_index(name='distinct_txn_count')
    )

    summary_data = {
                "month_spend_propotion % in maverick & non maverick ": pct.reset_index().to_dict(orient="records"),
                "month_spend_in_region_by_preferred_vendor_flag": region_pref.to_dict(orient="records"),
                "Txn count based on preferred_vendor_flag and maverick_flag": maverick_vendor.to_dict(orient="records"),
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:
            - Identify the trend of maverick propotion month on month
            - Identify trend of region wise preferred to non-preferred vendors spend
            - Quanity the count of maverick to non-maverick transactions for preferred_vendor_flag
            - Also reasoning why 0 maverick transaction for preferred_vendor

            Return the above insights as a paragraph.
            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights":''
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    insight6 = json.loads(response.choices[0].message.content)
    slide6_insight = insight6['insights'].replace('. ', '.\n')

    return [img6a,img6b,img6c],slide6_insight

def slide7_content(ap,ar_summary,budget,kpi,client):

    img7c = BytesIO()

    terms = ap.groupby('payment_terms_days')['invoice_processing_days'].mean()

    terms.plot(marker='o', figsize=(6,4))
    plt.title("Processing Days vs Payment Terms")
    plt.ylabel("Avg Days")
    plt.tight_layout()
    plt.savefig(img7c, dpi=300)
    img7c.seek(0)
    plt.close()

    img7b = BytesIO()

    heat = ap.groupby(['month','payment_terms_days'])['late_payment_flag'].mean().unstack()

    plt.figure(figsize=(8,5))
    sns.heatmap(heat*100, annot=True, fmt=".1f", cmap="Reds")
    plt.title("Late Payment % — Month vs Payment Terms")
    plt.xlabel("Payment Terms (Days)")
    plt.ylabel("Month")
    plt.tight_layout()
    plt.savefig(img7b, dpi=300)
    img7b.seek(0)
    plt.close()

    img7a = BytesIO()

    ap['proc_bucket'] = pd.cut(
        ap['invoice_processing_days'],
        bins=[0,3,5,7,10,20],
        labels=['0-3','3-5','5-7','7-10','10+']
    )

    # --- Create pivot table (Month × Bucket) ---
    heatmap_data = (
        ap.groupby(['month','proc_bucket'])['late_payment_flag']
        .mean()
        .unstack()
    )

    # --- Plot Heatmap ---
    plt.figure(figsize=(10,5))
    sns.heatmap(
        heatmap_data,
        annot=True,           # show values
        fmt=".2f",            # 2 decimal places
        cmap="Reds",          # darker = higher late probability
        linewidths=0.5
    )

    plt.title("Late Payment Probability Heatmap\n(Month × Invoice Processing date Bucket)")
    plt.xlabel("Processing Time Bucket (Days)")
    plt.ylabel("Month")
    plt.tight_layout()
    plt.savefig(img7a, dpi=300)
    img7a.seek(0)
    plt.close()

    late_pay = (
        ap.groupby(['payment_terms_days','month'])['late_payment_flag']
        .mean()
        .mul(100)
        .rename('late_payment_percentage')
        .reset_index()
    )
    proc_prob = (
        ap.groupby(['month','proc_bucket'])['late_payment_flag']
        .mean()
        .rename('late_payment_probability')
        .reset_index()
    )

    summary_data_slide7 = {
                "Average_invoice_processing_day_by_payment_terms_days ": terms.reset_index().to_dict(orient="records"),
                "% of late_payment monthly by payment_terms_days ": late_pay.to_dict(orient="records"),
                "Monhtly late_payment_probability for processing time bucket ": proc_prob.to_dict(orient="records"),
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Spend performance data below.

            DATA:
            {json.dumps(summary_data_slide7)}

            Generate insights for a PowerPoint slide:
            - Identify the relationship of & late_payment monthly by payment_terms_days
            - Identify trend of Monhtly late_payment_probability for processing time bucket
            - Also reasoning for trend of Average_invoice_processing_day_by_payment_terms_days
            Return the above insights as a paragraph.
            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights":''
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    insight7 = json.loads(response.choices[0].message.content)
    slide7_insight = insight7['insights'].replace('. ', '.\n')

    return [img7a,img7b,img7c],slide7_insight

def slide8_content(ap,ar_summary,budget,kpi,client):
    # 8.1  — Monthly Invoice with Trendline
    img8a = BytesIO()
    monthly_invoice = ar_summary.groupby('month')['ar_invoiced_inr'].sum()
    #monthly_spend.index = monthly_spend.index.to_timestamp()

    x = np.arange(len(monthly_invoice))
    y = monthly_invoice.values

    # Linear trend
    z = np.polyfit(x, y, 1)
    trend = np.poly1d(z)
    y_billion = y / 1e9
    trend_billion = trend(x) / 1e9

    plt.figure(figsize=(10,5))
    plt.plot(monthly_invoice.index, y_billion, marker='o', label="Monthly Invoice")
    plt.plot(monthly_invoice.index, trend_billion, linestyle='--', linewidth=2, color='red', label="Trend Direction")

    for date, value in zip(monthly_invoice.index, y_billion):
        plt.text(date, value + 0.0004, f"{value:.2f}Bn", ha='center', va='bottom', fontsize=8)

    plt.title("Monthly Invoice Trend with Direction")
    plt.ylabel("Invoice (Billion INR)")
    plt.xlabel("Month")
    plt.legend()
    plt.grid(True)
    plt.xticks(monthly_invoice.index, [d for d in monthly_invoice.index], rotation=45)

    plt.tight_layout()
    plt.savefig(img8a, bbox_inches='tight',dpi=300)
    #plt.close()
    img8a.seek(0)
    monthly_invoice = ar_summary.groupby('month').agg({'ar_invoiced_inr':'sum'}).reset_index()
    plt.close()

    img8b = BytesIO()
    monthly_seg = ar_summary.groupby(['month','segment'])['ar_invoiced_inr'].sum().reset_index()

    pivot = monthly_seg.pivot(index='month', columns='segment', values='ar_invoiced_inr').fillna(0)
    pivot = pivot.sort_index()

    # ======================
    # Plot Chart
    # ======================
    plt.figure(figsize=(10,5))

    # Convert PeriodIndex to string for plotting
    x_labels = [str(x) for x in pivot.index]

    for col in pivot.columns:
        # Convert spend to billions
        y_billion = pivot[col] / 1e9
        plt.plot(x_labels, y_billion, marker='o', label=col)
        # Annotate each point
        for i, value in enumerate(y_billion):
            plt.text(i, value + 0.002, f"{value:.2f}bn", ha='center', va='bottom', fontsize=8, color='black')

    plt.title("Monthly Invoice Trend by Segment")
    plt.xlabel("Month")
    plt.ylabel("Invoice (Billion INR)")
    plt.legend()
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(img8b, dpi=300,bbox_inches='tight')
    plt.close()
    img8b.seek(0)

    months = sorted(monthly_seg['month'].unique())
    latest = months[-1]
    prev = months[-2]
    monthly_invoice['ar_invoiced_inr'] = monthly_invoice['ar_invoiced_inr']/1e9
    latest_monthly_invoice = monthly_invoice[monthly_invoice['month'] == latest]
    
    latest_month_invoice_by_seg = monthly_seg[monthly_seg['month']==latest]
    prev_month_invoice_by_seg = monthly_seg[monthly_seg['month']==prev]
    avg_monthly_invoice = float(monthly_invoice['ar_invoiced_inr'].mean())

    summary_data = {
                "monthly_invoice_data": monthly_invoice.to_dict(orient="records"),
                "latest_month_invoice" : latest_monthly_invoice.to_dict(orient="records"),
                "monthly_invoice_by_segment": monthly_seg.to_dict(orient="records"),
                "latest_month_invoice_by_segment":latest_month_invoice_by_seg.to_dict(orient="records"),
                "prev_month_invoice_by_segment":prev_month_invoice_by_seg.to_dict(orient="records"),
                "average_monthly_invoice" :avg_monthly_invoice
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Invoiced performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:

            - Identify peak month in invoice amount and key business segment driver in invoices and provide the percentage increase from the average monthly invoice.
            - Identify lowest month in invoices and get the reason by which the invoices are low based on business segment and  provide the percentage decrease from the average monthly invoices
            - Mention any structural pattern in business unit invoice monthly
            - Mention the  trend in values and changes in each segment in INR
            - Compare the latest month invoices by segment with previous month invoices

            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights": [{{'peak_month': '',
       'key_business_unit_driver': '',
       'percentage_increase_from_average': ''}},
      {{'lowest_month': '',
       'reason_for_low_spend': '',
       'percentage_decrease_from_average': ''}},
      {{'structural_pattern': ''}},
      {{'trend_in_values': ''}},
      {{'latest_month_vs_previous': ''}} ]
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0)
    insight8 = json.loads(response.choices[0].message.content)
    slide8_insight = f'''Invoiced amount was peak in {insight8['insights'][0]['peak_month']} with {insight8['insights'][0]['percentage_increase_from_average']} increase from average with key business unit driver as  {insight8['insights'][0]['key_business_unit_driver']}
    Due to  {insight8['insights'][1]['reason_for_low_spend']} ,observed  low spend in {insight8['insights'][1]['lowest_month']} with {insight8['insights'][1]['percentage_decrease_from_average']} decrease from average.
    {insight8['insights'][2]['structural_pattern']}
    {insight8['insights'][3]['trend_in_values']}
    {insight8['insights'][4]['latest_month_vs_previous']}'''

    return [img8a,img8b],slide8_insight

def slide9_content(ap,ar_summary,budget,kpi,client):
    # Define fixed color mapping for regions
    region_colors = {
        'East':  '#5fa2ce',  # medium blue
        'West':  '#ff9900',  # medium orange
        'North': '#60b35a',  # medium green
        'South': '#e15759'   # medium red
    }
    invoice_agg = ar_summary.groupby(['month','segment','region'])['ar_invoiced_inr'].sum().reset_index()
    slide9_insight = ''
    images = []

    for bu in invoice_agg['segment'].dropna().unique():
        img_bu = BytesIO()

        seg_region_data = invoice_agg[invoice_agg['segment'] == bu]
        seg_data = seg_region_data.groupby(['segment','month'])['ar_invoiced_inr'].sum().reset_index()
        # Pivot table (Actual Spend Values)
        pivot = seg_region_data.pivot_table(
            index='month',
            columns='region',
            values='ar_invoiced_inr',
            aggfunc='sum',
            fill_value=0
        ).sort_index()
    
        # Ensure consistent region order
        pivot = pivot.reindex(columns=region_colors.keys(), fill_value=0)
    
        # -------------------------------
        # ✅ Total Spend (Actual bn INR)
        # -------------------------------
        total_spend_bn = pivot.sum(axis=1) / 1e9
    
        # -------------------------------
        # ✅ Convert to 100% Stacked Values
        # -------------------------------
        pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
        # -------------------------------
        # Plot Chart
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))
    
        # ✅ 100% Stacked Bar Plot
        pivot_percent.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            legend=True,
            color=[region_colors[r] for r in pivot_percent.columns]
        )
    
        # -------------------------------
        # ✅ Total Spend Line (bn INR)
        # -------------------------------
        ax.plot(
            range(len(total_spend_bn)),
            total_spend_bn.values,
            marker='o',
            linestyle='--',
            linewidth=2,
            color='black',
            label='Total Invoice (bn INR)'
        )
    
        # -------------------------------
        # ✅ Add % Labels inside Bars
        # -------------------------------
        for i, row in enumerate(pivot_percent.values):
            bottom = 0
            for j, val in enumerate(row):
                if val > 0:
                    ax.text(
                        i,
                        bottom + val / 2,
                        f"{val:.0f}%",
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='white'
                    )
                bottom += val
    
        # -------------------------------
        # ✅ Annotate Total Spend on Line
        # -------------------------------
        for i, value in enumerate(total_spend_bn.values):
            ax.text(
                i,
                102,   # slightly above 100%
                f"{value:.2f}bn",
                ha='center',
                va='bottom',
                fontsize=8,
                color='black'
            )
    
        # -------------------------------
        # Titles and Labels
        # -------------------------------
        ax.set_title(f"Monthly Spend Share by Region (100%) — {bu}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Region Share (%)")
    
        ax.set_ylim(0, 110)  # 100% + space for total labels
    
        ax.set_xticks(range(len(pivot_percent.index)))
        ax.set_xticklabels(pivot_percent.index, rotation=45)
    
        # -------------------------------
        # Legend Fix (Bottom Center)
        # -------------------------------
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.18),
            ncol=5,
            fontsize=9
        )
    
        ax.grid(axis='y', linestyle='--', alpha=0.5)
    
        plt.tight_layout()
    
        # -------------------------------
        # Save Chart Image
        # -------------------------------
        plt.savefig(img_bu, dpi=300)
        plt.close()
    
        img_bu.seek(0)
        images.append(img_bu)
        
        seg_region_data['region_pct'] = (
            seg_region_data['ar_invoiced_inr'] /
            seg_region_data.groupby(['segment', 'month'])['ar_invoiced_inr'].transform('sum')) * 100
        summary_data = {
                    'segment_name':bu,
                    "segment_monthly_data": seg_data.to_dict(orient="records"),
                    "segment_region_monthly_data": seg_region_data.to_dict(orient="records")}
        prompt = f"""
                You are a senior financial analyst.

                Analyze the Monthly Invoiced Amount performance data in the given segment which contains regions below.

                DATA:
                {json.dumps(summary_data)}

                Generate insights for a PowerPoint slide:

                - Identify the  peak and lowest  Invoiced amount percentages across regions mix.

                Return the above insights as a paragraph.
                Return ONLY JSON in this format:

                {{
                  "segment_name": "",
                  "insights": ''
                }}

                Keep insights concise and executive-level.
                No markdown.
                """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        seg_insight = json.loads(response.choices[0].message.content)
        insights = f'''{seg_insight['segment_name']} : {seg_insight['insights']}'''+'\n'
        slide9_insight = slide9_insight + insights

    return images,slide9_insight


def slide10_content(ap,ar_summary,budget,kpi,client):
    img10a = BytesIO()
    monthly_collection = ar_summary.groupby('month')['ar_collected_inr'].sum()
    #monthly_spend.index = monthly_spend.index.to_timestamp()

    x = np.arange(len(monthly_collection))
    y = monthly_collection.values

    # Linear trend
    z = np.polyfit(x, y, 1)
    trend = np.poly1d(z)
    y_million = y / 1e6
    trend_million = trend(x) / 1e6

    plt.figure(figsize=(10,5))
    plt.plot(monthly_collection.index, y_million, marker='o', label="Monthly Collections")
    plt.plot(monthly_collection.index, trend_million, linestyle='--', linewidth=2, color='red', label="Trend Direction")

    for date, value in zip(monthly_collection.index, y_million):
        plt.text(date, value + 0.0004, f"{value:.2f}Mn", ha='center', va='bottom', fontsize=8)

    plt.title("Monthly Collections Trend with Direction")
    plt.ylabel("Collections (Million INR)")
    plt.xlabel("Month")
    plt.legend()
    plt.grid(True)
    plt.xticks(monthly_collection.index, [d for d in monthly_collection.index], rotation=45)

    plt.tight_layout()
    plt.savefig(img10a, bbox_inches='tight',dpi=300)
    plt.close()
    img10a.seek(0)
    monthly_collection = ar_summary.groupby('month').agg({'ar_collected_inr':'sum'}).reset_index()

    img10b = BytesIO()
    monthly_seg_collections = ar_summary.groupby(['month','segment'])['ar_collected_inr'].sum().reset_index()

    pivot = monthly_seg_collections.pivot(index='month', columns='segment', values='ar_collected_inr').fillna(0)
    pivot = pivot.sort_index()

    # ======================
    # Plot Chart
    # ======================
    plt.figure(figsize=(10,5))

    # Convert PeriodIndex to string for plotting
    x_labels = [str(x) for x in pivot.index]

    for col in pivot.columns:
        # Convert spend to billions
        y_million = pivot[col] / 1e6
        plt.plot(x_labels, y_million, marker='o', label=col)
        # Annotate each point
        for i, value in enumerate(y_million):
            plt.text(i, value + 0.001, f"{value:.2f}Mn", ha='center', va='bottom', fontsize=8, color='black')

    plt.title("Monthly Collections Trend by Segment")
    plt.xlabel("Month")
    plt.ylabel("Collections (Million INR)")
    plt.legend()
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(img10b, dpi=300,bbox_inches='tight')
    plt.close()
    img10b.seek(0)

    months = sorted(monthly_seg_collections['month'].unique())
    latest = months[-1]
    prev = months[-2]
    monthly_collection['ar_collected_inr'] = monthly_collection['ar_collected_inr']/1e9
    latest_month_collection = monthly_collection[monthly_collection['month'] == latest]
    latest_month_collection_by_seg = monthly_seg_collections[monthly_seg_collections['month']==latest]
    prev_month_collection_by_seg = monthly_seg_collections[monthly_seg_collections['month']==prev]
    avg_monthly_collection = float(monthly_collection['ar_collected_inr'].mean())

    summary_data = {
                "monthly_collected_data": monthly_collection.to_dict(orient="records"),
                "monthly_collections_by_segment": monthly_seg_collections.to_dict(orient="records"),
                "latest_month_collection_by_segment":latest_month_collection_by_seg.to_dict(orient="records"),
                "prev_month_collection_by_segment":prev_month_collection_by_seg.to_dict(orient="records"),
                "average_monthly_collection" :avg_monthly_collection
            }
    prompt = f"""
            You are a senior financial analyst.

            Analyze the Monthly Collctions performance data below.

            DATA:
            {json.dumps(summary_data)}

            Generate insights for a PowerPoint slide:

            - Identify peak month in Collection amount and key business segment driver in collections and provide the percentage increase from the average monthly collection.
            - Identify lowest month in collections and get the reason by which the collections are low based on business segment and  provide the percentage decrease from the average monthly collections
            - Mention any structural pattern in business segment collections monthly
            - Mention the  trend in values and changes in each segment in INR
            - Compare the latest month collections by segment with previous month collections and give us the trend in values

            Return ONLY JSON in this format:

            {{
              "segment_name": "",
              "insights": [{{'peak_month': '',
       'key_business_unit_driver': '',
       'percentage_increase_from_average': ''}},
      {{'lowest_month': '',
       'reason_for_low_spend': '',
       'percentage_decrease_from_average': ''}},
      {{'structural_pattern': ''}},
      {{'trend_in_values': ''}},
      {{'latest_month_vs_previous': ''}} ]
            }}

            Keep insights concise and executive-level.
            No markdown.
            """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0)

    insight10 = json.loads(response.choices[0].message.content)
    slide10_insight = f'''Collections was peak in {insight10['insights'][0]['peak_month']} with {insight10['insights'][0]['percentage_increase_from_average']} increase from average with key business unit driver as  {insight10['insights'][0]['key_business_unit_driver']}
    Due to  {insight10['insights'][1]['reason_for_low_spend']} ,observed  low spend in {insight10['insights'][1]['lowest_month']} with {insight10['insights'][1]['percentage_decrease_from_average']} decrease from average.
    {insight10['insights'][2]['structural_pattern']}
    {insight10['insights'][3]['trend_in_values']}
    {insight10['insights'][4]['latest_month_vs_previous']}'''

    return [img10a,img10b],slide10_insight

def slide11_content(ap,ar_summary,budget,kpi,client):
    # Define fixed color mapping for regions
    region_colors = {
        'East':  '#5fa2ce',  # medium blue
        'West':  '#ff9900',  # medium orange
        'North': '#60b35a',  # medium green
        'South': '#e15759'   # medium red
    }
    collections_agg = ar_summary.groupby(['month','segment','region'])['ar_collected_inr'].sum().reset_index()
    slide11_insight = ''
    images = []

    for bu in collections_agg['segment'].dropna().unique():
        img_bu = BytesIO()

        seg_region_data = collections_agg[collections_agg['segment'] == bu]
        seg_data = seg_region_data.groupby(['segment','month'])['ar_collected_inr'].sum().reset_index()

        # Pivot for stacked bars
        pivot = seg_region_data.pivot_table(
            index='month',
            columns='region',
            values='ar_collected_inr',
            aggfunc='sum',
            fill_value=0
        ).sort_index()
    
        # Ensure consistent region order
        pivot = pivot.reindex(columns=region_colors.keys(), fill_value=0)
    
        # -------------------------------
        # ✅ Total Spend (Actual bn INR)
        # -------------------------------
        total_spend_bn = pivot.sum(axis=1) / 1e9
    
        # -------------------------------
        # ✅ Convert to 100% Stacked Values
        # -------------------------------
        pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100
    
        # -------------------------------
        # Plot Chart
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))
    
        # ✅ 100% Stacked Bar Plot
        pivot_percent.plot(
            kind='bar',
            stacked=True,
            ax=ax,
            legend=True,
            color=[region_colors[r] for r in pivot_percent.columns]
        )
    
        # -------------------------------
        # ✅ Total Spend Line (bn INR)
        # -------------------------------
        ax.plot(
            range(len(total_spend_bn)),
            total_spend_bn.values,
            marker='o',
            linestyle='--',
            linewidth=2,
            color='black',
            label='Total Collections (bn INR)'
        )
    
        # -------------------------------
        # ✅ Add % Labels inside Bars
        # -------------------------------
        for i, row in enumerate(pivot_percent.values):
            bottom = 0
            for j, val in enumerate(row):
                if val > 0:
                    ax.text(
                        i,
                        bottom + val / 2,
                        f"{val:.0f}%",
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='white'
                    )
                bottom += val
    
        # -------------------------------
        # ✅ Annotate Total Spend on Line
        # -------------------------------
        for i, value in enumerate(total_spend_bn.values):
            ax.text(
                i,
                102,   # slightly above 100%
                f"{value:.2f}bn",
                ha='center',
                va='bottom',
                fontsize=8,
                color='black'
            )
    
        # -------------------------------
        # Titles and Labels
        # -------------------------------
        ax.set_title(f"Monthly Collections Share by Region (100%) — {bu}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Region Share (%)")
    
        ax.set_ylim(0, 110)  # 100% + space for total labels
    
        ax.set_xticks(range(len(pivot_percent.index)))
        ax.set_xticklabels(pivot_percent.index, rotation=45)
    
        # -------------------------------
        # Legend Fix (Bottom Center)
        # -------------------------------
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.18),
            ncol=5,
            fontsize=9
        )
    
        ax.grid(axis='y', linestyle='--', alpha=0.5)
    
        plt.tight_layout()
    
        # -------------------------------
        # Save Chart Image
        # -------------------------------
        plt.savefig(img_bu, dpi=300)
        plt.close()
    
        img_bu.seek(0)
        images.append(img_bu)
        
        seg_region_data['region_pct'] = (
            seg_region_data['ar_collected_inr'] /
            seg_region_data.groupby(['segment', 'month'])['ar_collected_inr'].transform('sum')) * 100
        summary_data = {
                    'segment_name':bu,
                    "segment_monthly_data": seg_data.to_dict(orient="records"),
                    "segment_region_monthly_data": seg_region_data.to_dict(orient="records")}
        prompt = f"""
                You are a senior financial analyst.

                Analyze the Monthly Collected Amount performance data in the given segment which contains regions below.

                DATA:
                {json.dumps(summary_data)}

                Generate insights for a PowerPoint slide:

                - Identify the  peak and lowest  Collected amount percentages across regions mix.

                Return the above insights as a paragraph.
                Return ONLY JSON in this format:

                {{
                  "segment_name": "",
                  "insights": " "
                }}

                Keep insights concise and executive-level.
                No markdown.
              """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        seg_insight = json.loads(response.choices[0].message.content)
        insights = f"{seg_insight['segment_name']} : {seg_insight['insights']}\n"
        slide11_insight = slide11_insight + insights

    return images,slide11_insight


def exec_summary_slide(excel_file,client):
    ar = excel_file["AR_Invoices_Collections"]
    ap = excel_file["AP_Spend_Invoices"]
    
    # Month columns
    ar["month"] = pd.to_datetime(ar["invoice_date"]).dt.to_period("M")
    ap["month"] = pd.to_datetime(ap["txn_date"]).dt.to_period("M")
    
    
    # -------------------------------
    # AR MoM Summary
    # -------------------------------
    ar_mom = ar.groupby("month").agg(
        invoiced=("invoice_amount_inr", "sum"),
        collected=("paid_amount_inr", "sum"),
        overdue=("late_payment_flag", "sum")
    ).reset_index()
    
    ar_mom["collection_pct"] = ar_mom["collected"] / ar_mom["invoiced"] * 100
    
    # Latest + Previous month
    latest = ar_mom["month"].max()
    prev = ar_mom["month"].sort_values().iloc[-2]
    
    L = ar_mom[ar_mom["month"] == latest].iloc[0]
    P = ar_mom[ar_mom["month"] == prev].iloc[0]
    
    # -------------------------------
    # Drivers: Region + Segment
    # -------------------------------
    region_pending = ar.groupby("region").apply(
        lambda x: x["invoice_amount_inr"].sum() - x["paid_amount_inr"].sum()
    ).sort_values(ascending=False)
    
    segment_pending = ar.groupby("segment").apply(
        lambda x: x["invoice_amount_inr"].sum() - x["paid_amount_inr"].sum()
    ).sort_values(ascending=False)
    
    top_region = region_pending.index[0]
    top_segment = segment_pending.index[0]
    
    
    # -------------------------------
    # AP Spend Trend
    # -------------------------------
    ap_mom = ap.groupby("month").agg(
        spend=("amount_inr", "sum"),
        invoices=("txn_id", "count")
    ).reset_index()
    
    ap_latest = ap_mom[ap_mom["month"] == latest].iloc[0]
    ap_prev   = ap_mom[ap_mom["month"] == prev].iloc[0]

    def build_llm_prompt():
        return f"""
    You are a CFO-level finance strategy advisor.
    
    Generate a crisp ONE-SLIDE executive summary for senior officials.
    
    ### Context
    We are reviewing latest Month-over-Month Accounts Receivable and Payables performance.
    
    ### Latest Month: {latest}
    ### Previous Month: {prev}
    
    ---
    
    ## 1. Accounts Receivable (AR)
    
    - Invoiced: ₹{L['invoiced']/1e7:.2f} Cr (Prev: ₹{P['invoiced']/1e7:.2f} Cr)
    - Collected: ₹{L['collected']/1e7:.2f} Cr (Prev: ₹{P['collected']/1e7:.2f} Cr)
    - Collection Efficiency: {L['collection_pct']:.1f}% (Prev: {P['collection_pct']:.1f}%)
    - Overdue Cases: {int(L['overdue'])} (Prev: {int(P['overdue'])})
    
    Key Backlog Driver:
    - Region with highest pending: {top_region}
    - Segment with highest pending: {top_segment}
    
    ---
    
    ## 2. Accounts Payable (AP)
    
    - Spend: ₹{ap_latest['spend']/1e7:.2f} Cr (Prev: ₹{ap_prev['spend']/1e7:.2f} Cr)
    - Invoice Volume: {int(ap_latest['invoices'])} invoices
    
    ---
    
    ### Output Requirements
    
    Write the summary in this exact structure:
    
    Slide Title: Executive Summary ({latest})
    
    • Overall Performance (2 bullets)
    • Key Drivers of Change (2 bullets)
    • Risks & Watchouts (2 bullets)
    • Anomalies and Key drivers of Anomalies (2 bullets)
    • Recommended Actions (2 bullets)
    
    Tone: Sharp, executive, PPT-ready.
    Do NOT repeat raw numbers excessively.
    Explain WHY performance changed.
    """
    
    # Generate prompt
    prompt = build_llm_prompt()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0)
    ppt_text = response.choices[0].message.content.strip()

    ppt_text = ppt_text.replace("###", "") 

    return ppt_text