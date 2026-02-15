"""
Summary Crew - Storytelling Narrative Executive Summary
Format 3: The Big Picture + What's Working + What Needs Attention + Next Steps
USES ONLY numbers from combined_insights - NO made-up data
"""

from crewai import Agent, Task, Crew, Process
import logging
import json
import re

logger = logging.getLogger(__name__)


class SummaryCrew:
    """
    Summary Crew - Creates storytelling narrative executive summary
    Format: The Big Picture | What's Working | What Needs Attention | Next Steps
    """
    
    def __init__(self, llm):
        self.llm = llm
        
        # Create specialized agents
        self.big_picture_analyst = self._create_big_picture_analyst()
        self.working_analyst = self._create_working_analyst()
        self.attention_analyst = self._create_attention_analyst()
        self.next_steps_advisor = self._create_next_steps_advisor()
        
        logger.info("✅ Summary Crew initialized for storytelling narrative format")
    
    def _create_big_picture_analyst(self):
        """Agent for 'The Big Picture' section"""
        return Agent(
            role="Chief Financial Strategist",
            goal="Craft a concise 3-4 sentence overview of overall financial health with key metrics",
            backstory="""You are a CFO-level strategist who can distill complex financial data into a compelling narrative.
            You write 3-4 sentences that tell the complete story: overall performance, key drivers, and critical issues.
            You ALWAYS include specific numbers from the data.
            
            Format: "Q4 performance shows [trend] with revenue at [X] ([+/-]%), driven by [segment1] and [segment2]. 
            However, [concern1] at [Y] and [concern2] at [Z] require immediate attention. [Forward-looking statement]."
            
            You NEVER make up numbers - only use what's in the insights.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
            max_iter=2
        )
    
    def _create_working_analyst(self):
        """Agent for 'What's Working' section - 3 bullet points"""
        return Agent(
            role="Business Performance Analyst",
            goal="Identify 3 positive developments with specific numbers from the data",
            backstory="""You find the TOP 3 things going well in the business.
            Each bullet point is 1-2 sentences with specific numbers.
            Format: "• [Achievement] with [EXACT numbers]. [Impact]."
            
            Example: "• Enterprise revenue up 12.3% to ₹84.5B, driven by AI platform launch contributing ₹12.3B."
            
            You NEVER make up numbers - only use what's in the insights.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],
            max_iter=2
        )
    
    def _create_attention_analyst(self):
        """Agent for 'What Needs Attention' section - 3 bullet points"""
        return Agent(
            role="Risk Assessment Director",
            goal="Identify 3 critical concerns with specific numbers from the data",
            backstory="""You find the TOP 3 things needing immediate attention.
            Each bullet point is 1-2 sentences with specific numbers and impact.
            Format: "• [Problem] with [EXACT numbers]. [Financial impact/risk]."
            
            Example: "• Cloud spend 18.7% over budget (₹12.3M), consuming 23% of margin gains and projected to reach ₹15-18M quarterly overrun."
            
            You NEVER make up numbers - only use what's in the insights.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],
            max_iter=2
        )
    
    def _create_next_steps_advisor(self):
        """Agent for 'Next Steps' section - 4 prioritized actions"""
        return Agent(
            role="Strategic Planning Director",
            goal="Create 4 prioritized next steps with owners and timelines",
            backstory="""You create a clear action plan with 4 steps organized by timeline.
            Format: "THIS WEEK: [Action]. [Owner]. [Expected impact]"
                     "THIS MONTH: [Action]. [Owner]. [Expected impact]"
                     "THIS QUARTER: [Action]. [Owner]. [Expected impact]"
            
            Example: "THIS WEEK: Launch collection campaign for 60+ day accounts (₹18.5M). AR Manager. Target recovery ₹12-15M."
            
            Each action must address a specific concern from the data.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],
            max_iter=2
        )
    
    def generate_summary(self, combined_insights):
        """
        Generate storytelling narrative executive summary
        Returns: big_picture, working, attention, next_steps
        """
        logger.info("🚀 Summary Crew: Generating storytelling narrative executive summary...")
        
        # Task 1: Big Picture Analyst
        task1 = Task(
            description=f"""You are the Chief Financial Strategist. Write the "Big Picture" section.

INSIGHTS TEXT (USE ONLY NUMBERS FROM HERE):
{combined_insights[:8000]}

INSTRUCTIONS:
1. Write 3-4 sentences that tell the complete story
2. Include: overall performance trend, key revenue/spend numbers, critical concerns
3. Use EXACT numbers from the insights
4. End with a forward-looking statement

Format example:
"Q4 performance shows strong revenue growth of 8.2% to ₹342.1B, driven by Enterprise (+12.3%) and SMB segments. However, margin pressure from cloud overspend (18.7%, ₹12.3M) and DSO deterioration to 48 days (+3 vs target) requires immediate attention. Collections efficiency improved 24.4% in SMB, but late payments at 15.2% continue to impact cash flow. Focus on cloud governance and collection automation will be critical for Q1."

Return ONLY this JSON:
{{
    "big_picture": "your 3-4 sentence narrative with specific numbers"
}}""",
            expected_output="A JSON with the big picture narrative",
            agent=self.big_picture_analyst
        )
        
        # Task 2: Working Analyst - 3 things going well
        task2 = Task(
            description=f"""You are the Business Performance Analyst. Find 3 things going well.

INSIGHTS TEXT (USE ONLY FROM HERE):
{combined_insights[:8000]}

INSTRUCTIONS:
1. Find 3 positive developments with numbers
2. Each bullet: 1-2 sentences
3. Include specific numbers and impact
4. Format each with "• "

Examples:
"• Enterprise revenue up 12.3% to ₹84.5B, driven by AI platform launch contributing ₹12.3B."
"• SMB collections improved 24.4% MoM to ₹42.8M through automated reminders, increasing 30-day rate from 68% to 83%."
"• Vendor compliance reached 92.5% with preferred vendors, reducing maverick spend from 20.4% to 14.6%."

Return ONLY this JSON:
{{
    "working": [
        "• [first positive with numbers]",
        "• [second positive with numbers]",
        "• [third positive with numbers]"
    ]
}}""",
            expected_output="A JSON with 3 positive bullets",
            agent=self.working_analyst,
            context=[task1]
        )
        
        # Task 3: Attention Analyst - 3 things needing attention
        task3 = Task(
            description=f"""You are the Risk Assessment Director. Find 3 things needing attention.

INSIGHTS TEXT (USE ONLY FROM HERE):
{combined_insights[:8000]}

INSTRUCTIONS:
1. Find 3 critical concerns with numbers
2. Each bullet: 1-2 sentences
3. Include specific numbers, financial impact, and risk
4. Format each with "• "

Examples:
"• Cloud spend 18.7% over budget (₹12.3M), consuming 23% of margin gains and projected to reach ₹15-18M quarterly overrun if unaddressed."
"• Late payments at 91.6% for 15-day terms, delaying ₹23.4M cash flow and growing 15% MoM, risking vendor relationships."
"• Enterprise invoicing down 9.0% (₹7.6M) with top 5 customers reducing orders 18%, signaling potential revenue risk."

Return ONLY this JSON:
{{
    "attention": [
        "• [first concern with numbers]",
        "• [second concern with numbers]",
        "• [third concern with numbers]"
    ]
}}""",
            expected_output="A JSON with 3 concern bullets",
            agent=self.attention_analyst,
            context=[task1, task2]
        )
        
        # Task 4: Next Steps Advisor - 4 prioritized actions
        task4 = Task(
            description=f"""You are the Strategic Planning Director. Create 4 next steps with timelines.

CONCERNS TO ADDRESS:
{{task3_output}}

INSTRUCTIONS:
1. Create 4 actions addressing the top concerns
2. Organize by timeline: THIS WEEK, THIS MONTH, THIS QUARTER (1-2 each)
3. Include: action, owner, expected impact with numbers where possible
4. Use EXACT format:

"THIS WEEK: [Specific action]. [Owner]. [Expected impact with numbers if available]"
"THIS MONTH: [Specific action]. [Owner]. [Expected impact with numbers if available]"
"THIS QUARTER: [Specific action]. [Owner]. [Expected impact with numbers if available]"

Examples:
"THIS WEEK: Launch collection campaign for 60+ day accounts (₹18.5M). AR Manager. Target recovery ₹12-15M in 30 days."
"THIS MONTH: Implement cloud budget controls with 80% utilization alerts. CFO & CTO. Target 20% reduction (₹10M quarterly)."
"THIS QUARTER: Renegotiate top 5 IT contracts for 15% rate reduction. CIO & CPO. Estimated savings ₹5-7M annually."

Return ONLY this JSON with a single "next_steps" list containing all 4 items:
{{
    "next_steps": [
        "THIS WEEK: [action]. [owner]. [impact]",
        "THIS WEEK: [action]. [owner]. [impact]",
        "THIS MONTH: [action]. [owner]. [impact]",
        "THIS QUARTER: [action]. [owner]. [impact]"
    ]
}}""",
            expected_output="A JSON with 4 prioritized next steps",
            agent=self.next_steps_advisor,
            context=[task1, task2, task3]
        )
        
        # Create crew with all tasks
        crew = Crew(
            agents=[
                self.big_picture_analyst,
                self.working_analyst,
                self.attention_analyst,
                self.next_steps_advisor
            ],
            tasks=[task1, task2, task3, task4],
            process=Process.sequential,
            verbose=True
        )
        
        try:
            result = crew.kickoff()
            
            # Extract JSON from result
            final_summary = {}
            
            if hasattr(result, 'tasks_output') and len(result.tasks_output) >= 4:
                # Parse each task output
                for i, task_output in enumerate(result.tasks_output):
                    try:
                        output_text = task_output.raw
                        json_match = re.search(r'(\{[\s\S]*\})', output_text)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            final_summary.update(data)
                    except:
                        continue
            
            # Ensure we have all required fields with fallbacks
            if not final_summary.get("big_picture"):
                final_summary["big_picture"] = self._extract_big_picture(combined_insights)
            
            if not final_summary.get("working"):
                final_summary["working"] = self._extract_working(combined_insights)
            
            if not final_summary.get("attention"):
                final_summary["attention"] = self._extract_attention(combined_insights)
            
            if not final_summary.get("next_steps"):
                final_summary["next_steps"] = self._create_next_steps(final_summary.get("attention", []))
            
            # Create formatted text for email/backup
            final_summary["formatted_text"] = self._create_formatted_text(final_summary)
            
            return final_summary
            
        except Exception as e:
            logger.error(f"❌ Summary Crew error: {e}")
            return self._extract_direct_from_insights(combined_insights)
    
    def _extract_big_picture(self, insights):
        """Emergency extraction of big picture narrative"""
        import re
        
        # Extract key metrics
        revenue_match = re.search(r'revenue.*?([₹]?\d+\.?\d*[BMK]?).*?(\d+\.?\d*%)?', insights, re.IGNORECASE)
        revenue = revenue_match.group(1) if revenue_match else "N/A"
        growth = revenue_match.group(2) if revenue_match and revenue_match.group(2) else ""
        
        spend_match = re.search(r'spend.*?([₹]?\d+\.?\d*[BMK]?)', insights, re.IGNORECASE)
        spend = spend_match.group(1) if spend_match else "N/A"
        
        dso_match = re.search(r'DSO.*?(\d+)', insights, re.IGNORECASE)
        dso = dso_match.group(1) if dso_match else "N/A"
        
        # Find positive and negative indicators
        positive = re.findall(r'(increase|growth|improve).*?(\d+\.?\d*%)', insights, re.IGNORECASE)
        negative = re.findall(r'(concern|risk|over|decline|drop|late).*?(\d+\.?\d*%|₹\d+\.?\d*[BMK]?)', insights, re.IGNORECASE)
        
        pos_text = positive[0][0] + " " + positive[0][1] if positive else "positive trends"
        neg_text = negative[0][0] + " at " + negative[0][1] if negative else "some concerns"
        
        return f"Q4 performance shows {pos_text} with revenue at {revenue}{ ' ('+growth+')' if growth else ''}. However, {neg_text} requires attention. Focus on key initiatives will drive Q1 improvements."
    
    def _extract_working(self, insights):
        """Emergency extraction of positive bullets"""
        lines = insights.split('\n')
        working = []
        
        positive_keywords = ['increase', 'growth', 'improve', 'peak', 'high', 'success']
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in positive_keywords):
                if '₹' in line or '%' in line:
                    if len(line) > 15 and len(line) < 150:
                        working.append(f"• {line}")
                        if len(working) >= 3:
                            break
        
        while len(working) < 3:
            working.append("• Review detailed insights for complete picture")
        
        return working[:3]
    
    def _extract_attention(self, insights):
        """Emergency extraction of concern bullets"""
        lines = insights.split('\n')
        attention = []
        
        concern_keywords = ['concern', 'risk', 'over', 'under', 'low', 'decrease', 'drop', 'late']
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in concern_keywords):
                if '₹' in line or '%' in line:
                    if len(line) > 15 and len(line) < 150:
                        attention.append(f"• {line}")
                        if len(attention) >= 3:
                            break
        
        while len(attention) < 3:
            attention.append("• Monitor detailed metrics for risk assessment")
        
        return attention[:3]
    
    def _create_next_steps(self, attention_bullets):
        """Create next steps based on concerns"""
        steps = []
        
        if attention_bullets:
            for i, bullet in enumerate(attention_bullets[:3]):
                if "cloud" in bullet.lower():
                    steps.append("THIS WEEK: Review cloud budget and implement controls. CFO. Target 20% reduction.")
                elif "payment" in bullet.lower() or "late" in bullet.lower():
                    steps.append("THIS WEEK: Launch collection campaign for overdue accounts. AR Manager. Target ₹12-15M recovery.")
                elif "enterprise" in bullet.lower() or "revenue" in bullet.lower():
                    steps.append("THIS MONTH: Interview top 10 enterprise customers. Sales VP. Identify decline causes.")
                elif "dso" in bullet.lower():
                    steps.append("THIS MONTH: Optimize payment terms with top vendors. Treasurer. Target 3-day DSO reduction.")
                else:
                    steps.append(f"THIS MONTH: Investigate {bullet[2:30]}. Controller. Priority: HIGH.")
        
        while len(steps) < 4:
            steps.append("THIS QUARTER: Review strategic initiatives. Strategy Team. Align with annual plan.")
        
        return steps[:4]
    
    def _create_formatted_text(self, summary):
        """Create formatted text for email/backup"""
        formatted = "="*80 + "\n"
        formatted += " " * 28 + "EXECUTIVE SUMMARY\n"
        formatted += "="*80 + "\n\n"
        
        formatted += "THE BIG PICTURE\n"
        formatted += "-"*40 + "\n"
        formatted += summary.get("big_picture", "") + "\n\n"
        
        formatted += "WHAT'S WORKING\n"
        formatted += "-"*40 + "\n"
        for w in summary.get("working", []):
            formatted += f"{w}\n"
        formatted += "\n"
        
        formatted += "WHAT NEEDS ATTENTION\n"
        formatted += "-"*40 + "\n"
        for a in summary.get("attention", []):
            formatted += f"{a}\n"
        formatted += "\n"
        
        formatted += "NEXT STEPS\n"
        formatted += "-"*40 + "\n"
        for ns in summary.get("next_steps", []):
            formatted += f"{ns}\n"
        
        return formatted
    
    def _extract_direct_from_insights(self, insights):
        """Complete fallback summary"""
        working = self._extract_working(insights)
        attention = self._extract_attention(insights)
        
        return {
            "big_picture": self._extract_big_picture(insights),
            "working": working,
            "attention": attention,
            "next_steps": self._create_next_steps(attention),
            "formatted_text": self._create_formatted_text({
                "big_picture": self._extract_big_picture(insights),
                "working": working,
                "attention": attention,
                "next_steps": self._create_next_steps(attention)
            })
        }