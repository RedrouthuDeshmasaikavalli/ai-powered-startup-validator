import os
import re
import json
from typing import AsyncGenerator, Dict, Any, List
from pydantic import BaseModel, Field, model_validator

from google.adk.agents import Agent
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.workflow import Workflow, JoinNode, node, FunctionNode, START, Edge
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.genai import types
from google.adk.apps import App

from app.config import config

# 1. Structured Input/Output schemas

class StartupInput(BaseModel):
    idea: str = Field(description="The core startup idea.")
    target_audience: str = Field(description="The primary target audience or customer persona.")
    problem_statement: str = Field(description="The problem this startup idea aims to solve.")
    industry_market: str = Field(description="The industry or market the startup operates in.")
    location: str = Field(description="The geographic location or target market region.")
    budget: str = Field(description="The available budget or funding context (e.g. '$10k bootstrap', '$500k pre-seed').")

    @model_validator(mode='before')
    @classmethod
    def parse_input(cls, data: Any) -> Any:
        text = None
        if isinstance(data, dict):
            if "parts" in data:
                parts = data["parts"]
                if isinstance(parts, list) and parts:
                    part = parts[0]
                    if isinstance(part, dict) and "text" in part:
                        text = part["text"]
                    elif hasattr(part, "text"):
                        text = part.text
            else:
                return data
        elif hasattr(data, "parts"):
            parts = data.parts
            if parts:
                part = parts[0]
                if hasattr(part, "text"):
                    text = part.text
                elif isinstance(part, dict) and "text" in part:
                    text = part["text"]
        elif isinstance(data, str):
            text = data

        if text:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            
            parsed = {}
            lines = text.split("\n")
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_").replace("-", "_")
                    val = val.strip()
                    parsed[key] = val
            
            fields = ["idea", "target_audience", "problem_statement", "industry_market", "location", "budget"]
            if any(f in parsed for f in fields):
                return parsed

        return data

class ViabilityReport(BaseModel):
    market_analysis: str = Field(description="Summary of the market feasibility and audience demand.")
    competitor_insights: str = Field(description="Analysis of potential competitors and differentiator opportunities.")
    revenue_strategies: str = Field(description="Proposed monetization models and financial feasibility.")
    risk_analysis: str = Field(description="Key risks identified (market, execution, financial).")
    viability_score: int = Field(description="Feasibility score from 0 to 100.")
    recommendation: str = Field(description="Overall recommendation: 'Strong Match', 'Moderate Viability', or 'High Risk'.")

# Setup MCP Toolset for local development
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="uv",
            args=["run", "python", "app/mcp_server.py"],
        ),
    ),
)

# 2. Specialized sub-agents (LlmAgents)
market_analyst = Agent(
    name="market_analyst",
    model=config.model,
    instruction="""You are a seasoned Market Research Analyst.
Your job is to analyze the startup idea's target audience size, market demand, and competitors.
You have access to MCP tools: `get_competitors` and `estimate_market_size`. You MUST call these tools to retrieve real data before writing your analysis.
Structure your report clearly with bullet points, highlighting market trends, target audience demographics, and competition dynamics.""",
    tools=[mcp_toolset],
    description="Analyzes market viability, target audience demand, and competition landscape."
)

financial_advisor = Agent(
    name="financial_advisor",
    model=config.model,
    instruction="""You are a Senior Financial Risk Advisor.
Your job is to analyze the revenue strategies, budget feasibility, and financial/business risks of the startup.
You have access to MCP tools: `get_revenue_benchmarks` and `estimate_market_size`. You MUST call these tools to retrieve real data before writing your analysis.
Evaluate if the budget is realistic for the target market and suggest monetization strategies.""",
    tools=[mcp_toolset],
    description="Evaluates revenue strategies, budget feasibility, and financial/operational risks."
)

# 3. Lead Orchestrator
orchestrator = Agent(
    name="orchestrator",
    model=config.model,
    instruction="""You are the lead Startup Validator Orchestrator.
Your goal is to evaluate the startup idea by coordinating with the market analyst and the financial advisor.

Startup Idea Details:
- Idea: {idea}
- Target Audience: {target_audience}
- Problem Statement: {problem_statement}
- Industry/Market: {industry_market}
- Location: {location}
- Budget: {budget}

Follow these steps:
1. Invoke the market_analyst to get their market analysis.
2. Invoke the financial_advisor to get their financial analysis.
3. Synthesize the findings into a comprehensive initial assessment.
4. Conclude by asking if they have any clarifications or refinements, or if they are ready to proceed with generating the final scorecard.
""",
    tools=[AgentTool(market_analyst), AgentTool(financial_advisor)],
    description="Coordinates startup idea evaluation with market and financial experts."
)

