import json
from crewai import Agent
from src.prompts.agent_prompts import COMPLIANCE_ROLE, COMPLIANCE_GOAL, COMPLIANCE_BACKSTORY

def create_compliance_agent(llm) -> Agent:
    """
    Creates the Compliance / Safety Agent.
    """
    return Agent(
        role=COMPLIANCE_ROLE,
        goal=COMPLIANCE_GOAL,
        backstory=COMPLIANCE_BACKSTORY,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
