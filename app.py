import json
import argparse
import sys
from dotenv import load_dotenv

# Ensure env vars are loaded
load_dotenv()

from src.orchestrator import run_ticket_resolution
from src.utils.citation_checker import CitationChecker
from src.utils.pii_redactor import PIIRedactor

def main():
    parser = argparse.ArgumentParser(description="Run E-commerce Support Resolution Agent on a ticket.")
    parser.add_argument("--ticket_file", type=str, help="Path to JSON file containing ticket and order context", required=True)
    args = parser.parse_args()

    try:
        with open(args.ticket_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading ticket file: {e}")
        sys.exit(1)
        
    ticket_text = json.dumps(data.get("ticket", {}))
    order_context = json.dumps(data.get("order_context", {}))
    
    print("====================================")
    print("🎫 STARTING SUPPORT RESOLUTION RUN")
    print("====================================")
    print(f"Ticket: {ticket_text[:100]}...")
    
    # PII Redaction on input (optional, depending on strictness)
    safe_ticket_text = PIIRedactor.redact(ticket_text)
    
    # Run the Crew
    try:
        result = run_ticket_resolution(safe_ticket_text, order_context)
        raw_output = str(result.raw if hasattr(result, 'raw') else result)
    except Exception as e:
        print(f"CRITICAL ERROR in Agent execution: {e}")
        sys.exit(1)
        
    print("\n====================================")
    print("📄 FINAL OUTPUT (FROM COMPLIANCE AGENT)")
    print("====================================")
    print(raw_output)
    
    # We could also programmatically run the CitationChecker here as a hard-stop
    # But the Compliance Agent essentially acts as this check contextually.
    
    print("\n====================================")
    print("✅ RUN COMPLETE")
    print("====================================")

if __name__ == "__main__":
    main()