# 4. Security Checkpoint Node
@node
def security_checkpoint(ctx: Context, node_input: StartupInput):
    # Prepare structured audit log
    log_data = {
        "event": "security_checkpoint_evaluation",
        "session_id": ctx.session.id,
        "severity": "INFO",
        "checks": []
    }
    
    text_content = f"{node_input.idea} {node_input.target_audience} {node_input.problem_statement} {node_input.industry_market}".lower()
    
    # 4a. Domain safety check: Banned industries / illegal categories
    banned_keywords = ["gambling", "adult content", "weapons", "drugs", "illegal", "exploit", "hack"]
    for kw in banned_keywords:
        if kw in text_content:
            log_data["severity"] = "CRITICAL"
            log_data["checks"].append(f"banned_category_detected: {kw}")
            print(json.dumps(log_data), flush=True)
            return Event(
                output=f"Security violation: Startup idea matches banned business category '{kw}'.", 
                route="SECURITY_EVENT"
            )
            
    # 4b. Prompt injection check
    injection_keywords = ["ignore previous instructions", "system prompt", "override instructions", "dan mode", "you must now act as"]
    for kw in injection_keywords:
        if kw in text_content:
            log_data["severity"] = "WARNING"
            log_data["checks"].append(f"prompt_injection_detected: {kw}")
            print(json.dumps(log_data), flush=True)
            return Event(
                output="Potential prompt injection attempt detected.", 
                route="SECURITY_EVENT"
            )
            
    # 4c. PII scrubbing
    clean_idea = node_input.idea
    clean_problem = node_input.problem_statement
    
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_regex, clean_idea) or re.search(email_regex, clean_problem):
        clean_idea = re.sub(email_regex, '[EMAIL_SCRUBBED]', clean_idea)
        clean_problem = re.sub(email_regex, '[EMAIL_SCRUBBED]', clean_problem)
        log_data["checks"].append("pii_scrubbed: email")
        
    phone_regex = r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b'
    if re.search(phone_regex, clean_idea) or re.search(phone_regex, clean_problem):
        clean_idea = re.sub(phone_regex, '[PHONE_SCRUBBED]', clean_idea)
        clean_problem = re.sub(phone_regex, '[PHONE_SCRUBBED]', clean_problem)
        log_data["checks"].append("pii_scrubbed: phone")

    if not log_data["checks"]:
        log_data["checks"].append("all_checks_passed")
        
    # Print JSON audit log
    print(json.dumps(log_data), flush=True)
    
    # Save input data to state
    return Event(
        output=node_input,
        route="PROCEED",
        state={
            "idea": clean_idea,
            "target_audience": node_input.target_audience,
            "problem_statement": clean_problem,
            "industry_market": node_input.industry_market,
            "location": node_input.location,
            "budget": node_input.budget,
            "security_passed": True
        }
    )

@node
def security_event(node_input: str) -> str:
    return f"❌ Validation Blocked: {node_input}"

# 5. Human-in-the-loop Gate Node
@node(rerun_on_resume=True)
async def hitl_gate(ctx: Context, node_input: types.Content):
    orchestrator_text = ""
    if node_input and node_input.parts:
        orchestrator_text = "".join(part.text for part in node_input.parts if part.text)
    
    # Check if we have received resume input
    if not ctx.resume_inputs or "user_confirmation" not in ctx.resume_inputs:
        yield Event(
            message=f"Initial Assessment Completed:\n\n{orchestrator_text}",
            state={"initial_assessment": orchestrator_text}
        )
        yield RequestInput(
            interrupt_id="user_confirmation",
            message="Please review the initial assessment above. Provide any clarifications or updates, or type 'approve' to generate the final scorecard."
        )
        return
        
    # User responded
    user_response = ctx.resume_inputs["user_confirmation"]
    yield Event(
        output=user_response,
        state={"clarification_response": user_response},
        route="PROCEED"
    )

# 6. Final Evaluator LlmAgent with output_schema
final_evaluator = Agent(
    name="final_evaluator",
    model=config.model,
    instruction="""You are the Senior Startup Evaluator.
Review the initial assessment:
{initial_assessment}

And the user's feedback/clarifications:
{clarification_response}

Generate the final viability report with structured JSON matching the schema. Calculate a realistic score between 0 and 100 based on the risks and feasibility.""",
    output_schema=ViabilityReport,
    output_key="final_report"
)

# 7. Render Output Function Node
@node
def render_output(node_input: dict) -> str:
    report = f"""# Startup Viability Report

## Viability Score: {node_input.get('viability_score')}/100 ({node_input.get('recommendation')})

### Market Analysis
{node_input.get('market_analysis')}

### Competitor Insights
{node_input.get('competitor_insights')}

### Revenue Strategies
{node_input.get('revenue_strategies')}

### Risk Analysis
{node_input.get('risk_analysis')}
"""
    return report

# 8. Define Workflow Graph
root_agent = Workflow(
    name="startup_idea_validator_workflow",
    input_schema=StartupInput,
    edges=[
        Edge(from_node=START, to_node=security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=security_event, route="SECURITY_EVENT"),
        Edge(from_node=security_checkpoint, to_node=orchestrator, route="PROCEED"),
        Edge(from_node=orchestrator, to_node=hitl_gate),
        Edge(from_node=hitl_gate, to_node=final_evaluator, route="PROCEED"),
        Edge(from_node=final_evaluator, to_node=render_output)
    ],
    description="Evaluates startup business feasibility using a multi-agent system."
)

app = App(
    root_agent=root_agent,
    name="app",
)