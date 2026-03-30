import os
import sys
from pathlib import Path

# Add project root to path so `src` module is discoverable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from pathlib import Path
from src.orchestrator import run_ticket_resolution

def run_evaluation():
    test_dir = Path("data/test_tickets")
    results_dir = Path("evaluation/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = sorted(list(test_dir.glob("*.json")))
    
    print(f"Found {len(test_files)} test cases. Starting evaluation...")
    
    for file_path in test_files:
        print(f"\n{'='*50}\nEvaluating: {file_path.name}\n{'='*50}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        ticket_text = json.dumps(data.get("ticket", {}))
        order_context = json.dumps(data.get("order_context", {}))
        
        start_time = time.time()
        
        try:
            result = run_ticket_resolution(ticket_text, order_context)
            raw_output = str(result.raw if hasattr(result, 'raw') else result)
        except Exception as e:
            raw_output = f'{{"error": "{str(e)}" }}'
            print(f"Error running agent: {e}")
            
        duration = time.time() - start_time
        
        # Save output
        output_data = {
            "test_case": file_path.name,
            "duration_seconds": round(duration, 2),
            "input": data,
            "raw_agent_output": raw_output
        }
        
        result_file = results_dir / f"result_{file_path.name}"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
            
        print(f"\nResult saved to {result_file}")
        print(f"Agent Output snippet:\n{raw_output[:300]}...\n")

if __name__ == "__main__":
    run_evaluation()
