import sys
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Startup Idea Validator MCP Server")

@mcp.tool()
def get_competitors(industry: str, idea: str) -> dict:
    """Retrieves standard competitors and market differentiators for a given industry and startup idea.
    
    Args:
        industry: The startup vertical or industry name (e.g. SaaS, E-commerce, Edtech, Fintech, Healthcare).
        idea: A short description of the startup idea.
    """
    ind_lower = industry.lower()
    if "fintech" in ind_lower or "finance" in ind_lower or "payment" in ind_lower:
        return {
            "competitors": ["Stripe", "Plaid", "Brex", "Revolut", "Wise"],
            "market_share_context": "Stripe leads online payments; Brex dominates corporate finance; Plaid leads open banking APIs.",
            "differentiator_opportunities": "Target specialized regional compliance, micro-lending, or AI-driven fraud detection."
        }
    elif "health" in ind_lower or "medical" in ind_lower or "clinical" in ind_lower or "care" in ind_lower:
        return {
            "competitors": ["Zocdoc", "Oscar Health", "Teladoc", "Ro", "Veeva Systems"],
            "market_share_context": "Teladoc leads telehealth; Oscar dominates consumer health plans; Zocdoc dominates booking.",
            "differentiator_opportunities": "Focus on niche patient portals, clinical intake automation, or HIPAA-compliant SaaS."
        }
    elif "saas" in ind_lower or "software" in ind_lower or "b2b" in ind_lower or "productivity" in ind_lower:
        return {
            "competitors": ["Salesforce", "HubSpot", "ClickUp", "Notion", "Slack"],
            "market_share_context": "HubSpot/Salesforce lead sales CRM; Notion/ClickUp dominate productivity and document storage.",
            "differentiator_opportunities": "Create hyper-targeted integrations, local LLM tooling, or single-feature workflows."
        }
    elif "edu" in ind_lower or "school" in ind_lower or "learn" in ind_lower or "college" in ind_lower:
        return {
            "competitors": ["Duolingo", "Coursera", "Udemy", "Quizlet", "Canvas"],
            "market_share_context": "Duolingo leads language learning; Coursera/Udemy lead professional certifications; Canvas leads LMS.",
            "differentiator_opportunities": "Focus on interactive AI-guided learning, gamified children's education, or school-district portals."
        }
    else:
        return {
            "competitors": ["Incumbent Leader A", "Niche Startup B", "Regional Player C"],
            "market_share_context": "Top players control 55% of market volume; long-tail startups occupy the rest.",
            "differentiator_opportunities": "Tailor to local localized regulations, AI-driven hyper-personalization, or lower price point tiers."
        }

@mcp.tool()
def estimate_market_size(industry: str, target_audience: str, location: str) -> dict:
    """Estimates the addressable market size (TAM, SAM, SOM) for a given industry, audience, and location.
    
    Args:
        industry: The vertical or industry name.
        target_audience: The targeted customer demographics or profile.
        location: The primary target market region or location.
    """
    # Deterministic simulation based on lengths of inputs
    base_factor = (len(industry) + len(target_audience) + len(location)) * 3_500_000
    tam_val = base_factor * 10
    sam_val = int(tam_val * 0.12)
    som_val = int(sam_val * 0.05)
    
    return {
        "tam": f"${tam_val:,}",
        "sam": f"${sam_val:,}",
        "som": f"${som_val:,}",
        "metrics_description": f"TAM: Total global or national spend in '{industry}'. SAM: Addressable portion matching '{target_audience}' in '{location}'. SOM: Feasible capture volume in years 1-3."
    }

@mcp.tool()
def get_revenue_benchmarks(industry: str) -> dict:
    """Retrieves standard pricing structures, average CAC/LTV, and gross margins for an industry.
    
    Args:
        industry: The vertical or industry name.
    """
    ind_lower = industry.lower()
    if "fintech" in ind_lower or "finance" in ind_lower or "payment" in ind_lower:
        return {
            "pricing_model": "Percentage transaction fee (0.5%-2.9%) + monthly SaaS subscription.",
            "gross_margin": "65% - 75%",
            "cac_benchmark": "High ($150 - $400 for consumer; $2,000+ for enterprise)",
            "ltv_to_cac_ratio_target": "3.5x - 4.5x"
        }
    elif "saas" in ind_lower or "software" in ind_lower or "b2b" in ind_lower:
        return {
            "pricing_model": "Tiered monthly subscription per seat or per volume unit (freemium/upsell).",
            "gross_margin": "75% - 85%",
            "cac_benchmark": "Medium ($100 - $300)",
            "ltv_to_cac_ratio_target": "3.0x+"
        }
    elif "edu" in ind_lower or "learn" in ind_lower:
        return {
            "pricing_model": "Monthly consumer subscription or annual per-student licensing fee.",
            "gross_margin": "60% - 75%",
            "cac_benchmark": "Low-to-Medium ($30 - $80 consumer)",
            "ltv_to_cac_ratio_target": "3.0x - 3.5x"
        }
    else:
        return {
            "pricing_model": "Direct transaction sales, marketplace take rate, or dynamic subscription.",
            "gross_margin": "55% - 70%",
            "cac_benchmark": "Variable ($50 - $150)",
            "ltv_to_cac_ratio_target": "3.0x"
        }

if __name__ == '__main__':
    mcp.run()
