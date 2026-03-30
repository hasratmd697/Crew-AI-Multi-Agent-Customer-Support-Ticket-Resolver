# E-commerce Support Resolution Agent

This repository contains a multi-agent RAG system built with CrewAI designed to resolve e-commerce customer support tickets accurately and safely. The system uses a strict "evidence-only" approach to ensure zero hallucinations and enforces citation-backed claims for all policy decisions.

## Architecture & Agents
The project relies on a sequential process of 5 CrewAI agents:
1. **Triage Agent:** Classifies the issue and identifies missing info.
2. **Order Context Interpreter:** Parses order data (flags perishables, final sale, etc.).
3. **Policy Retriever Agent:** Uses a custom `ChromaDB` tool to fetch the 5 most relevant policy excerpts.
4. **Resolution Writer Agent:** Drafts the response using ONLY the fetched policy excerpts.
5. **Compliance & Safety Agent:** Audits the draft for hallucinated claims, missing citations, and tone. It can force a rewrite or escalation.

## Setup Instructions

### 1. Requirements
- Python 3.10+
- OpenAI API Key

### 2. Installation
```bash
python -m venv venv
.\\venv\\Scripts\\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-4o-mini  # Or gpt-4o for better performance
```

## Running the Project

### Step 1: Data Ingestion
First, build the vector database from the synthetic markdown policies:
```bash
python ingest.py
```
*This reads the 14 markdown files in `data/policies/`, chunks them (500 tokens, 75 overlap), embeds them using `all-MiniLM-L6-v2`, and stores them in ChromaDB.*

### Step 2: Running a Single Ticket
Use the CLI application to run a specific test case:
```bash
python app.py --ticket_file data/test_tickets/tc01_exception.json
```

### Step 3: Run Full Evaluation
To evaluate the system against all provided test tickets:
```bash
python evaluation/evaluate.py
```
*Results will be saved in `evaluation/results/`.*

## License
Created for PurpleMerit Assessment.
