import html
import json
from typing import Any, Dict, List

import gradio as gr
from dotenv import load_dotenv

from src.config import OPENAI_API_KEY, OPENAI_MODEL_NAME, TEST_TICKETS_DIR, VECTORSTORE_DIR
from src.orchestrator import run_ticket_resolution_ui
from src.ui_adapter import UiRunResult, is_vectorstore_ready


load_dotenv()


CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --pm-bg: #f5f1eb;
  --pm-panel: #fbf9f5;
  --pm-panel-2: #f1ece4;
  --pm-border: #d5cec3;
  --pm-border-strong: #b7aea1;
  --pm-text: #1d2328;
  --pm-text-muted: #556069;
  --pm-accent: #1f6262;
  --pm-warning: #8a5a17;
  --pm-danger: #8b3431;
  --pm-success: #24563b;
}

body, .gradio-container {
  background: var(--pm-bg) !important;
  color: var(--pm-text) !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
}

.gradio-container {
  max-width: 1400px !important;
}

.app-header,
.panel,
.status-card,
.metric-block,
.text-block,
.evidence-card,
.notice {
  border: 1px solid var(--pm-border);
  background: var(--pm-panel);
}

.app-header {
  padding: 18px 20px;
  margin-bottom: 16px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--pm-text-muted);
  margin-bottom: 8px;
}

.app-title {
  margin: 0;
  font-size: 32px;
  line-height: 1.1;
  font-weight: 700;
}

.app-subtitle {
  margin: 10px 0 0;
  color: var(--pm-text-muted);
  font-size: 15px;
  max-width: 920px;
}

.app-meta,
.evidence-meta,
.status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.meta-chip,
.evidence-chip {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border: 1px solid var(--pm-border);
  background: #f1ece4;
  font-size: 12px;
  font-weight: 600;
}

.panel {
  padding: 16px;
}

.panel-heading {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
}

