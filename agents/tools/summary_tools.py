"""
Summary Tools for CrewAI Agents
Provides tools for executive summary generation
"""

import json
import re
from crewai.tools import BaseTool
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class InsightAggregatorInput(BaseModel):
    """Input schema for InsightAggregatorTool"""
    all_slides_insights: Dict[str, Any] = Field(
        description="Dictionary of insights from all slides"
    )
    slide_titles: Dict[int, str] = Field(
        description="Dictionary mapping slide numbers to titles"
    )
    
    model_config = ConfigDict(
        extra="forbid",  # This adds additionalProperties: false to the schema
        arbitrary_types_allowed=True
    )


class InsightAggregatorTool(BaseTool):
    """Tool for aggregating insights from all slides"""
    
    name: str = "insight_aggregator_tool"
    description: str = "Aggregates and categorizes insights from all slides"
    args_schema: Type[BaseModel] = InsightAggregatorInput
    
    def _run(self, all_slides_insights: Dict[str, Any], slide_titles: Dict[int, str]) -> dict:
        """Aggregate insights by category"""
        
        aggregated = {
            "financial_performance": [],
            "operational_efficiency": [],
            "risk_compliance": [],
            "working_capital": [],
            "revenue_collections": [],
            "all_insights": []
        }
        
        # Categorize insights based on slide titles
        for slide_num, title in slide_titles.items():
            insight = all_slides_insights.get(title, "")
            
            if not insight:
                continue
            
            aggregated["all_insights"].append({"slide": title, "insight": insight})
            
            # Categorize based on title keywords
            title_lower = title.lower()
            if any(word in title_lower for word in ["spend", "expense", "cost"]):
                aggregated["financial_performance"].append({"slide": title, "insight": insight})
            elif any(word in title_lower for word in ["payment", "processing", "behaviour"]):
                aggregated["operational_efficiency"].append({"slide": title, "insight": insight})
            elif any(word in title_lower for word in ["risk", "compliance", "late"]):
                aggregated["risk_compliance"].append({"slide": title, "insight": insight})
            elif any(word in title_lower for word in ["working capital", "budget"]):
                aggregated["working_capital"].append({"slide": title, "insight": insight})
            elif any(word in title_lower for word in ["invoice", "collection", "revenue"]):
                aggregated["revenue_collections"].append({"slide": title, "insight": insight})
        
        return aggregated


class PriorityAnalyzerInput(BaseModel):
    """Input schema for PriorityAnalyzerTool"""
    concerns: List[str] = Field(
        description="List of concerns to analyze"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class PriorityAnalyzerTool(BaseTool):
    """Tool for analyzing and prioritizing concerns"""
    
    name: str = "priority_analyzer_tool"
    description: str = "Analyzes concerns and assigns priority levels"
    args_schema: Type[BaseModel] = PriorityAnalyzerInput
    
    def _run(self, concerns: List[str]) -> list:
        """Analyze concerns and assign priority"""
        
        prioritized = []
        
        # Keywords that indicate high priority
        high_priority_keywords = ["critical", "severe", "significant", "urgent", "risk", "compliance", "fraud"]
        medium_priority_keywords = ["moderate", "attention", "monitor", "trend"]
        
        for concern in concerns:
            concern_lower = concern.lower()
            
            if any(word in concern_lower for word in high_priority_keywords):
                priority = "HIGH"
            elif any(word in concern_lower for word in medium_priority_keywords):
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            prioritized.append({
                "concern": concern,
                "priority": priority,
                "requires_immediate_action": priority == "HIGH"
            })
        
        return prioritized


class ActionRecommenderInput(BaseModel):
    """Input schema for ActionRecommenderTool"""
    insights: Dict[str, Any] = Field(
        description="Categorized insights"
    )
    concerns: List[str] = Field(
        description="List of concerns"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class ActionRecommenderTool(BaseTool):
    """Tool for generating recommended actions"""
    
    name: str = "action_recommender_tool"
    description: str = "Generates recommended actions based on insights and concerns"
    args_schema: Type[BaseModel] = ActionRecommenderInput
    
    def _run(self, insights: Dict[str, Any], concerns: List[str]) -> list:
        """Generate recommended actions"""
        
        actions = []
        
        # Financial performance actions
        if insights.get("financial_performance"):
            actions.append({
                "action": "Review budget vs actual variance for top cost centers",
                "owner": "Finance Controller",
                "priority": "HIGH",
                "timeline": "Next week"
            })
        
        # Operational efficiency actions
        if insights.get("operational_efficiency"):
            actions.append({
                "action": "Analyze payment processing times and identify bottlenecks",
                "owner": "AP Manager",
                "priority": "MEDIUM",
                "timeline": "Next 2 weeks"
            })
        
        # Risk and compliance actions
        if insights.get("risk_compliance") or any("risk" in c.lower() for c in concerns):
            actions.append({
                "action": "Conduct risk assessment for high-risk vendors",
                "owner": "Risk Manager",
                "priority": "HIGH",
                "timeline": "Immediate"
            })
        
        # Working capital actions
        if insights.get("working_capital"):
            actions.append({
                "action": "Optimize payment terms to improve working capital",
                "owner": "Treasury",
                "priority": "MEDIUM",
                "timeline": "This month"
            })
        
        # Revenue and collections actions
        if insights.get("revenue_collections"):
            actions.append({
                "action": "Focus collection efforts on overdue accounts",
                "owner": "AR Manager",
                "priority": "HIGH",
                "timeline": "This week"
            })
        
        return actions[:5]  # Return top 5 actions


class MetricExtractorInput(BaseModel):
    """Input schema for MetricExtractorTool"""
    insights_text: str = Field(
        description="Text containing insights to extract metrics from"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True
    )


class MetricExtractorTool(BaseTool):
    """Tool for extracting key metrics from insights"""
    
    name: str = "metric_extractor_tool"
    description: str = "Extracts key numerical metrics from insights"
    args_schema: Type[BaseModel] = MetricExtractorInput
    
    def _run(self, insights_text: str) -> dict:
        """Extract metrics like percentages, amounts, trends"""
        
        metrics = {
            "percentages": [],
            "amounts": [],
            "trends": []
        }
        
        # Extract percentages
        pct_pattern = r'(\d+(?:\.\d+)?)%'
        metrics["percentages"] = re.findall(pct_pattern, insights_text)
        
        # Extract amounts (INR)
        amount_pattern = r'(?:₹|INR|Rs\.?)\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        amounts = re.findall(amount_pattern, insights_text)
        metrics["amounts"] = [a.replace(',', '') for a in amounts]
        
        # Extract trend words
        trend_words = ["increase", "decrease", "up", "down", "growth", "decline", "stable"]
        words = insights_text.lower().split()
        metrics["trends"] = [word for word in words if word in trend_words]
        
        return metrics