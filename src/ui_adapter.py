import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class UiRunResult:
    success: bool
    error_title: Optional[str] = None
    error_message: Optional[str] = None
    classification: Dict[str, Any] = field(default_factory=dict)
    order_flags: List[str] = field(default_factory=list)
    retrieved_excerpts: List[Dict[str, Any]] = field(default_factory=list)
    decision: str = "not run"
    rationale: str = ""
    customer_response_draft: str = ""
    next_steps: List[str] = field(default_factory=list)
    compliance_check: Dict[str, Any] = field(default_factory=dict)
    run_notes: List[str] = field(default_factory=list)
    raw_output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_error(
        cls,
        title: str,
        message: str,
        raw_output: Optional[Dict[str, Any]] = None,
    ) -> "UiRunResult":
        return cls(
            success=False,
            error_title=title,
            error_message=message,
            compliance_check={
                "passed": False,
                "issues": [message],
                "action": "escalate",
            },
            run_notes=["The request did not complete successfully."],
            raw_output=raw_output or {},
        )


STAGE_NAMES = ["triage", "order_context", "retrieval", "writer", "compliance"]


def validate_ticket_payload(ticket_payload: Dict[str, Any]) -> Optional[str]:
    if not isinstance(ticket_payload, dict):
        return "Input must be a JSON object with `ticket` and `order_context` keys."

    ticket = ticket_payload.get("ticket")
    order_context = ticket_payload.get("order_context")

    if not isinstance(ticket, dict):
        return "`ticket` must be a JSON object."

    if not isinstance(order_context, dict):
        return "`order_context` must be a JSON object."

    ticket_text = ticket.get("text")
    if not isinstance(ticket_text, str) or not ticket_text.strip():
        return "`ticket.text` is required and must be a non-empty string."

    return None


def is_vectorstore_ready(vectorstore_dir: Path) -> bool:
    if not vectorstore_dir.exists():
        return False

    sqlite_exists = (vectorstore_dir / "chroma.sqlite3").exists()
    chunk_dirs = [path for path in vectorstore_dir.iterdir() if path.is_dir()]
    return sqlite_exists and bool(chunk_dirs)


def coerce_output_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if hasattr(value, "raw"):
        return str(value.raw)
    if hasattr(value, "output"):
        return coerce_output_text(value.output)
    return str(value)


def collect_stage_outputs(crew: Any, result: Any) -> Dict[str, str]:
    stage_outputs = {name: "" for name in STAGE_NAMES}

    candidate_lists: List[Iterable[Any]] = []
    result_tasks_output = getattr(result, "tasks_output", None)
    if isinstance(result_tasks_output, list):
        candidate_lists.append(result_tasks_output)

    crew_tasks = getattr(crew, "tasks", None)
    if isinstance(crew_tasks, list):
        candidate_lists.append(crew_tasks)

    for source in candidate_lists:
        for index, stage_name in enumerate(STAGE_NAMES):
            if stage_outputs[stage_name]:
                continue
            if index >= len(source):
                continue
            text = coerce_output_text(source[index]).strip()
            if text:
                stage_outputs[stage_name] = text

    stage_outputs["final"] = coerce_output_text(result).strip()
    return stage_outputs


def find_json_value(text: str, expected_type: Optional[type] = None) -> Any:
    if not text:
        return None

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if expected_type is not None and not isinstance(value, expected_type):
            continue
        return value
    return None


def parse_triage_output(text: str) -> Dict[str, Any]:
    parsed = find_json_value(text, dict) or {}
    confidence = parsed.get("confidence", 0.0)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    return {
        "issue_type": str(parsed.get("issue_type", "unknown")).strip() or "unknown",
        "sub_type": str(parsed.get("sub_type", "unknown")).strip() or "unknown",
        "confidence": confidence,
        "missing_fields": parsed.get("missing_fields", []) or [],
        "clarifying_questions": parsed.get("clarifying_questions", []) or [],
    }


def parse_order_flags(text: str) -> List[str]:
    flags: List[str] = []
    for line in text.splitlines():
        clean = line.strip()
        clean = re.sub(r"^[\-\*\u2022\d\.\)\(]+\s*", "", clean)
        if clean:
            flags.append(clean)
    return flags


def parse_retrieval_output(text: str) -> List[Dict[str, Any]]:
    parsed = find_json_value(text, list) or []
    excerpts: List[Dict[str, Any]] = []

    for item in parsed:
        if not isinstance(item, dict):
            continue
        excerpts.append(
            {
                "doc_title": str(item.get("doc_title", "Unknown")),
                "section": str(item.get("section", "Unknown")),
                "chunk_id": str(item.get("chunk_id", "Unknown")),
                "excerpt": str(item.get("excerpt", "")).strip(),
            }
        )

    return excerpts


