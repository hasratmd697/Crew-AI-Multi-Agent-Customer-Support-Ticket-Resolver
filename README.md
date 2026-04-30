---
title: PurpleMerit Ops Console
sdk: gradio
app_file: app.py
python_version: 3.10
---

# E-commerce Support Resolution Agent

This project is a multi-agent RAG system for e-commerce customer support. It reads a ticket, analyzes order context, retrieves relevant policy evidence, drafts a response, and runs a compliance pass before returning a final recommendation.

The frontend is now a professional Gradio ops console designed to run locally or on Hugging Face Spaces.

## What This App Does
- Accepts customer ticket input in three modes: bundled examples, guided form, and raw JSON.
- Runs a 5-agent backend pipeline for triage, order analysis, retrieval, drafting, and compliance.
- Displays structured outputs only: issue classification, policy evidence, customer draft, and compliance decision.
- Supports deployment on Hugging Face Spaces with `app.py` as the entrypoint.

## Project Structure
```text
.
├── app.py                 # Gradio frontend for local use and Hugging Face Spaces
├── cli.py                 # Original CLI runner for single-ticket execution
├── ingest.py              # Builds the Chroma vector store from markdown policies
├── requirements.txt       # Python dependencies
├── README.md              # Setup and deployment guide
├── BLOG.md                # Project narrative / portfolio-style writeup
├── SRS.md                 # Software Requirements Specification
├── data/
│   ├── policies/
│   ├── test_tickets/
│   └── vectorstore/
└── src/
    ├── orchestrator.py
    ├── ui_adapter.py
    ├── agents/
    ├── prompts/
    ├── ingestion/
    └── utils/
```

## Local Setup

### 1. Create and activate a virtual environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
python -m pip install -r requirements.txt
```

### 3. Create the environment file
Create a `.env` file in the root folder:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL_NAME=gpt-4o-mini
```

### 4. Build the vector store
Run this once if `data/vectorstore/` is missing or needs to be rebuilt:

```bash
python ingest.py
```

### 5. Launch the app locally
```bash
python app.py
```

### 6. Optional: run the CLI version
```bash
python cli.py --ticket_file data/test_tickets/tc01_exception.json
```

## Step-by-Step: Make It Live on Hugging Face Spaces

Follow these steps in order to see the live app online.

### 1. Make sure the project works locally
Before pushing anything:
- `pip install -r requirements.txt`
- `python ingest.py`
- `python app.py`

If the app opens locally, your Space setup will be much easier.

### 2. Ensure these files are present in your repo
You need these key files at the repo root:
- `app.py`
- `requirements.txt`
- `README.md`
- `data/vectorstore/`

Important:
- Hugging Face Spaces will read the YAML block at the top of `README.md`.
- Your current `README.md` is already configured for `sdk: gradio`.

### 3. Commit your latest code
From the project folder:

```bash
git add .
git commit -m "Add Gradio ops console and deployment docs"
```

### 4. Create a new Hugging Face Space
Go to:
- `https://huggingface.co/spaces`

Then:
1. Click `Create new Space`
2. Choose a Space name
3. Set visibility to `Public` or `Private`
4. Select `Gradio` as the SDK
5. Create the Space

### 5. Upload or push this project to the Space repo
You can do this in either of two ways.

Option A: Use Git
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push hf main
```

Option B: Upload files manually in the Hugging Face web UI
- Upload the full project files
- Keep the folder structure intact
- Make sure `data/vectorstore/` is included

### 6. Add your secret key in Space settings
Open your Space, then:
1. Go to `Settings`
2. Find `Variables and secrets`
3. Add:
   - Key: `OPENAI_API_KEY`
   - Value: your real API key
4. Optionally add:
   - Key: `OPENAI_MODEL_NAME`
   - Value: `gpt-4o-mini`

Do not hardcode the API key in the repo.

### 7. Wait for the build to finish
After push or upload:
- Hugging Face will install dependencies from `requirements.txt`
- It will detect `app.py`
- It will start the Gradio app automatically

If everything is correct, the Space page will show the live app.

### 8. Open the live app
Your app URL will look like:

```text
https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
```

### 9. Test the live app
Once it opens:
1. Load one of the bundled examples
2. Click `Run Analysis`
3. Confirm the tabs populate:
   - `Decision`
   - `Customer Draft`
   - `Policy Evidence`
   - `Compliance`

### 10. If the Space fails to start, check these first
- `OPENAI_API_KEY` is missing in Space settings
- `data/vectorstore/` was not uploaded
- dependency install failed
- the repo was uploaded without the root files
- `requirements.txt` is missing or outdated

## Hugging Face Deployment Checklist
- `README.md` contains the YAML block at the top
- `app.py` exists in the root
- `requirements.txt` includes `gradio`
- `OPENAI_API_KEY` is added in Space secrets
- `data/vectorstore/` exists in the repository
- app works locally before deployment

## Running Evaluation
To run the included test set locally:

```bash
python evaluation/evaluate.py
```

Results are written to `evaluation/results/`.

## Notes
- This app is designed as an operations console, not a chatbot.
- The UI intentionally shows structured outputs instead of chain-of-thought.
- If the Space feels slow on first run, that is normal for dependency loading and model warm-up.

## License
Created for PurpleMerit Assessment.
