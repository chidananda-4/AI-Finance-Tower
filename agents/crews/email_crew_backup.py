"""
Email Crew - Pure reasoning agents, no tools
Agents collaborate to create and send professional emails
"""

from crewai import Agent, Task, Crew, Process
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class EmailCrew:
    """
    Email Crew - Pure reasoning agents that collaborate to send professional emails
    No tools - agents just reason and the crew handles the actual sending
    """
    
    def __init__(self, llm, config_path="config/email_config.json"):
        self.llm = llm
        self.config = self._load_config(config_path)
        
        # Create pure reasoning agents (no tools)
        self.email_strategist = self._create_email_strategist()
        self.content_writer = self._create_content_writer()
        self.compliance_officer = self._create_compliance_officer()
        
        logger.info("✅ Email Crew initialized with 3 pure reasoning agents (no tools)")
    
    def _load_config(self, config_path):
        """Load email configuration from file"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_emails": []
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"✅ Email configuration loaded from {config_path}")
                    return config
            except Exception as e:
                logger.error(f"Error loading email config: {e}")
                return default_config
        else:
            logger.warning(f"⚠️ Email config file not found at {config_path}")
            return default_config
    
    def _create_email_strategist(self):
        """Email Strategist - determines recipient list and email strategy"""
        return Agent(
            role="Email Communications Strategist",
            goal="Determine the optimal recipient list and email strategy for maximum impact",
            backstory="""You are a senior communications strategist who has advised Fortune 500 CEOs.
            You know exactly who needs to receive which information and how to structure 
            communications for different audiences. You ensure the right people get the right information.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],  # No tools - pure reasoning
            max_iter=2
        )
    
    def _create_content_writer(self):
        """Content Writer - crafts the email content"""
        return Agent(
            role="Executive Email Writer",
            goal="Craft clear, professional, and impactful email content",
            backstory="""You are an expert business writer who has drafted thousands of executive emails.
            You know how to strike the perfect tone - professional yet approachable, concise yet complete.
            Your emails are always well-structured and easy to read.
            Your addressing should be 'Dear Bill' and end with Best Regards Chidananda Tarai""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],  # No tools - pure reasoning
            max_iter=5
        )
    
    def _create_compliance_officer(self):
        """Compliance Officer - ensures email meets standards"""
        return Agent(
            role="Email Compliance Officer",
            goal="Ensure all emails meet professional standards and compliance requirements",
            backstory="""You are a meticulous compliance officer who reviews all outgoing communications.
            You check for proper formatting, appropriate language, and ensure all necessary 
            disclaimers and information are included. But Don't reject the email approval""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],  # No tools - pure reasoning
            max_iter=5
        )
    
    def send_report(self, ppt_bytes, filename, executive_summary, custom_recipients=None):
        """
        Send email using pure reasoning agents
        Agents collaborate, then crew handles the actual sending
        """
        logger.info("🚀 Email Crew: Starting agent collaboration...")
        
        # Prepare context
        recipients = custom_recipients if custom_recipients else self.config.get("recipient_emails", [])
        summary_json = json.dumps(executive_summary, default=str, indent=2)
        
        # Task 1: Email Strategist - Determine recipients and strategy
        task1 = Task(
            description=f"""You are the Email Strategist. Review the executive summary and determine:

CONFIGURED RECIPIENTS: {recipients}

EXECUTIVE SUMMARY:
{summary_json[:2000]}  # Limit length

Your tasks:
1. Validate if the configured recipients are appropriate for this report
2. Suggest any additional stakeholders who should receive this
3. Determine the email strategy (urgency, tone, key messages)

Return a JSON with:
{{
    "final_recipients": {recipients},
    "email_strategy": "standard/urgent/executive_summary",
    "key_messages": ["message1", "message2"],
    "tone": "professional/urgent/formal",
    "notes": "any additional recommendations"
}}""",
            expected_output="A JSON with recipient strategy",
            agent=self.email_strategist
        )
        
        # Task 2: Content Writer - Draft email
        task2 = Task(
            description=f"""You are the Email Writer. Based on the strategist's recommendations, draft the email.

EXECUTIVE SUMMARY:
{summary_json[:2000]}

Your tasks:
1. Write a compelling email subject line tonality should be neutral and corporate
2. Draft the email body incorporating the executive summary
3. Include appropriate greeting - "Dear Bill" and closing, writing "with Best Regards
Chidananda Tarai"
4. Mention the attached presentation

Return a JSON with:
{{
    "subject": "Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}",
    "greeting": "Dear ...",
    "body": "Full email body text...",
    "closing": "Best regards,...",
    "full_email": "Complete email as it will appear"
}}""",
            expected_output="A JSON with complete email content",
            agent=self.content_writer,
            context=[task1]
        )
        
        # Task 3: Compliance Officer - Review and approve
        task3 = Task(
            description="""You are the Compliance Officer. Review the email draft for any issues.

Check for:
1. Professional tone and language
2. Proper formatting
3. All necessary information included
4. No sensitive data exposed
5. Appropriate for external recipients

If approved, return the final email content.
If issues found, provide corrections.
Approve the email max within 2 iterations

Return a JSON with:
{{
    "approved": true/false,
    "issues": ["issue1", "issue2"] if not approved,
    "final_subject": "approved subject",
    "final_body": "approved body",
    "final_email": "complete approved email"
}}""",
            expected_output="A JSON with approved email content",
            agent=self.compliance_officer,
            context=[task2]
        )
        
        # Create crew with all agents
        crew = Crew(
            agents=[
                self.email_strategist,
                self.content_writer,
                self.compliance_officer
            ],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            # Run agent collaboration
            result = crew.kickoff()
            
            # Extract the approved email content
            final_email = None
            if hasattr(result, 'tasks_output') and len(result.tasks_output) >= 3:
                # Get compliance officer's output
                compliance_output = result.tasks_output[2].raw
                
                # Parse JSON
                try:
                    import re
                    json_match = re.search(r'(\{[\s\S]*\})', compliance_output)
                    if json_match:
                        approved = json.loads(json_match.group(1))
                        
                        if approved.get("approved", True):
                            # Send the email using SMTP (crew handles the actual sending)
                            subject = approved.get("final_subject", f"Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}")
                            body = approved.get("final_body", "")
                            
                            # Use recipients from strategist or config
                            strategist_output = result.tasks_output[0].raw
                            strategist_match = re.search(r'(\{[\s\S]*\})', strategist_output)
                            if strategist_match:
                                strategist_data = json.loads(strategist_match.group(1))
                                final_recipients = strategist_data.get("final_recipients", recipients)
                            else:
                                final_recipients = recipients
                            
                            # Actually send the email
                            send_result = self._send_via_smtp(
                                sender_email=self.config["sender_email"],
                                sender_password=self.config["sender_password"],
                                recipients=final_recipients,
                                subject=subject,
                                body=body,
                                attachment_bytes=ppt_bytes.getvalue(),
                                attachment_filename=filename,
                                smtp_server=self.config["smtp_server"],
                                smtp_port=self.config["smtp_port"]
                            )
                            
                            return {
                                "success": send_result.get("success", False),
                                "message": send_result.get("message", "Email processed"),
                                "recipients": final_recipients,
                                "recipients_sent": len(final_recipients),
                                "agent_collaboration": "successful"
                            }
                        else:
                            return {
                                "success": False,
                                "message": f"Email not approved: {approved.get('issues', ['Unknown issues'])}",
                                "agent_collaboration": "completed"
                            }
                except Exception as e:
                    logger.error(f"Error parsing agent output: {e}")
            
            # Fallback - send without agent approval
            logger.warning("Agent collaboration incomplete, using fallback")
            return self._fallback_send(ppt_bytes, filename, executive_summary, recipients)
            
        except Exception as e:
            logger.error(f"❌ Email Crew error: {e}")
            return self._fallback_send(ppt_bytes, filename, executive_summary, recipients)
    
    def _send_via_smtp(self, sender_email, sender_password, recipients, subject, body, 
                       attachment_bytes, attachment_filename, smtp_server, smtp_port):
        """Actual SMTP sending (not a tool, just a helper method)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PPT
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.presentationml.presentation')
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
            msg.attach(part)
            
            # Send
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Email sent to {len(recipients)} recipients"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _fallback_send(self, ppt_bytes, filename, executive_summary, recipients):
        """Fallback sending if agent collaboration fails"""
        try:
            # Create simple email
            if isinstance(executive_summary, dict):
                summary_text = executive_summary.get("executive_summary", "Financial analysis completed.")
            else:
                summary_text = str(executive_summary)
            
            subject = f"Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}"
            body = f"""
FINANCE CONTROL TOWER REPORT

{summary_text}

Please find the detailed presentation attached.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            return self._send_via_smtp(
                sender_email=self.config["sender_email"],
                sender_password=self.config["sender_password"],
                recipients=recipients,
                subject=subject,
                body=body,
                attachment_bytes=ppt_bytes.getvalue(),
                attachment_filename=filename,
                smtp_server=self.config["smtp_server"],
                smtp_port=self.config["smtp_port"]
            )
        except Exception as e:
            return {"success": False, "message": str(e)}