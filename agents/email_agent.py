"""
Email Agent - Uses CrewAI Email Crew for agent collaboration
"""

import logging
from agents.crews.email_crew import EmailCrew
from io import BytesIO

logger = logging.getLogger(__name__)

class EmailAgent:
    """
    Email Agent that leverages CrewAI Email Crew for agent collaboration
    """
    
    def __init__(self, client, config_path="config/email_config.json"):
        self.client = client
        # Initialize CrewAI LLM
        from crewai import LLM
        self.llm = LLM(
            model="gpt-4o-mini",
            api_key=client.api_key,
            temperature=0.3
        )
        # Initialize Email Crew
        self.crew = EmailCrew(self.llm, config_path)
        logger.info("✅ Email Agent initialized with CrewAI Email Crew")
    
    def send_report(self, ppt_bytes: BytesIO, filename: str, executive_summary: dict, recipients=None):
        """
        Send report using CrewAI email crew
        """
        logger.info("📧 Email Agent: Delegating to Email Crew...")
        return self.crew.send_report(ppt_bytes, filename, executive_summary, recipients)
    
    def test_connection(self):
        """Test email connection"""
        return self.crew._send_via_smtp(
            sender_email=self.crew.config["sender_email"],
            sender_password=self.crew.config["sender_password"],
            recipients=[self.crew.config["sender_email"]],
            subject="Test Connection",
            body="This is a test email.",
            attachment_bytes=b"",
            attachment_filename="",
            smtp_server=self.crew.config["smtp_server"],
            smtp_port=self.crew.config["smtp_port"]
        )