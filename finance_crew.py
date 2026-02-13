import json
from crewai import Agent, Task, Crew,LLM
from dotenv import load_dotenv
from pathlib import Path
import os
# Load .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Get API key with error handling
openai_api_key = os.getenv('OPENAI_API_KEY')

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
llm = LLM(
    model="gpt-4.1",  # fast and cheap
    api_key=openai_api_key
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_latest_month(data_dict):
    months = sorted(data_dict.keys())
    if len(months) < 2:
        return months[-1], None
    return months[-1], months[-2]


def mom_change(data_dict):
    latest, previous = get_latest_month(data_dict)

    if previous is None:
        return latest, 0

    latest_val = data_dict.get(latest, 0)
    prev_val = data_dict.get(previous, 0)

    if prev_val == 0:
        return latest, 0

    change = (latest_val - prev_val) / prev_val * 100
    return latest, round(change, 2)


# ============================================================
# MAIN MULTI-SLIDE INSIGHT ENGINE
# ============================================================

def run_finance_crew(snapshot):

    ap = snapshot["ap_kpis"]
    ar = snapshot["ar_kpis"]

    # ============================================================
    # PREPARE CONTEXTS
    # ============================================================

    latest_month, ap_spend_change = mom_change(ap["monthly_spend_trend"])
    _, processing_change = mom_change(ap["processing_time_trend"])
    _, maverick_change = mom_change(ap["maverick_pct"])
    _, dpo_change = mom_change(ap["dpo_trend"])

    latest_ar_month, revenue_change = mom_change(ar["revenue_trend"])
    _, collection_change = mom_change(ar["collection_trend"])
    _, late_payment_change = mom_change(ar["late_payment_pct"])

    # ============================================================
    # CREATE ANALYST AGENT
    # ============================================================

    analyst = Agent(
        role="Finance Control Tower Analyst",
        goal="Provide concise executive insights with root drivers and recommended actions.",
        backstory="You are a CFO-level finance strategist reviewing a monthly dashboard.",
        verbose=False
    )

    # ============================================================
    # MASTER TASK
    # ============================================================

    task = Task(
        description=f"""
You are preparing a MONTHLY executive dashboard.

Focus strictly on the latest month: {latest_month}.

For EACH slide:
- Provide exactly 2 bullet points.
- Answer:
    What changed?
    Where?
    Why (probable drivers)?
    What should be done next?
- Keep it concise.
- Do not use markdown.
- Return only JSON.

==================================================
AP SLIDE 1 – Spend Performance
MoM Spend Change: {ap_spend_change} %
Business Unit & Region Context:
{json.dumps(ap["bu_region_combo"], indent=2)}

==================================================
AP SLIDE 2 – Operational Efficiency
Processing Time Change: {processing_change} %
Late Payment %: {ap["late_payment_pct"]}
Dispute %: {ap["dispute_pct"]}

==================================================
AP SLIDE 3 – Compliance & Risk
Maverick Change: {maverick_change} %
Vendor Concentration:
{json.dumps(ap["vendor_concentration_pct"], indent=2)}
Vendor Risk Trend:
{json.dumps(ap["vendor_risk_avg"], indent=2)}

==================================================
AP SLIDE 4 – Working Capital
DPO Change: {dpo_change} %
On-Time %:
{json.dumps(ap["on_time_pct"], indent=2)}


==================================================
AR SLIDE 5 – Revenue & Collection
Revenue Change: {revenue_change} %
Collection Change: {collection_change} %
Collection Rate:
{json.dumps(ar["collection_rate_pct"], indent=2)}

==================================================
AR SLIDE 6 – Segment Performance
Segment Mix:
{json.dumps(ar["segment_mix_pct"], indent=2)}
Segment Collection Rate:
{json.dumps(ar["segment_collection_rate_pct"], indent=2)}

==================================================
AR SLIDE 7 – Aging & DSO
DSO: {ar["dso"]}
Aging Distribution:
{json.dumps(ar["aging_distribution_pct"], indent=2)}
Late Payment Change: {late_payment_change} %

==================================================
Return JSON in this exact format:

{{
  "ap": {{
      "slide1": ["bullet1", "bullet2"],
      "slide2": ["bullet1", "bullet2"],
      "slide3": ["bullet1", "bullet2"],
      "slide4": ["bullet1", "bullet2"]
  }},
  "ar": {{
      "slide5": ["bullet1", "bullet2"],
      "slide6": ["bullet1", "bullet2"],
      "slide7": ["bullet1", "bullet2"]
  }},
  "executive_summary": ["bullet1", "bullet2"]
}}

No extra text outside JSON.
""",
        expected_output="Structured JSON insights for all slides.",
        agent=analyst
    )

    crew = Crew(
        agents=[analyst],
        tasks=[task],
        verbose=False
    )

    result = crew.kickoff()

    try:
        parsed = json.loads(result.raw)
        return parsed
    except:
        print("INSIGHT PARSE ERROR")
        print("RAW OUTPUT:", result.raw)
        return {
            "ap": {},
            "ar": {},
            "executive_summary": []
        }
