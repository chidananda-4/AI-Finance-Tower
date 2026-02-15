"""
Summary Agent - Simplified version using string input
"""

import logging
from agents.crews.summary_crew import SummaryCrew

logger = logging.getLogger(__name__)

class SummaryAgent:
    """
    Summary Agent that leverages the Summary Crew for multi-agent collaboration
    Takes a simple string input of all insights
    """
    
    def __init__(self, client):
        self.client = client
        # Initialize the Crew with LLM
        from crewai import LLM
        self.llm = LLM(
            model="gpt-4o-mini",
            api_key=client.api_key,
            temperature=0.3
        )
        self.crew = SummaryCrew(self.llm)
        logger.info("✅ Summary Agent initialized")
    
    def generate_executive_summary(self, combined_insights):
        """
        Generate executive summary using the multi-agent crew
        Args:
            combined_insights: String containing all insights from all slides
        """
        logger.info("📋 Summary Agent: Delegating to Summary Crew with string input...")
        logger.info(f"Input insights length: {len(combined_insights)} characters")
        
        try:
            summary = self.crew.generate_summary(combined_insights)
            logger.info("✅ Summary Agent received response from crew")
            
            # Verify the summary has required fields
            if not summary.get("executive_summary"):
                logger.warning("⚠️ Summary missing executive_summary field")
            
            return summary
        except Exception as e:
            logger.error(f"❌ Summary Agent error: {e}")
            # Return fallback summary
            return self.crew._get_fallback_summary()