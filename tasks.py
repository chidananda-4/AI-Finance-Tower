from crewai import Task
from agents import data_analyst, executive_writer, report_generator


def create_tasks(file_path):

    analyze_task = Task(
        description=f"""
        Use the KPI tool to analyze KPI data from {file_path}.
        Compute Week on Week growth, MoM growth, top driver region, worst region and detect anomaly.
        """,
        expected_output="Structured KPI insights dictionary.",
        agent=data_analyst
    )

    narrative_task = Task(
        description="""
        Based on the KPI insights generated in the previous step,
        generate an executive summary explaining:
        - What changed
        - Where
        - Why
        - Recommended next steps
        Try to quote numbers wherever possible in your narrative
        """,
        expected_output="Executive narrative text.",
        agent=executive_writer
    )

    report_task = Task(
        description=f"""
        Generate a PPT report using the dataset {file_path},
        the KPI insights and the executive narrative.
        Then send the report via email.
        """,
        expected_output="PPT created and email sent confirmation.",
        agent=report_generator
    )

    return analyze_task, narrative_task, report_task
