import argparse
import json
import sys

from dotenv import load_dotenv

from src.orchestrator import run_ticket_resolution
from src.utils.pii_redactor import PIIRedactor


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E-commerce Support Resolution Agent on a ticket.")
    parser.add_argument("--ticket_file", type=str, help="Path to JSON file containing ticket and order context", required=True)
    args = parser.parse_args()

    try:
        with open(args.ticket_file, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except Exception as exc:
        print(f"Error reading ticket file: {exc}")
        sys.exit(1)

    ticket_text = json.dumps(data.get("ticket", {}), ensure_ascii=False)
    order_context = json.dumps(data.get("order_context", {}), ensure_ascii=False)

    print("====================================")
    print("STARTING SUPPORT RESOLUTION RUN")
    print("====================================")
    print(f"Ticket: {ticket_text[:100]}...")

    safe_ticket_text = PIIRedactor.redact(ticket_text)

    try:
        result = run_ticket_resolution(safe_ticket_text, order_context)
        raw_output = str(result.raw if hasattr(result, "raw") else result)
    except Exception as exc:
        print(f"CRITICAL ERROR in Agent execution: {exc}")
        sys.exit(1)

    print("\n====================================")
    print("FINAL OUTPUT (FROM COMPLIANCE AGENT)")
    print("====================================")
    print(raw_output)

    print("\n====================================")
    print("RUN COMPLETE")
    print("====================================")


if __name__ == "__main__":
    main()