.section-note,
.status-label,
.text-title,
.evidence-title {
  color: var(--pm-text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.status-card,
.metric-block,
.text-block,
.evidence-card,
.notice {
  padding: 12px 14px;
}

.status-value {
  font-size: 18px;
  font-weight: 700;
  margin-top: 8px;
}

.status-subvalue,
.text-content,
.evidence-excerpt,
.notes-list,
.compliance-list {
  margin-top: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 14px;
}

.decision-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 14px;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
}

.notes-list,
.compliance-list {
  margin: 8px 0 0;
  padding-left: 18px;
}

.soft-divider {
  border-top: 1px solid var(--pm-border);
  margin: 14px 0;
}

.evidence-list {
  display: grid;
  gap: 12px;
}

.mono,
.gradio-container textarea,
.gradio-container code,
.gradio-container pre {
  font-family: 'IBM Plex Mono', monospace !important;
}

.primary-button {
  background: var(--pm-accent) !important;
  color: #ffffff !important;
  border: 1px solid var(--pm-accent) !important;
}

.secondary-button {
  background: var(--pm-panel) !important;
  color: var(--pm-text) !important;
  border: 1px solid var(--pm-border-strong) !important;
}

.notice.error {
  border-color: #d3a29b;
  background: #f7ebe9;
}

.notice.warning {
  border-color: #ddc48e;
  background: #f6eedb;
}

.notice.success {
  border-color: #b7cbbf;
  background: #edf3ef;
}

.success-text {
  color: var(--pm-success);
}

.warning-text {
  color: var(--pm-warning);
}

.danger-text {
  color: var(--pm-danger);
}

.gradio-container .gr-button,
.gradio-container .tab-nav button,
.gradio-container .gr-box,
.gradio-container .block {
  border-radius: 0 !important;
  box-shadow: none !important;
}

@media (max-width: 980px) {
  .status-strip,
  .decision-grid {
    grid-template-columns: 1fr;
  }
}
"""


EXAMPLE_FILES = {
    "Late Delivery / Perishable Refund": "tc01_exception.json",
    "Marketplace Policy Conflict": "tc02_conflict.json",
    "Ambiguous Final-Sale Request": "tc03_abstain.json",
}


def load_example_payloads() -> Dict[str, Dict[str, Any]]:
    payloads: Dict[str, Dict[str, Any]] = {}
    for label, filename in EXAMPLE_FILES.items():
        path = TEST_TICKETS_DIR / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as file_handle:
                payloads[label] = json.load(file_handle)
    return payloads


EXAMPLE_PAYLOADS = load_example_payloads()


def build_header_html() -> str:
    vector_status = "Ready" if is_vectorstore_ready(VECTORSTORE_DIR) else "Missing"
    api_status = "Configured" if OPENAI_API_KEY else "Missing"
    return f"""
    <div class="app-header">
      <div class="eyebrow">PurpleMerit Assessment</div>
      <h1 class="app-title">Support Resolution Ops Console</h1>
      <p class="app-subtitle">
        Professional review interface for ticket intake, retrieved policy evidence, final customer drafting,
        and compliance decisions. Structured outputs only, no chain-of-thought exposure.
      </p>
      <div class="app-meta">
        <span class="meta-chip">Framework: Gradio</span>
        <span class="meta-chip">Model: {html.escape(OPENAI_MODEL_NAME)}</span>
        <span class="meta-chip">API Key: {html.escape(api_status)}</span>
        <span class="meta-chip">Vector Store: {html.escape(vector_status)}</span>
      </div>
    </div>
    """


def build_alert_html(message: str, level: str = "warning") -> str:
    return f'<div class="notice {level}">{html.escape(message)}</div>'


def empty_status_html() -> str:
    return """
    <div class="status-strip">
      <div class="status-card"><div class="status-label">Issue Type</div><div class="status-value">Awaiting run</div><div class="status-subvalue">Classification has not been generated yet.</div></div>
      <div class="status-card"><div class="status-label">Confidence</div><div class="status-value">--</div><div class="status-subvalue">Run an analysis to score routing confidence.</div></div>
      <div class="status-card"><div class="status-label">Decision</div><div class="status-value">--</div><div class="status-subvalue">Writer outcome will appear here.</div></div>
      <div class="status-card"><div class="status-label">Compliance</div><div class="status-value">--</div><div class="status-subvalue">Approve, rewrite, or escalate.</div></div>
    </div>
    """


def empty_decision_html() -> str:
    return """
    <div class="decision-grid">
      <div class="text-block"><div class="text-title">Rationale</div><div class="text-content">Policy-grounded rationale will appear here after a run.</div></div>
      <div class="metric-block"><div class="text-title">Run Notes</div><div class="text-content">Validation notes, redaction warnings, and clarifying prompts will appear here.</div></div>
    </div>
    """


def empty_evidence_html() -> str:
    return '<div class="notice warning">No policy excerpts loaded yet. Run a ticket to populate retrieved evidence.</div>'


def empty_compliance_html() -> str:
    return '<div class="text-block"><div class="text-title">Compliance Review</div><div class="text-content">Compliance output will appear here after an analysis run.</div></div>'


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def payload_to_form_values(payload: Dict[str, Any]) -> List[Any]:
    ticket = payload.get("ticket", {})
    order = payload.get("order_context", {})
    return [
        ticket.get("text", ""),
        ticket.get("customer_id", ""),
        ticket.get("channel", "email"),
        order.get("order_id", ""),
        order.get("order_date", ""),
        order.get("delivery_date", ""),
        order.get("expected_delivery_date", ""),
        order.get("item_category", ""),
        order.get("item_name", ""),
        order.get("item_price", 0),
        order.get("fulfillment_type", "first-party"),
        order.get("seller_name", ""),
        order.get("shipping_region", ""),
        order.get("order_status", "delivered"),
        order.get("payment_method", "credit_card"),
        bool(order.get("is_final_sale", False)),
        pretty_json(payload),
    ]


def build_payload_from_form(
    ticket_text: str,
    customer_id: str,
    channel: str,
    order_id: str,
    order_date: str,
    delivery_date: str,
    expected_delivery_date: str,
    item_category: str,
    item_name: str,
    item_price: float,
    fulfillment_type: str,
    seller_name: str,
    shipping_region: str,
    order_status: str,
    payment_method: str,
    is_final_sale: bool,
) -> Dict[str, Any]:
    order_context = {
        "order_id": order_id.strip(),
        "order_date": order_date.strip(),
        "delivery_date": delivery_date.strip(),
        "expected_delivery_date": expected_delivery_date.strip(),
        "item_category": item_category.strip(),
        "item_name": item_name.strip(),
        "item_price": float(item_price or 0),
        "fulfillment_type": fulfillment_type,
        "shipping_region": shipping_region.strip(),
        "order_status": order_status,
        "payment_method": payment_method,
        "is_final_sale": bool(is_final_sale),
    }
    if seller_name.strip():
        order_context["seller_name"] = seller_name.strip()

    return {
        "ticket": {
            "text": ticket_text.strip(),
            "customer_id": customer_id.strip(),
            "channel": channel,
        },
        "order_context": order_context,
    }


def render_status_strip(result: UiRunResult) -> str:
    issue_type = result.classification.get("issue_type", "unknown")
    sub_type = result.classification.get("sub_type", "unknown")
    confidence = result.classification.get("confidence", 0.0)
    decision = result.decision or "not available"
    action = result.compliance_check.get("action", "unknown")
    passed = result.compliance_check.get("passed", False)
    action_class = "success-text" if passed else ("warning-text" if action == "rewrite" else "danger-text")

    return f"""
    <div class="status-strip">
      <div class="status-card"><div class="status-label">Issue Type</div><div class="status-value">{html.escape(str(issue_type))}</div><div class="status-subvalue">Sub-type: {html.escape(str(sub_type))}</div></div>
      <div class="status-card"><div class="status-label">Confidence</div><div class="status-value">{float(confidence):.2f}</div><div class="status-subvalue">Triage confidence for the current routing decision.</div></div>
      <div class="status-card"><div class="status-label">Decision</div><div class="status-value">{html.escape(str(decision))}</div><div class="status-subvalue">Writer recommendation based on retrieved policy text.</div></div>
      <div class="status-card"><div class="status-label">Compliance</div><div class="status-value {action_class}">{html.escape(str(action))}</div><div class="status-subvalue">Passed: {"Yes" if passed else "No"}</div></div>
    </div>
    """


def render_decision_html(result: UiRunResult) -> str:
    notes = result.run_notes or ["No additional run notes were recorded."]
    notes_html = "".join(f"<li>{html.escape(note)}</li>" for note in notes)
    rationale = html.escape(result.rationale or "No rationale was captured from the writer stage.")
    return f"""
    <div class="decision-grid">
      <div class="text-block"><div class="text-title">Rationale</div><div class="text-content">{rationale}</div></div>
      <div class="metric-block"><div class="text-title">Run Notes</div><ul class="notes-list">{notes_html}</ul></div>
    </div>
    """


def render_evidence_html(result: UiRunResult) -> str:
    if not result.retrieved_excerpts:
        return empty_evidence_html()

    cards = []
    for excerpt in result.retrieved_excerpts:
        cards.append(
            f"""
            <div class="evidence-card">
              <div class="evidence-title">Retrieved Excerpt</div>
              <div class="evidence-meta">
                <span class="evidence-chip">{html.escape(excerpt.get("doc_title", "Unknown"))}</span>
                <span class="evidence-chip">{html.escape(excerpt.get("section", "Unknown"))}</span>
                <span class="evidence-chip mono">{html.escape(excerpt.get("chunk_id", "Unknown"))}</span>
              </div>
              <div class="evidence-excerpt">{html.escape(excerpt.get("excerpt", ""))}</div>
            </div>
            """
        )
    return f'<div class="evidence-list">{"".join(cards)}</div>'


def render_compliance_html(result: UiRunResult) -> str:
    compliance = result.compliance_check or {}
    issues = compliance.get("issues") or ["No issues reported."]
    issues_html = "".join(f"<li>{html.escape(str(issue))}</li>" for issue in issues)
    passed = "Passed" if compliance.get("passed") else "Failed"
    action = compliance.get("action", "unknown")
    return f"""
    <div class="text-block">
      <div class="text-title">Compliance Review</div>
      <div class="metric-value">{html.escape(passed)}</div>
      <div class="soft-divider"></div>
      <div class="text-title">Action</div>
      <div class="text-content">{html.escape(str(action))}</div>
      <div class="soft-divider"></div>
      <div class="text-title">Issues</div>
      <ul class="compliance-list">{issues_html}</ul>
    </div>
    """


def render_customer_draft(result: UiRunResult) -> str:
    if result.customer_response_draft.strip():
        return result.customer_response_draft
    return "No customer-facing draft was captured from the writer stage."


def result_to_outputs(result: UiRunResult):
    level = "success" if result.success else "error"
    message = "Run complete." if result.success else f"{result.error_title}: {result.error_message}"
    raw_json = pretty_json(result.to_dict())

    return (
        render_status_strip(result) if result.success else empty_status_html(),
        build_alert_html(message, level=level),
        render_decision_html(result) if result.success else empty_decision_html(),
        render_customer_draft(result),
        render_evidence_html(result) if result.success else empty_evidence_html(),
        render_compliance_html(result) if result.success else empty_compliance_html(),
        raw_json,
    )


def load_example(example_name: str):
    payload = EXAMPLE_PAYLOADS.get(example_name, {"ticket": {}, "order_context": {}})
    return payload_to_form_values(payload)


def reset_form():
    return [
        "",
        "",
        "email",
        "",
        "",
        "",
        "",
        "",
        "",
        0,
        "first-party",
        "",
        "",
        "delivered",
        "credit_card",
        False,
        pretty_json({"ticket": {"text": "", "customer_id": "", "channel": "email"}, "order_context": {}}),
        empty_status_html(),
        build_alert_html("Inputs cleared. Load an example or enter a new ticket.", level="warning"),
        empty_decision_html(),
        "",
        empty_evidence_html(),
        empty_compliance_html(),
        pretty_json({}),
    ]


def run_console(
    input_mode: str,
    example_name: str,
    ticket_text: str,
    customer_id: str,
    channel: str,
    order_id: str,
    order_date: str,
    delivery_date: str,
    expected_delivery_date: str,
    item_category: str,
    item_name: str,
    item_price: float,
    fulfillment_type: str,
    seller_name: str,
    shipping_region: str,
    order_status: str,
    payment_method: str,
    is_final_sale: bool,
    raw_json_text: str,
    progress=gr.Progress(track_tqdm=False),
):
    progress(0.05, desc="Collecting inputs")

    if input_mode == "Raw JSON":
        try:
            payload = json.loads(raw_json_text)
        except json.JSONDecodeError as exc:
            return result_to_outputs(UiRunResult.from_error("Invalid JSON", f"Could not parse the raw JSON payload: {exc}"))
    else:
        if input_mode == "Example Cases" and example_name not in EXAMPLE_PAYLOADS:
            return result_to_outputs(UiRunResult.from_error("Example not found", "Select a valid bundled example before running."))

        payload = build_payload_from_form(
            ticket_text,
            customer_id,
            channel,
            order_id,
            order_date,
            delivery_date,
            expected_delivery_date,
            item_category,
            item_name,
            item_price,
            fulfillment_type,
            seller_name,
            shipping_region,
            order_status,
            payment_method,
            is_final_sale,
        )

    def progress_callback(value: float, message: str) -> None:
        progress(value, desc=message)

    return result_to_outputs(run_ticket_resolution_ui(payload, progress_callback=progress_callback))


def build_demo() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="PurpleMerit Ops Console", fill_width=True) as demo:
        gr.HTML(build_header_html())

        with gr.Row(equal_height=False):
            with gr.Column(scale=5):
                with gr.Group(elem_classes=["panel"]):
                    gr.HTML('<h2 class="panel-heading">Ticket Intake</h2>')
                    gr.HTML('<div class="section-note">Load a bundled example, work from the guided form, or paste a raw JSON payload.</div>')

                    input_mode = gr.Radio(choices=["Example Cases", "Guided Form", "Raw JSON"], value="Example Cases", label="Input Mode")
                    example_name = gr.Dropdown(choices=list(EXAMPLE_PAYLOADS.keys()), value=next(iter(EXAMPLE_PAYLOADS.keys()), None), label="Bundled Example")

                    with gr.Accordion("Guided Form", open=True):
                        ticket_text = gr.Textbox(label="Ticket Text", lines=6, placeholder="Paste or edit the customer request.")
                        with gr.Row():
                            customer_id = gr.Textbox(label="Customer ID")
                            channel = gr.Dropdown(label="Channel", choices=["email", "chat", "web_form", "phone"], value="email")
                        with gr.Row():
                            order_id = gr.Textbox(label="Order ID")
                            item_name = gr.Textbox(label="Item Name")
                        with gr.Row():
                            order_date = gr.Textbox(label="Order Date", placeholder="YYYY-MM-DD")
                            delivery_date = gr.Textbox(label="Delivery Date", placeholder="YYYY-MM-DD")
                            expected_delivery_date = gr.Textbox(label="Expected Delivery Date", placeholder="YYYY-MM-DD")
                        with gr.Row():
                            item_category = gr.Textbox(label="Item Category", placeholder="perishable, electronics, unknown...")
                            item_price = gr.Number(label="Item Price", value=0, precision=2)
                        with gr.Row():
                            fulfillment_type = gr.Dropdown(label="Fulfillment Type", choices=["first-party", "marketplace-seller"], value="first-party")
                            seller_name = gr.Textbox(label="Seller Name")
                        with gr.Row():
                            shipping_region = gr.Textbox(label="Shipping Region", placeholder="US-NY")
                            order_status = gr.Dropdown(label="Order Status", choices=["delivered", "shipped", "processing", "cancelled", "returned", "unknown"], value="delivered")
                        with gr.Row():
                            payment_method = gr.Dropdown(label="Payment Method", choices=["credit_card", "paypal", "debit_card", "gift_card", "other"], value="credit_card")
                            is_final_sale = gr.Checkbox(label="Final Sale", value=False)

                    with gr.Accordion("Raw JSON", open=False):
                        raw_json_text = gr.Textbox(label="Ticket Payload JSON", lines=18, elem_classes=["mono"], placeholder='{"ticket": {...}, "order_context": {...}}')

                    with gr.Row():
                        run_button = gr.Button("Run Analysis", elem_classes=["primary-button"], variant="primary")
                        reset_button = gr.Button("Reset", elem_classes=["secondary-button"])

            with gr.Column(scale=7):
                status_html = gr.HTML(empty_status_html())
                alert_html = gr.HTML(build_alert_html("Load an example or enter a ticket to begin.", level="warning"))

                with gr.Tabs():
                    with gr.Tab("Decision"):
                        decision_html = gr.HTML(empty_decision_html())
                    with gr.Tab("Customer Draft"):
                        customer_draft = gr.Textbox(label="Customer Response Draft", lines=18, interactive=False)
                    with gr.Tab("Policy Evidence"):
                        evidence_html = gr.HTML(empty_evidence_html())
                    with gr.Tab("Compliance"):
                        compliance_html = gr.HTML(empty_compliance_html())

                with gr.Accordion("Raw Run Output", open=False):
                    raw_output_text = gr.Textbox(label="Normalized Result JSON", lines=22, interactive=False, elem_classes=["mono"])

        example_outputs = [
            ticket_text,
            customer_id,
            channel,
            order_id,
            order_date,
            delivery_date,
            expected_delivery_date,
            item_category,
            item_name,
            item_price,
            fulfillment_type,
            seller_name,
            shipping_region,
            order_status,
            payment_method,
            is_final_sale,
            raw_json_text,
        ]

        example_name.change(fn=load_example, inputs=[example_name], outputs=example_outputs)

        run_button.click(
            fn=run_console,
            inputs=[
                input_mode,
                example_name,
                ticket_text,
                customer_id,
                channel,
                order_id,
                order_date,
                delivery_date,
                expected_delivery_date,
                item_category,
                item_name,
                item_price,
                fulfillment_type,
                seller_name,
                shipping_region,
                order_status,
                payment_method,
                is_final_sale,
                raw_json_text,
            ],
            outputs=[status_html, alert_html, decision_html, customer_draft, evidence_html, compliance_html, raw_output_text],
        )

        reset_button.click(
            fn=reset_form,
            outputs=[
                ticket_text,
                customer_id,
                channel,
                order_id,
                order_date,
                delivery_date,
                expected_delivery_date,
                item_category,
                item_name,
                item_price,
                fulfillment_type,
                seller_name,
                shipping_region,
                order_status,
                payment_method,
                is_final_sale,
                raw_json_text,
                status_html,
                alert_html,
                decision_html,
                customer_draft,
                evidence_html,
                compliance_html,
                raw_output_text,
            ],
        )

        if EXAMPLE_PAYLOADS:
            demo.load(fn=load_example, inputs=[example_name], outputs=example_outputs)

    return demo


demo = build_demo()
demo.queue()


if __name__ == "__main__":
    demo.launch()
