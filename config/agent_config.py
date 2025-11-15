"""
Agent Optimization Configuration
Centralized profiles for model, reasoning, and verbosity settings
"""
from dataclasses import dataclass
from openai.types.shared import Reasoning
from agents import ModelSettings
from typing import Optional


@dataclass
class AgentOptimizationProfile:
    """Optimization profile for an agent"""
    model: str
    reasoning_effort: str  # "minimal", "low", "medium", "high"
    verbosity: str  # "low", "medium", "high"
    max_turns: int
    
    def to_model_settings(self) -> ModelSettings:
        """Convert to ModelSettings object with Reasoning"""
        return ModelSettings(
            reasoning=Reasoning(effort=self.reasoning_effort),
            verbosity=self.verbosity
        )


# Pre-defined profiles for different agent types
AGENT_PROFILES = {
    # ============================================================
    # MEMORY AGENT SUB-AGENTS (fast classification)
    # ============================================================
    
    "intent_classifier": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="minimal",  # Single classification task
        verbosity="low",             # Structured output only
        max_turns=1
    ),
    
    "rule_extractor": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Some inference needed
        verbosity="low",             # Structured output only
        max_turns=1
    ),
    
    "rule_filter": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Semantic matching
        verbosity="low",             # Structured output only
        max_turns=1
    ),
    
    "complexity_classifier": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="minimal",  # Pattern matching
        verbosity="low",             # Structured output only
        max_turns=1
    ),
    
    # ============================================================
    # SPECIALIST SUB-AGENTS (Communication focused)
    # ============================================================
    
    "calendar": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Straightforward scheduling
        verbosity="low",             # Concise summaries
        max_turns=10
    ),
    
    "email": AgentOptimizationProfile(
        model="gpt-5.1",
        reasoning_effort="medium",   # Tone, composition, rules
        verbosity="medium",          # Professional formatting
        max_turns=10
    ),
    
    "report_writer": AgentOptimizationProfile(
        model="gpt-5.1",
        reasoning_effort="medium",   # Creative composition
        verbosity="medium",          # Structured documents
        max_turns=10
    ),
    
    "whatsapp": AgentOptimizationProfile(
        model="gpt-5-nano",
        reasoning_effort="minimal",  # Simple message formatting
        verbosity="low",             # Concise mobile text
        max_turns=5
    ),
    
    # ============================================================
    # ANALYTICS AGENTS (DDMac Analytics Database)
    # ============================================================
    
    "employee_analytics": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Data queries with some analysis
        verbosity="medium",          # Detailed analytics summaries
        max_turns=5
    ),
    
    "project_analytics": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Budget and variance analysis
        verbosity="medium",          # Detailed project insights
        max_turns=5
    ),
    
    "task_analytics": AgentOptimizationProfile(
        model="gpt-5-mini",
        reasoning_effort="low",      # Task-level data analysis
        verbosity="medium",          # Detailed task breakdowns
        max_turns=5
    ),
}


# ============================================================
# DYNAMIC ORCHESTRATOR PROFILES (based on task complexity)
# ============================================================

ORCHESTRATOR_PROFILES = {
    "SIMPLE": AgentOptimizationProfile(
        model="gpt-5.1",
        reasoning_effort="minimal",  # Quick decisions
        verbosity="low",             # Brief responses
        max_turns=15
    ),
    
    "MEDIUM": AgentOptimizationProfile(
        model="gpt-5.1",
        reasoning_effort="low",      # Some planning needed
        verbosity="medium",          # Standard responses
        max_turns=30
    ),
    
    "COMPLEX": AgentOptimizationProfile(
        model="gpt-5.1",
        reasoning_effort="medium",   # Deep analysis
        verbosity="medium",          # Detailed responses
        max_turns=45
    ),
}


def get_agent_profile(agent_type: str) -> AgentOptimizationProfile:
    """
    Get optimization profile for an agent type
    
    Args:
        agent_type: Type of agent (calendar, email, etc.)
    
    Returns:
        AgentOptimizationProfile for that agent type
    """
    return AGENT_PROFILES.get(agent_type, AGENT_PROFILES["email"])


def get_orchestrator_profile(complexity: str) -> AgentOptimizationProfile:
    """
    Get dynamic orchestrator profile based on task complexity
    
    Args:
        complexity: Task complexity (SIMPLE, MEDIUM, COMPLEX)
    
    Returns:
        AgentOptimizationProfile for that complexity level
    """
    return ORCHESTRATOR_PROFILES.get(complexity.upper(), ORCHESTRATOR_PROFILES["MEDIUM"])

