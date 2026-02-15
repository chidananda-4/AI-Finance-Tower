"""
Agents package initialization
"""
# Don't import directly here to avoid circular imports
# Import will happen in the modules that need them

__all__ = [
    'SummaryAgent',
    'EmailAgent',
    'create_email_config_ui'
]

# These will be imported when needed
def __getattr__(name):
    if name == 'SummaryAgent':
        from agents.summary_agent import SummaryAgent
        return SummaryAgent
    elif name == 'EmailAgent':
        from agents.email_agent import EmailAgent
        return EmailAgent
    elif name == 'create_email_config_ui':
        from agents.email_agent import create_email_config_ui
        return create_email_config_ui
    raise AttributeError(f"module {__name__} has no attribute {name}")