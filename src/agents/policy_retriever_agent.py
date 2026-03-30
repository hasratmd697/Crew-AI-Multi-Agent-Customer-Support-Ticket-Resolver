import json
from crewai import Agent
from crewai.tools import tool
from src.prompts.agent_prompts import POLICY_RETRIEVER_ROLE, POLICY_RETRIEVER_GOAL, POLICY_RETRIEVER_BACKSTORY
from src.ingestion.embedder import get_retriever

# Define a custom CrewAI tool for vector search
@tool("Search Policy Knowledge Base")
def search_policy_kb(query: str) -> str:
    """
    Search the ecommerce policy knowledge base for relevant rules and exceptions.
    Input should be a specific search query like 'return policy for perishable items'.
    """
    try:
        retriever = get_retriever()
        docs = retriever.invoke(query)
        
        results = []
        for d in docs:
            chunk_data = {
                "doc_title": d.metadata.get("doc_title", "Unknown"),
                "section": d.metadata.get("section", "Unknown"),
                "chunk_id": d.metadata.get("chunk_id", "Unknown"),
                "excerpt": d.page_content
            }
            results.append(chunk_data)
        
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching KB: {str(e)}"

def create_policy_retriever_agent(llm) -> Agent:
    """
    Creates the Policy Retriever Agent empowered with the vector search tool.
    """
    return Agent(
        role=POLICY_RETRIEVER_ROLE,
        goal=POLICY_RETRIEVER_GOAL,
        backstory=POLICY_RETRIEVER_BACKSTORY,
        llm=llm,
        tools=[search_policy_kb],
        verbose=True,
        allow_delegation=False
    )
