from crewai import Agent
from src.prompts.agent_prompts import ORDER_CONTEXT_ROLE, ORDER_CONTEXT_GOAL, ORDER_CONTEXT_BACKSTORY

def create_order_context_agent(llm) -> Agent:
    """
    Creates the Order Context Analyzer Agent.
    """
    return Agent(
        role=ORDER_CONTEXT_ROLE,
        goal=ORDER_CONTEXT_GOAL,
        backstory=ORDER_CONTEXT_BACKSTORY,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
