from crewai import Agent, LLM
from tools import KPITool, PPTTool, EmailTool
import os

from dotenv import load_dotenv
from pathlib import Path

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

data_analyst = Agent(
    role="Senior Data Analyst",
    goal="Analyze KPI data and detect trends and anomalies",
    backstory="Expert in financial and operational KPI analytics.",
    tools=[KPITool()],
    llm=llm,
    verbose=True
)

executive_writer = Agent(
    role="Chief Strategy Officer",
    goal="Generate executive-level narrative from KPI insights",
    backstory="Expert in translating data into strategic storytelling.",
    llm=llm,
    verbose=True
)

report_generator = Agent(
    role="Reporting Specialist",
    goal="Generate PPT deck and distribute report",
    backstory="Expert in creating board-ready executive presentations.",
    tools=[PPTTool(), EmailTool()],
    llm=llm,
    verbose=True
)
