"""
Email Tools for CrewAI Agents
Provides tools for email operations
"""

import smtplib
import os
import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from crewai.tools import BaseTool
from typing import Optional, Type, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class EmailConfigInput(BaseModel):
    """Input schema for EmailConfigTool"""
    config_path: str = Field(
        default="config/email_config.json", 
        description="Path to email config file"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class EmailConfigTool(BaseTool):
    """Tool for loading and validating email configuration"""
    
    name: str = "email_config_tool"
    description: str = "Loads and validates email configuration from file or environment"
    args_schema: Type[BaseModel] = EmailConfigInput
    
    def _run(self, config_path: str = "config/email_config.json") -> dict:
        """Load email configuration"""
        config = {}
        
        # Try to load from file
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                return {"error": str(e)}
        
        # Override with environment variables
        config["smtp_server"] = os.getenv("SMTP_SERVER", config.get("smtp_server", "smtp.gmail.com"))
        config["smtp_port"] = int(os.getenv("SMTP_PORT", config.get("smtp_port", 587)))
        config["sender_email"] = os.getenv("SENDER_EMAIL", config.get("sender_email", ""))
        config["sender_password"] = os.getenv("SENDER_PASSWORD", config.get("sender_password", ""))
        config["recipient_emails"] = os.getenv("RECIPIENT_EMAILS", config.get("recipient_emails", "")).split(",")
        
        return config


class EmailSenderInput(BaseModel):
    """Input schema for EmailSenderTool"""
    sender_email: str = Field(description="Sender email address")
    sender_password: str = Field(description="Sender email password")
    recipients: List[str] = Field(description="List of recipient email addresses")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    attachment_bytes: Optional[bytes] = Field(None, description="PPT file bytes")
    attachment_filename: Optional[str] = Field(None, description="PPT filename")
    smtp_server: str = Field("smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(587, description="SMTP port")
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class EmailSenderTool(BaseTool):
    """Tool for sending emails with attachments"""
    
    name: str = "email_sender_tool"
    description: str = "Sends emails with PPT attachments and formatted content"
    args_schema: Type[BaseModel] = EmailSenderInput
    
    def _run(self, 
             sender_email: str,
             sender_password: str,
             recipients: List[str],
             subject: str,
             body: str,
             attachment_bytes: Optional[bytes] = None,
             attachment_filename: Optional[str] = None,
             smtp_server: str = "smtp.gmail.com",
             smtp_port: int = 587) -> dict:
        """Send email with attachment"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachment if provided
            if attachment_bytes and attachment_filename:
                part = MIMEBase('application', 'vnd.openxmlformats-officedocument.presentationml.presentation')
                part.set_payload(attachment_bytes)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{attachment_filename}"'
                )
                msg.attach(part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return {
                "success": True,
                "message": f"Email sent successfully to {len(recipients)} recipients"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class EmailFormatterInput(BaseModel):
    """Input schema for EmailFormatterTool"""
    executive_summary: Dict[str, Any] = Field(
        description="Executive summary dictionary"
    )
    recipient_name: str = Field(
        default="CXO", 
        description="Name of the recipient"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class EmailFormatterTool(BaseTool):
    """Tool for formatting email content"""
    
    name: str = "email_formatter_tool"
    description: str = "Formats executive summary into professional email body"
    args_schema: Type[BaseModel] = EmailFormatterInput
    
    def _run(self, executive_summary: dict, recipient_name: str = "CXO") -> str:
        """Format executive summary for email"""
        
        body = f"""
Dear {recipient_name},

FINANCE CONTROL TOWER - EXECUTIVE REPORT
{'='*50}

{executive_summary.get('executive_summary', '')}

{'='*50}
KEY HIGHLIGHTS:
"""
        for h in executive_summary.get('highlights', []):
            body += f"✓ {h}\n"
        
        body += "\nCRITICAL CONCERNS:\n"
        for c in executive_summary.get('concerns', []):
            body += f"⚠ {c}\n"
        
        body += "\nRECOMMENDED ACTIONS:\n"
        for a in executive_summary.get('recommended_actions', []):
            action = a.get('action', '')
            owner = a.get('owner', 'TBD')
            priority = a.get('priority', 'Medium')
            body += f"• {action} [Owner: {owner}, Priority: {priority}]\n"
        
        body += f"""
{'='*50}
Please find the detailed presentation attached.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Finance Control Tower AI System
"""
        return body


class EmailValidatorInput(BaseModel):
    """Input schema for EmailValidatorTool"""
    emails: List[str] = Field(
        description="List of email addresses to validate"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class EmailValidatorTool(BaseTool):
    """Tool for validating email addresses"""
    
    name: str = "email_validator_tool"
    description: str = "Validates email address format"
    args_schema: Type[BaseModel] = EmailValidatorInput
    
    def _run(self, emails: List[str]) -> dict:
        """Validate list of email addresses"""
        
        valid = []
        invalid = []
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if re.match(pattern, email.strip()):
                valid.append(email.strip())
            else:
                invalid.append(email.strip())
        
        return {
            "valid": valid,
            "invalid": invalid,
            "all_valid": len(invalid) == 0
        }