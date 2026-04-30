import json
from textwrap import dedent

from crewai import Crew, LLM, Process, Task

from src.agents.compliance_agent import create_compliance_agent
from src.agents.order_context_agent import create_order_context_agent
from src.agents.policy_retriever_agent import create_policy_retriever_agent
from src.agents.resolution_writer_agent import create_resolution_writer_agent
from src.agents.triage_agent import create_triage_agent
from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME, VECTORSTORE_DIR
from src.prompts.agent_prompts import (
    COMPLIANCE_TASK_PROMPT,
    ORDER_CONTEXT_TASK_PROMPT,
    POLICY_RETRIEVER_TASK_PROMPT,
    TRIAGE_TASK_PROMPT,
    WRITER_TASK_PROMPT,
)
from src.ui_adapter import (
    UiRunResult,
    collect_stage_outputs,
    is_vectorstore_ready,
    normalize_ui_run_result,
    validate_ticket_payload,
)
from src.utils.pii_redactor import PIIRedactor


def build_support_crew(ticket_text: str, order_context: str) -> Crew:
    """Builds the CrewAI process for handling a support ticket."""

    llm = LLM(
        model=f"openrouter/{OPENAI_MODEL_NAME}",
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )

    triage_ag = create_triage_agent(llm)
    order_context_ag = create_order_context_agent(llm)
    retriever_ag = create_policy_retriever_agent(llm)
    writer_ag = create_resolution_writer_agent(llm)
    compliance_ag = create_compliance_agent(llm)

    triage_task = Task(
        description=dedent(
            TRIAGE_TASK_PROMPT.format(
                ticket_text=ticket_text,
                order_context=order_context,
            )
        ),
        expected_output="JSON with issue_type, sub_type, missing_fields, clarifying_questions, confidence.",
        agent=triage_ag,
    )

    context_task = Task(
        description=dedent(
            ORDER_CONTEXT_TASK_PROMPT.format(
                ticket_text=ticket_text,
                order_context=order_context,
            )
        ),
        expected_output="A concise bulleted list of order flags (e.g. final sale, regional policy).",
        agent=order_context_ag,
    )

    retrieval_task = Task(
        description=dedent(
            POLICY_RETRIEVER_TASK_PROMPT.format(
                issue_type="{triage_task.output}",
                sub_type="See Triage Output",
                order_flags="{context_task.output}",
                ticket_text=ticket_text,
            )
        ),
        expected_output="Raw JSON list of 5 most relevant policy excerpts (doc_title, section, chunk_id, excerpt).",
        agent=retriever_ag,
        context=[triage_task, context_task],
    )

    writer_task = Task(
        description=dedent(
            WRITER_TASK_PROMPT.format(
                ticket_text=ticket_text,
                order_flags="{context_task.output}",
                policy_excerpts="{retrieval_task.output}",
            )
        ),
        expected_output="Structured text with Decision, Rationale (with citations), Citations Used, Draft Response, Next Steps.",
        agent=writer_ag,
        context=[context_task, retrieval_task],
    )

    compliance_task = Task(
        description=dedent(
            COMPLIANCE_TASK_PROMPT.format(
                policy_excerpts="{retrieval_task.output}",
                drafted_resolution="{writer_task.output}",
            )
        ),
        expected_output="JSON with passed (boolean), issues (list), action ('approve', 'rewrite', 'escalate').",
        agent=compliance_ag,
        context=[retrieval_task, writer_task],
    )

    return Crew(
        agents=[triage_ag, order_context_ag, retriever_ag, writer_ag, compliance_ag],
        tasks=[triage_task, context_task, retrieval_task, writer_task, compliance_task],
        process=Process.sequential,
        verbose=True,
    )


def run_ticket_resolution(ticket_text: str, order_context: str, max_retries: int = 2):
    """
    Runs the Crew process and returns the raw CrewAI result.
    """
    result = None
    for attempt in range(max_retries + 1):
        print(f"--- Running Crew (Attempt {attempt + 1}) ---")
        crew = build_support_crew(ticket_text, order_context)
        result = crew.kickoff()

        final_output = str(result.raw if hasattr(result, "raw") else result)
        lowered = final_output.lower()
        is_approve = "approve" in lowered
        is_escalate = "escalate" in lowered
        is_rewrite = "rewrite" in lowered

        if is_approve or is_escalate or attempt == max_retries:
            return result

        if is_rewrite:
            print("Compliance check failed! Triggering a rewrite...")

    return result


def run_ticket_resolution_ui(ticket_payload: dict, max_retries: int = 2, progress_callback=None) -> UiRunResult:
    """
    Frontend-safe helper for Gradio and Spaces.
    Validates the payload, runs the crew, and returns a normalized result object.
    """
    validation_error = validate_ticket_payload(ticket_payload)
    if validation_error:
        return UiRunResult.from_error(
            "Invalid input payload",
            validation_error,
            raw_output={"input": ticket_payload},
        )

    if not OPENAI_API_KEY:
        return UiRunResult.from_error(
            "Missing API key",
            "Set the `OPENAI_API_KEY` environment variable before running the analysis.",
            raw_output={"input": ticket_payload},
        )

    if not is_vectorstore_ready(VECTORSTORE_DIR):
        return UiRunResult.from_error(
            "Vector store not ready",
            "The local Chroma vector store was not found. Run `python ingest.py` to build `data/vectorstore/` before launching the app.",
            raw_output={"input": ticket_payload, "vectorstore_dir": str(VECTORSTORE_DIR)},
        )

    ticket_text = json.dumps(ticket_payload.get("ticket", {}), ensure_ascii=False)
    order_context = json.dumps(ticket_payload.get("order_context", {}), ensure_ascii=False)
    safe_ticket_text = PIIRedactor.redact(ticket_text)
    pii_was_redacted = safe_ticket_text != ticket_text

    try:
        if progress_callback:
            progress_callback(0.1, "Preparing agent workflow")
        result = None
        stage_outputs = None

        for attempt in range(max_retries + 1):
            if progress_callback:
                progress_callback(
                    min(0.35 + (attempt * 0.1), 0.7),
                    f"Running multi-agent analysis (attempt {attempt + 1})",
                )

            crew = build_support_crew(safe_ticket_text, order_context)
            result = crew.kickoff()
            stage_outputs = collect_stage_outputs(crew, result)

            compliance_text = stage_outputs.get("compliance", "") or stage_outputs.get("final", "")
            lowered = compliance_text.lower()
            if "rewrite" not in lowered or attempt == max_retries:
                break

            print("Compliance check failed! Triggering a rewrite...")

        if progress_callback:
            progress_callback(0.82, "Normalizing agent output")

        normalized = normalize_ui_run_result(
            ticket_payload=ticket_payload,
            stage_outputs=stage_outputs or {"final": ""},
            pii_was_redacted=pii_was_redacted,
        )

        if progress_callback:
            progress_callback(1.0, "Run complete")

        return normalized
    except Exception as exc:
        return UiRunResult.from_error(
            "Execution failed",
            f"The backend run did not complete successfully: {exc}",
            raw_output={
                "input": ticket_payload,
                "exception": str(exc),
            },
        )
