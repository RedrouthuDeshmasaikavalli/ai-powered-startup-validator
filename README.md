# Startup Idea Validator Agent

A simulated multi-agent system built with the Google Agent Development Kit (ADK 2.0) that validates startup ideas by conducting feasibility, competitive, financial, and risk analyses.

## Prerequisites

- **Python 3.11+** (Python 3.11–3.13 supported)
- **uv** (recommended Python package manager)
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/apikey)

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd startup-idea-validator
   ```

2. Create and configure your environment file:
   ```bash
   cp .env.example .env
   # Add your GOOGLE_API_KEY in the .env file
   ```

3. Install project dependencies:
   ```bash
   make install
   ```

4. Launch the local developer playground:
   ```bash
   make playground
   ```
   This will start the local server and open the ADK playground UI at [http://localhost:18081](http://localhost:18081).

---

## Solution Architecture

```mermaid
graph TD
    START --> SecCheck[Security Checkpoint]
    SecCheck -- SECURITY_EVENT --> SecEvent[Security Event Node]
    SecCheck -- PROCEED --> Orch[Orchestrator Agent]
    Orch --> Analyst[Market Analyst Agent]
    Orch --> Advisor[Financial Advisor Agent]
    Analyst --> MCPServer[MCP Server Tools]
    Advisor --> MCPServer
    Orch --> HITL[Human-in-the-Loop Gate]
    HITL -- Needs Resume --> User[User Input: Confirm/Refine]
    User --> HITL
    HITL -- PROCEED --> FinalEval[Final Evaluator Agent]
    FinalEval --> Render[Render Output Node]
```

The system contains:
- **`security_checkpoint`**: A workflow function node filtering prompt injection, sanitizing PII, and checking for banned startup industries (e.g. weapons, drugs).
- **`orchestrator`**: A lead `LlmAgent` coordinating with two domain experts.
- **`market_analyst`**: A specialized sub-agent that pulls data from the local MCP server to examine TAM/SAM/SOM and key competitors.
- **`financial_advisor`**: A specialized sub-agent that checks average CAC, pricing, and profit margins via MCP.
- **`hitl_gate`**: An interactive checkpoint requiring the user to approve initial findings or input refinements.
- **`final_evaluator`**: An agent that digests findings and user corrections to return a structured feasibility scorecard.

---

## Assets

### Workflow Diagram
![Workflow Diagram](assets/architecture_diagram.png)

### Cover Page Banner
![Cover Page Banner](assets/cover_page_banner.png)

---

## How to Run

- **Interactive Playground UI:**
  ```bash
  make playground
  ```
  Launches the interactive web-based playground at [http://localhost:18081](http://localhost:18081).

- **API Web Server Mode:**
  ```bash
  make run
  ```
  Launches the production-ready FastAPI application server at `http://localhost:8080`.

---

## Sample Test Cases

### Test Case 1: Standard Valid Tech Idea
- **Input:**
  ```json
  {
    "idea": "A micro-investment platform for children to learn financial literacy with parental controls.",
    "target_audience": "Parents with kids aged 8-15",
    "problem_statement": "Children lack financial literacy, and traditional banking apps are too complex.",
    "industry_market": "Fintech / Edtech",
    "location": "United States",
    "budget": "$50,000 self-funded"
  }
  ```
- **Expected Flow:**
  - Passes `security_checkpoint` with `INFO` log status.
  - `orchestrator` fetches analysis from sub-agents using MCP tools.
  - Pauses at `hitl_gate` and asks user to confirm.
- **Check in Playground:**
  - The UI will output the initial assessment and show a response box requesting input.
  - Submitting `approve` will resume the workflow and display the final Viability Scorecard (e.g. Score: 85/100, Recommendation: Strong Match).

### Test Case 2: PII Redaction Check
- **Input:**
  ```json
  {
    "idea": "A private consulting service. Reach out to me at admin@mysecretstartup.com or 555-019-2834.",
    "target_audience": "Small businesses",
    "problem_statement": "Need expert business consulting.",
    "industry_market": "Consulting",
    "location": "Global",
    "budget": "$10,000"
  }
  ```
- **Expected Flow:**
  - `security_checkpoint` runs regex checks and detects PII.
  - The email and phone number are replaced with `[EMAIL_SCRUBBED]` and `[PHONE_SCRUBBED]`.
- **Check in Playground/Logs:**
  - Verify that the terminal logs output `{"event": "security_checkpoint_evaluation", "checks": ["pii_scrubbed: email", "pii_scrubbed: phone"]}`.
  - The initial assessment outputted by the orchestrator will only see the scrubbed version of the idea.

### Test Case 3: Security Violation (Banned Category)
- **Input:**
  ```json
  {
    "idea": "An anonymous online catalog for selling illegal drugs and weapons.",
    "target_audience": "Darknet buyers",
    "problem_statement": "Difficulty purchasing weapons safely.",
    "industry_market": "Retail / Black Market",
    "location": "Worldwide",
    "budget": "$10,000"
  }
  ```
- **Expected Flow:**
  - `security_checkpoint` flags the banned keyword `weapons` / `drugs`.
  - Routes immediately to `security_event`.
- **Check in Playground:**
  - The validation halts immediately. The UI outputs `❌ Validation Blocked: Security violation: Startup idea matches banned business category 'weapons'.`

---

## Troubleshooting

1. **`404 Model Not Found` Error:**
   - Make sure your `.env` lists `GEMINI_MODEL=gemini-2.5-flash`. The old `gemini-1.5-*` models are retired and return 404.
2. **`uv sync` fails with hardlink errors (OneDrive/Windows):**
   - In your terminal, run `$env:UV_LINK_MODE="copy"` before running `make install` or `uv sync`. OneDrive does not support NTFS hardlinks.
3. **Changes to `agent.py` or `mcp_server.py` are not picked up (Windows):**
   - On Windows, playground hot-reload is disabled due to event loop locks. Close your server with `CTRL+C`, or execute this in PowerShell to force-kill:
     ```powershell
     Get-Process -Id (Get-NetTCPConnection -LocalPort 18081, 8090 -ErrorAction SilentlyContinue).OwningProcess | Stop-Process -Force
     ```
     Then start a fresh server.

---

## Demo Script

A spoken presentation script is available at [DEMO_SCRIPT.txt](file:///c:/Users/Deshma/OneDrive/Desktop/Project-Idea-Generator/startup-idea-validator/DEMO_SCRIPT.txt) for presenting this project and its architecture diagrams.

---

## Push to GitHub

1. Create a new repo at https://github.com/new
   - Name: startup-idea-validator
   - Visibility: Public or Private
   - Do NOT initialize with README (you already have one)

2. In your terminal, navigate into your project folder:
   ```bash
   cd startup-idea-validator
   git init
   git add .
   git commit -m "Initial commit: startup-idea-validator ADK agent"
   git branch -M main
   git remote add origin https://github.com/<your-username>/startup-idea-validator.git
   git push -u origin main
   ```

3. Verify .gitignore includes:
   ```
   .env          ← your API key — must NEVER be pushed
   .venv/
   __pycache__/
   *.pyc
   .adk/
   ```

⚠ NEVER push `.env` to GitHub. Your API key will be exposed publicly.
