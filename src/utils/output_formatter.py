import json
from typing import Dict, Any

class OutputFormatter:
    """
    Formats the final output combining results from all agents into the required JSON structure.
    """
    
    @staticmethod
    def format_final_resolution(
        triage_result: Dict[str, Any],
        retriever_result: Dict[str, Any],
        writer_result: Dict[str, Any],
        compliance_result: Dict[str, Any]
    ) -> str:
        """
        Combines agent outputs into the final schema.
        """
        
        output = {
            "classification": {
                "issue_type": triage_result.get("issue_type", "unknown"),
                "confidence": triage_result.get("confidence", 0.0)
            },
            "clarifying_questions": triage_result.get("clarifying_questions", []),
            "decision": writer_result.get("decision", "needs escalation"),
            "rationale": writer_result.get("rationale", ""),
            "citations": retriever_result.get("citations_used", []),
            "customer_response_draft": writer_result.get("customer_response_draft", ""),
            "next_steps": writer_result.get("next_steps", []),
            "compliance_check": {
                "passed": compliance_result.get("passed", False),
                "issues": compliance_result.get("issues", []),
                "action_taken": compliance_result.get("action", "escalate")
            }
        }
        
        return json.dumps(output, indent=2)
