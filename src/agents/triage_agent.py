from crewai import Agent
from src.prompts.agent_prompts import TRIAGE_AGENT_ROLE, TRIAGE_AGENT_GOAL, TRIAGE_AGENT_BACKSTORY

def create_triage_agent(llm) -> Agent:
    """
    Creates the Triage Agent which classifies the ticket and identifies missing info.
    """
    return Agent(
        role=TRIAGE_AGENT_ROLE,
        goal=TRIAGE_AGENT_GOAL,
        backstory=TRIAGE_AGENT_BACKSTORY,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
