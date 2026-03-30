from crewai import Agent
from src.prompts.agent_prompts import WRITER_ROLE, WRITER_GOAL, WRITER_BACKSTORY

def create_resolution_writer_agent(llm) -> Agent:
    """
    Creates the Resolution Writer Agent. Must adhere strictly to evidence from retriever.
    """
    return Agent(
        role=WRITER_ROLE,
        goal=WRITER_GOAL,
        backstory=WRITER_BACKSTORY,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
