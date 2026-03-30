from textwrap import dedent
from crewai import Task, Crew, Process, LLM

from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME, OPENAI_API_BASE
from src.agents.triage_agent import create_triage_agent
from src.agents.order_context_agent import create_order_context_agent
from src.agents.policy_retriever_agent import create_policy_retriever_agent
from src.agents.resolution_writer_agent import create_resolution_writer_agent
from src.agents.compliance_agent import create_compliance_agent
from src.prompts.agent_prompts import (
    TRIAGE_TASK_PROMPT, ORDER_CONTEXT_TASK_PROMPT, 
    POLICY_RETRIEVER_TASK_PROMPT, WRITER_TASK_PROMPT, COMPLIANCE_TASK_PROMPT
)

def build_support_crew(ticket_text: str, order_context: str) -> Crew:
    """Builds the CrewAI process for handling a support ticket."""
    
    # Initialize LLM using CrewAI's LLM wrapper (backed by LiteLLM)
    # Use the openrouter/ prefix so LiteLLM routes correctly without needing base_url
    llm = LLM(
        model=f"openrouter/{OPENAI_MODEL_NAME}",
        api_key=OPENAI_API_KEY,
        temperature=0.1
    )
    
    # Instantiate Agents
    triage_ag = create_triage_agent(llm)
    order_context_ag = create_order_context_agent(llm)
    retriever_ag = create_policy_retriever_agent(llm)
    writer_ag = create_resolution_writer_agent(llm)
    compliance_ag = create_compliance_agent(llm)
    
    # 1. Triage Task
    triage_task = Task(
        description=dedent(TRIAGE_TASK_PROMPT.format(
            ticket_text=ticket_text, 
            order_context=order_context
        )),
        expected_output="JSON with issue_type, sub_type, missing_fields, clarifying_questions, confidence.",
        agent=triage_ag
    )
    
    # 2. Context Analysis Task
    context_task = Task(
        description=dedent(ORDER_CONTEXT_TASK_PROMPT.format(
            ticket_text=ticket_text,
            order_context=order_context
        )),
        expected_output="A concise bulleted list of order flags (e.g. final sale, regional policy).",
        agent=order_context_ag
    )
    
    # 3. Policy Retrieval Task
    retrieval_task = Task(
        description=dedent(POLICY_RETRIEVER_TASK_PROMPT.format(
            issue_type="{triage_task.output}",
            sub_type="See Triage Output",
            order_flags="{context_task.output}",
            ticket_text=ticket_text
        )),
        expected_output="Raw JSON list of 5 most relevant policy excerpts (doc_title, section, chunk_id, excerpt).",
        agent=retriever_ag,
        context=[triage_task, context_task]
    )
    
    # 4. Resolution Writer Task
    writer_task = Task(
        description=dedent(WRITER_TASK_PROMPT.format(
            ticket_text=ticket_text,
            order_flags="{context_task.output}",
            policy_excerpts="{retrieval_task.output}"
        )),
        expected_output="Structured text with Decision, Rationale (with citations), Citations Used, Draft Response, Next Steps.",
        agent=writer_ag,
        context=[context_task, retrieval_task]
    )
    
    # 5. Compliance & Safety Review Task
    compliance_task = Task(
        description=dedent(COMPLIANCE_TASK_PROMPT.format(
            policy_excerpts="{retrieval_task.output}",
            drafted_resolution="{writer_task.output}"
        )),
        expected_output="JSON with passed (boolean), issues (list), action ('approve', 'rewrite', 'escalate').",
        agent=compliance_ag,
        context=[retrieval_task, writer_task]
    )
    
    crew = Crew(
        agents=[triage_ag, order_context_ag, retriever_ag, writer_ag, compliance_ag],
        tasks=[triage_task, context_task, retrieval_task, writer_task, compliance_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew

def run_ticket_resolution(ticket_text: str, order_context: str, max_retries=2):
    """
    Runs the Crew process. Handles the rewrite loop programmatically if 
    Compliance Agent triggers a rewrite.
    """
    for attempt in range(max_retries + 1):
        print(f"--- Running Crew (Attempt {attempt + 1}) ---")
        crew = build_support_crew(ticket_text, order_context)
        
        # In CrewAI > v0.80, kickoff returns a CrewOutput object
        result = crew.kickoff()
        
        # Extract the final task output (Compliance Task)
        # Note: Depending on CrewAI version, accessing task outputs varies. 
        # Safest way in raw text:
        final_output = str(result.raw if hasattr(result, 'raw') else result)
        
        # Crude extraction of action from final output JSON
        # A more robust system would parse the JSON properly.
        is_approve = 'approve' in final_output.lower()
        is_escalate = 'escalate' in final_output.lower()
        is_rewrite = 'rewrite' in final_output.lower()
        
        if is_approve or is_escalate or attempt == max_retries:
            return result
        
        print("Compliance check failed! Triggering a rewrite...")
        
    return result
