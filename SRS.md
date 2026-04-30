# Software Requirements Specification

## 1. Introduction

### 1.1 Purpose
This document defines the software requirements for the PurpleMerit E-commerce Support Resolution Agent and its Gradio-based frontend deployed locally or on Hugging Face Spaces.

### 1.2 Scope
The system assists with e-commerce support-ticket handling by analyzing customer ticket text and order context, retrieving policy evidence, drafting a resolution, and performing a compliance review before presenting structured results to the user.

### 1.3 Intended Audience
- project evaluators
- software engineers
- AI engineers
- product reviewers
- technical recruiters

## 2. Overall Description

### 2.1 Product Perspective
The product is a Python-based AI application composed of:
- a multi-agent backend using CrewAI
- a Chroma vector store for policy retrieval
- a Gradio frontend for interaction and visualization
- Hugging Face Spaces support for public deployment

### 2.2 Product Functions
- ingest policy markdown files into a vector store
- accept ticket and order-context input
- classify ticket type and sub-type
- analyze structured order constraints
- retrieve top policy excerpts
- draft a customer resolution
- run a compliance and safety check
- display structured output in a frontend console

### 2.3 User Classes
- evaluator using bundled examples
- technical reviewer using raw JSON input
- operator entering a case manually through the guided form

### 2.4 Operating Environment
- Python 3.10+
- local Windows development environment
- Hugging Face Spaces runtime with Gradio
- internet access for LLM API calls

### 2.5 Constraints
- requires a valid `OPENAI_API_KEY`
- depends on existing vector store or prior ingestion
- frontend must use `app.py` as Space entrypoint
- UI should not expose chain-of-thought

## 3. Functional Requirements

### FR-1 Input Modes
The system shall support:
- bundled example tickets
- guided form input
- raw JSON input

### FR-2 Ticket Validation
The system shall validate that:
- `ticket` exists
- `order_context` exists
- `ticket.text` is a non-empty string

### FR-3 Triage Processing
The system shall classify the ticket into:
- issue type
- sub-type
- confidence score
- missing fields
- clarifying questions

### FR-4 Order Context Analysis
The system shall analyze order data and return relevant operational or policy flags.

### FR-5 Policy Retrieval
The system shall retrieve relevant policy excerpts from the vector store and present:
- document title
- section
- chunk ID
- excerpt text

### FR-6 Resolution Drafting
The system shall generate:
- decision
- rationale
- customer response draft
- next steps

### FR-7 Compliance Review
The system shall generate:
- pass or fail status
- list of issues
- action result such as approve, rewrite, or escalate

### FR-8 Error Handling
The system shall provide user-visible error states for:
- invalid JSON
- invalid input structure
- missing API key
- missing vector store
- runtime backend exceptions

### FR-9 Frontend Output
The frontend shall display results in separate sections for:
- decision
- customer draft
- policy evidence
- compliance
- raw normalized output

### FR-10 Local and Hosted Execution
The system shall support:
- local frontend launch via `python app.py`
- CLI execution via `python cli.py --ticket_file ...`
- hosted deployment via Hugging Face Spaces

## 4. Non-Functional Requirements

### NFR-1 Usability
The UI shall be professional, restrained, and easy to scan.

### NFR-2 Visual Design
The UI shall:
- avoid gradients
- avoid excessive emoji use
- use muted colors and strong typography
- maintain a desktop-first layout that collapses for smaller screens

### NFR-3 Reliability
The system shall fail gracefully with informative error messaging instead of crashing the UI.

### NFR-4 Maintainability
The frontend shall use a normalized backend result model so UI components are not tightly coupled to raw LLM output text.

### NFR-5 Security
The system shall not hardcode API keys in source files and shall use environment variables or Hugging Face secrets.

### NFR-6 Explainability
The system shall show evidence and compliance status but shall not expose chain-of-thought.

## 5. External Interface Requirements

### 5.1 User Interface
The user interface shall include:
- input mode selector
- example selector
- guided ticket form
- raw JSON editor
- run button
- reset button
- result tabs

### 5.2 Software Interfaces
- OpenAI-compatible LLM API
- ChromaDB vector store
- CrewAI orchestration
- Gradio frontend runtime

### 5.3 Data Interfaces
Input data format:
- JSON with `ticket` and `order_context`

Output data format:
- normalized structured result object for the UI

## 6. Assumptions and Dependencies
- policy markdown files exist in `data/policies/`
- vector store exists in `data/vectorstore/` or can be generated
- the deployment environment can install Python dependencies from `requirements.txt`
- the LLM API remains reachable from the deployment environment

## 7. Acceptance Criteria
- the app launches locally with `python app.py`
- example tickets can be loaded and run
- the results render in all four main tabs
- invalid input shows clear inline errors
- the app can be deployed to Hugging Face Spaces
- the Space runs with `app.py` as the main entrypoint

## 8. Future Enhancements
- richer analytics dashboard
- stronger stage-by-stage structured parsing
- cached demo mode without live API calls
- downloadable run reports
