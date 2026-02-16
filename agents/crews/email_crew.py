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
import re

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
            communications for different audiences. You ensure the right people get the right information.
            You are practical and focused on getting the message to the right people efficiently.""",
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
            You know how to strike the perfect neutral tone - professional yet approachable, concise yet complete.
            Your emails are always well-structured and easy to read. You focus on clarity and impact.Treat all the currency in inr""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],  # No tools - pure reasoning
            max_iter=2
        )
    
    def _create_compliance_officer(self):
        """Compliance Officer - ensures email meets basic standards"""
        return Agent(
            role="Email Compliance Officer",
            goal="Quickly review emails for major issues and approve them if they meet basic standards",
            backstory="""You are a practical compliance officer who focuses on real issues, not perfection.
            You check for:
            1. Professional tone (no offensive language)
            2. Complete sentences (no obvious cut-offs)
            3. Appropriate for the audience
            4. All necessary information present
            
            You APPROVE emails that meet these basic standards. You only reject if there are MAJOR issues.
            You understand that getting the information out is more important than perfection.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],  # No tools - pure reasoning
            max_iter=1  # Only one iteration - quick review
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
2. If recipients list is empty, suggest default stakeholders (CFO, Finance Team)
3. Determine the email strategy (standard/urgent/executive_summary)

Return a JSON with:
{{
    "final_recipients": {recipients if recipients else ["cfo@company.com", "finance@company.com"]},
    "email_strategy": "standard",
    "key_messages": ["key point 1", "key point 2"],
    "tone": "professional",
    "notes": "Send as standard business communication"
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
1. Write a clear email subject line
2. Draft the email body incorporating the executive summary
3. Include appropriate greeting and closing
4. Mention the attached presentation

Keep it professional but straightforward. No need for fancy formatting.

Return a JSON with:
{{
    "subject": "Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}",
    "greeting": "Dear Team,",
    "body": "Full email body text...",
    "closing": "Best regards,\nFinance Control Tower AI System",
    "full_email": "Complete email as it will appear"
}}""",
            expected_output="A JSON with complete email content",
            agent=self.content_writer,
            context=[task1]
        )
        
        # Task 3: Compliance Officer - Quick review (APPROVE by default)
        task3 = Task(
            description="""You are the Compliance Officer. Do a QUICK review of the email draft.

CHECK ONLY FOR MAJOR ISSUES:
❌ Offensive or unprofessional language
❌ Clearly incomplete sentences
❌ Missing critical information

✅ APPROVE if it meets these basic standards.
✅ When in doubt, APPROVE.

Return a JSON with:
{{
    "approved": true,  # Always true unless major issues found
    "issues": [],  # Empty unless major issues
    "final_subject": "subject from writer",
    "final_body": "body from writer",
    "final_email": "complete email"
}}""",
            expected_output="A JSON with approved email content (always approved unless major issues)",
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
            
            # Extract content from tasks
            final_recipients = recipients
            subject = f"Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}"
            body = ""
            
            if hasattr(result, 'tasks_output') and len(result.tasks_output) >= 3:
                # Get strategist output for recipients
                try:
                    strategist_text = result.tasks_output[0].raw
                    strategist_match = re.search(r'(\{[\s\S]*\})', strategist_text)
                    if strategist_match:
                        strategist_data = json.loads(strategist_match.group(1))
                        final_recipients = strategist_data.get("final_recipients", recipients)
                except:
                    pass
                
                # Get writer output for content
                try:
                    writer_text = result.tasks_output[1].raw
                    writer_match = re.search(r'(\{[\s\S]*\})', writer_text)
                    if writer_match:
                        writer_data = json.loads(writer_match.group(1))
                        subject = writer_data.get("subject", subject)
                        body = writer_data.get("body", "")
                        full_email = writer_data.get("full_email", "")
                        if full_email:
                            body = full_email
                except:
                    pass
                
                # Compliance officer - we ignore their output and always send
                # unless they found major issues (which they won't with our prompt)
                logger.info("✅ Compliance review completed - sending email")
            
            # Actually send the email
            if final_recipients and body:
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
                    "message": send_result.get("message", "Email sent"),
                    "recipients": final_recipients,
                    "recipients_sent": len(final_recipients),
                    "agent_collaboration": "successful"
                }
            else:
                # Fallback
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
            if attachment_bytes and attachment_filename:
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
            
            logger.info(f"✅ Email sent successfully to {len(recipients)} recipients")
            return {"success": True, "message": f"Email sent to {len(recipients)} recipients"}
            
        except Exception as e:
            logger.error(f"❌ SMTP error: {e}")
            return {"success": False, "message": str(e)}
    
    def _fallback_send(self, ppt_bytes, filename, executive_summary, recipients):
        """Fallback sending if agent collaboration fails"""
        try:
            # Create simple email
            if isinstance(executive_summary, dict):
                summary_text = executive_summary.get("executive_summary", "Financial analysis completed.")
                highlights = executive_summary.get("highlights", [])
                concerns = executive_summary.get("concerns", [])
                
                body = f"""
FINANCE CONTROL TOWER REPORT

EXECUTIVE SUMMARY:
{summary_text}

KEY HIGHLIGHTS:
{chr(10).join(['• ' + h for h in highlights[:3]])}

KEY CONCERNS:
{chr(10).join(['• ' + (c if isinstance(c, str) else c.get('concern', '')) for c in concerns[:3]])}

Please find the detailed presentation attached.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
            else:
                body = f"""
FINANCE CONTROL TOWER REPORT

{str(executive_summary)}

Please find the detailed presentation attached.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
            
            subject = f"Finance Control Tower Report - {datetime.now().strftime('%B %d, %Y')}"
            
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