from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
from kpi_engine import compute_kpis
from ppt_generator import generate_ppt
from email_service import send_email_simulated


# -----------------------------
# KPI TOOL
# -----------------------------

class KPIInput(BaseModel):
    file_path: str = Field(..., description="Path to KPI CSV file")

    class Config:
        extra = "forbid"


class KPITool(BaseTool):
    name: str = "kpi_tool"
    description: str = "Compute KPI insights from dataset."
    args_schema: Type[BaseModel] = KPIInput

    def _run(self, file_path: str):
        insights = compute_kpis(file_path)
        return json.dumps(insights)  # return string


# -----------------------------
# PPT TOOL
# -----------------------------

class PPTInput(BaseModel):
    file_path: str
    insights_json: str
    narrative: str

    class Config:
        extra = "forbid"


class PPTTool(BaseTool):
    name: str = "ppt_tool"
    description: str = "Generate executive PPT report."
    args_schema: Type[BaseModel] = PPTInput

    def _run(self, file_path: str, insights_json: str, narrative: str):
        import json
        insights = json.loads(insights_json)

        # Always use correct dataset path
        correct_path = "data/synthetic_kpi_data.csv"

        return generate_ppt(correct_path, insights, narrative)


# -----------------------------
# EMAIL TOOL
# -----------------------------

class EmailInput(BaseModel):
    ppt_path: str

    class Config:
        extra = "forbid"


class EmailTool(BaseTool):
    name: str = "email_tool"
    description: str = "Send executive report via email."
    args_schema: Type[BaseModel] = EmailInput

    def _run(self, ppt_path: str):
        send_email_simulated(ppt_path)
        return "Email sent successfully"