def parse_writer_output(text: str) -> Dict[str, Any]:
    if not text:
        return {
            "decision": "not available",
            "rationale": "",
            "citations_used": [],
            "customer_response_draft": "",
            "next_steps": [],
        }

    heading_pattern = re.compile(
        r"(?im)^\s*(?:\*\*)?(Decision|Rationale|Citations Used|Draft Response|Next Steps)(?:\*\*)?\s*:\s*"
    )
    matches = list(heading_pattern.finditer(text))
    sections: Dict[str, str] = {}

    for index, match in enumerate(matches):
        key = match.group(1).lower().replace(" ", "_")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[key] = text[match.end() : end].strip()

    decision = sections.get("decision", "")
    if not decision:
        lowered = text.lower()
        if "needs escalation" in lowered:
            decision = "needs escalation"
        elif "approve" in lowered:
            decision = "approve"

    citations_used = sections.get("citations_used", "")
    citations = [
        item.strip("-* \n\t")
        for item in re.split(r"[,\\n]", citations_used)
        if item.strip("-* \n\t")
    ]

    next_steps_text = sections.get("next_steps", "")
    next_steps = [item.strip("-* \n\t") for item in next_steps_text.splitlines() if item.strip("-* \n\t")]
    if not next_steps and next_steps_text.strip():
        next_steps = [next_steps_text.strip()]

    return {
        "decision": decision.strip() or "not available",
        "rationale": sections.get("rationale", "").strip(),
        "citations_used": citations,
        "customer_response_draft": sections.get("draft_response", "").strip(),
        "next_steps": next_steps,
    }


def parse_compliance_output(text: str) -> Dict[str, Any]:
    parsed = find_json_value(text, dict) or {}
    action = str(parsed.get("action", "")).strip().lower()
    if not action:
        lowered = text.lower()
        if "rewrite" in lowered:
            action = "rewrite"
        elif "escalate" in lowered:
            action = "escalate"
        elif "approve" in lowered:
            action = "approve"
        else:
            action = "unknown"

    return {
        "passed": bool(parsed.get("passed", False)),
        "issues": parsed.get("issues", []) or [],
        "action": action,
    }


def build_run_notes(triage: Dict[str, Any], order_flags: List[str], pii_was_redacted: bool) -> List[str]:
    notes: List[str] = []

    if pii_was_redacted:
        notes.append("Potentially sensitive patterns were redacted from ticket text before agent execution.")

    for field_name in triage.get("missing_fields", []):
        notes.append(f"Missing field flagged by triage: {field_name}")

    for question in triage.get("clarifying_questions", []):
        notes.append(f"Clarifying question: {question}")

    if not order_flags:
        notes.append("Order context analyzer did not return structured flags.")

    return notes


def normalize_ui_run_result(
    ticket_payload: Dict[str, Any],
    stage_outputs: Dict[str, str],
    pii_was_redacted: bool = False,
) -> UiRunResult:
    triage = parse_triage_output(stage_outputs.get("triage", ""))
    order_flags = parse_order_flags(stage_outputs.get("order_context", ""))
    retrieved_excerpts = parse_retrieval_output(stage_outputs.get("retrieval", ""))
    writer = parse_writer_output(stage_outputs.get("writer", ""))
    compliance = parse_compliance_output(stage_outputs.get("compliance", "") or stage_outputs.get("final", ""))

    citation_check = None
    rationale = writer.get("rationale", "")
    if rationale and retrieved_excerpts:
        from src.utils.citation_checker import CitationChecker

        citation_check = CitationChecker.verify_citations(rationale, retrieved_excerpts)
        if not citation_check.get("passed", False):
            issues = compliance.setdefault("issues", [])
            issues.append(citation_check.get("reason", "Citation validation failed."))

    compliance_action = compliance.get("action", "unknown")
    passed = bool(compliance.get("passed", False))
    if citation_check and not citation_check.get("passed", False):
        passed = False
        if compliance_action == "approve":
            compliance_action = "rewrite"

    compliance["passed"] = passed
    compliance["action"] = compliance_action

    return UiRunResult(
        success=True,
        classification={
            "issue_type": triage.get("issue_type", "unknown"),
            "sub_type": triage.get("sub_type", "unknown"),
            "confidence": triage.get("confidence", 0.0),
        },
        order_flags=order_flags,
        retrieved_excerpts=retrieved_excerpts,
        decision=writer.get("decision", "not available"),
        rationale=writer.get("rationale", ""),
        customer_response_draft=writer.get("customer_response_draft", ""),
        next_steps=writer.get("next_steps", []),
        compliance_check=compliance,
        run_notes=build_run_notes(triage, order_flags, pii_was_redacted)
        + (
            ["Intermediate task outputs were only partially available; raw stage text is preserved in the debug panel."]
            if not stage_outputs.get("writer") or not stage_outputs.get("retrieval")
            else []
        ),
        raw_output={
            "input": ticket_payload,
            "stages": stage_outputs,
        },
    )
