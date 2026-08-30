"""
LLM integration service (Phase 8).

Provides two capabilities:
1. AI Summary generation — takes structured extraction + analysis results
   and generates a beginner-friendly plain-English summary.
2. RAG Chat — takes a user question + retrieved evidence chunks and
   generates an evidence-grounded answer.

Primary provider: Google Gemini (via google-generativeai).
Fallback: deterministic template-based summary when no API key is configured.

The LLM receives structured, evidence-backed information — it explains,
it doesn't invent. If the GEMINI_API_KEY is not configured, the system
still works using the template fallback.
"""

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Lazy-loaded client
_gemini_model = None


def _get_gemini_model():
    """Lazily initialize the Gemini model."""
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model

    api_key = settings.gemini_api_key
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        return _gemini_model
    except ImportError:
        logger.warning("google-generativeai not installed. LLM features disabled.")
        return None
    except Exception as exc:
        logger.warning(f"Could not initialize Gemini model: {exc}")
        return None


def _is_llm_available() -> bool:
    """Check if an LLM is available."""
    return _get_gemini_model() is not None


def _call_gemini(prompt: str, max_tokens: int = 1024) -> str | None:
    """Call Gemini API and return the text response, or None on failure."""
    model = _get_gemini_model()
    if model is None:
        return None
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.3,
            },
        )
        if response and response.text:
            return response.text.strip()
        return None
    except Exception as exc:
        logger.warning(f"Gemini API call failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# AI Summary
# ---------------------------------------------------------------------------

def _build_summary_prompt(analysis_data: dict) -> str:
    """Build a prompt for generating a beginner-friendly IPO summary."""
    company = analysis_data.get("company_name", "This company")
    overview = analysis_data.get("overview", "")
    fin_health = analysis_data.get("financial_health", {})
    metrics = analysis_data.get("financial_metrics", [])
    risk = analysis_data.get("risk_analysis", {})
    promoter = analysis_data.get("promoter_analysis", {})
    strengths = analysis_data.get("top_strengths", [])
    concerns = analysis_data.get("top_risks", [])

    prompt = f"""You are a financial educator explaining an IPO to a first-time retail investor in India. Write a clear, honest, balanced summary in simple English.

COMPANY: {company}
OVERVIEW: {overview}

FINANCIAL HEALTH: {fin_health.get('status', 'Unknown')} (Score: {fin_health.get('score', 'N/A')}/100)
Reasons: {'; '.join(fin_health.get('reasons', []))}

KEY METRICS:
"""
    for m in metrics:
        prompt += f"- {m.get('label', '')}: {m.get('value', 'N/A')} — {m.get('meaning', '')}\n"

    prompt += f"""
RISK LEVEL: {risk.get('overall_risk_level', 'Unknown')}
RISKS:
"""
    for r in risk.get("risks", []):
        prompt += f"- {r.get('category', '')}: {r.get('severity', 'Unknown')} — {r.get('reason', '')}\n"

    prompt += f"""
PROMOTER QUALITY: {promoter.get('label', 'Unknown')} ({promoter.get('stars', 0)}/5 stars)
PROMOTER POINTS: {'; '.join(promoter.get('points', []))}

STRENGTHS: {'; '.join(strengths)}
CONCERNS: {'; '.join(concerns)}

INSTRUCTIONS:
1. Write 3-5 sentences in plain English, as if explaining to a friend who knows nothing about finance.
2. Start with what the company does.
3. Mention the financial situation (good, moderate, or concerning).
4. Mention the biggest risk(s).
5. End with a balanced view.
6. Do NOT give investment advice. Do NOT say "buy", "apply", "guaranteed", "risk-free", or "listing gain".
7. Use phrases like "appears to be", "based on the data", "investors should understand".
8. If data is incomplete, say so honestly.
9. Keep it under 100 words.
"""
    return prompt


def _generate_template_summary(analysis_data: dict) -> str:
    """Deterministic template-based fallback when no LLM is available."""
    company = analysis_data.get("company_name", "This company")
    fin_health = analysis_data.get("financial_health", {})
    health_status = fin_health.get("status", "unavailable")
    score = fin_health.get("score")
    strengths = analysis_data.get("top_strengths", [])
    concerns = analysis_data.get("top_risks", [])
    risk = analysis_data.get("risk_analysis", {})
    risk_level = risk.get("overall_risk_level", "unknown")

    parts = []

    # Company overview
    overview = analysis_data.get("overview")
    if overview:
        parts.append(overview[:200].rstrip('.') + '.')
    else:
        parts.append(f"{company} is the company behind this IPO.")

    # Financial health
    if score is not None:
        if health_status == "Strong":
            parts.append(f"Based on the available financial data, the company appears to be in strong financial health (score: {score}/100).")
        elif health_status == "Moderate":
            parts.append(f"The company's financial position appears moderate (score: {score}/100).")
        else:
            parts.append(f"The financial health appears weak based on available data (score: {score}/100) — this warrants careful review.")
    else:
        parts.append("Financial health could not be fully assessed from the available data.")

    # Strengths
    if strengths:
        parts.append(f"Key strengths include: {strengths[0].lower()}.")

    # Risks
    if concerns:
        parts.append(f"The main concern is that {concerns[0].lower()}.")
    elif risk_level == "High":
        parts.append("The overall risk level appears high — review the risk factors carefully.")

    # Balanced ending
    parts.append("This analysis is based on information extracted from the DRHP and is not a recommendation to invest.")

    return " ".join(parts)


def generate_summary(analysis_data: dict) -> str:
    """Generate an AI summary of the IPO analysis.
    Uses Gemini if available, otherwise falls back to template."""

    # Try LLM first
    if _is_llm_available():
        prompt = _build_summary_prompt(analysis_data)
        result = _call_gemini(prompt, max_tokens=300)
        if result:
            return result

    # Fallback to template
    return _generate_template_summary(analysis_data)


# ---------------------------------------------------------------------------
# RAG Chat
# ---------------------------------------------------------------------------

def _build_chat_prompt(question: str, evidence_chunks: list[dict]) -> str:
    """Build a prompt for RAG-based question answering."""
    context = ""
    for i, chunk in enumerate(evidence_chunks, 1):
        page_info = f"(Pages {chunk.get('page_start', '?')}–{chunk.get('page_end', '?')}"
        section = chunk.get("section")
        if section:
            page_info += f", Section: {section}"
        page_info += ")"

        text = chunk.get("text", "")[:800]  # limit context size
        context += f"\n--- Evidence {i} {page_info} ---\n{text}\n"

    prompt = f"""You are an IPO research assistant answering questions about a DRHP (Draft Red Herring Prospectus) document for a retail investor in India who has little financial knowledge.

EVIDENCE FROM THE DOCUMENT:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer ONLY based on the evidence provided above. Do NOT invent information.
2. If the evidence doesn't contain enough information to answer, say: "I couldn't find enough information in the uploaded DRHP to answer that reliably."
3. Use simple, plain English.
4. Cite page numbers when relevant (e.g., "According to pages 45–47...").
5. Do NOT give investment advice. Do NOT say "buy", "apply", or "guaranteed".
6. Keep your answer concise (3-5 sentences).
7. If explaining a financial term, add a simple explanation in parentheses.
"""
    return prompt


def generate_chat_response(question: str, evidence_chunks: list[dict]) -> dict:
    """Generate a chat response from evidence chunks.
    Returns {answer: str, sources: list, llm_used: bool}."""

    sources = []
    for chunk in evidence_chunks:
        source = {
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "section": chunk.get("section"),
        }
        if source not in sources:
            sources.append(source)

    # Try LLM
    if _is_llm_available() and evidence_chunks:
        prompt = _build_chat_prompt(question, evidence_chunks)
        answer = _call_gemini(prompt, max_tokens=500)
        if answer:
            return {"answer": answer, "sources": sources[:5], "llm_used": True}

    # Fallback: return the most relevant evidence chunk as the answer
    if evidence_chunks:
        top = evidence_chunks[0]
        text = top.get("text", "")
        # Extract the most relevant sentences
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        answer_text = '. '.join(sentences[:3]) + '.' if sentences else text[:500]

        page_ref = f"(Source: pages {top.get('page_start', '?')}–{top.get('page_end', '?')}"
        section = top.get("section")
        if section:
            page_ref += f", {section}"
        page_ref += ")"

        return {
            "answer": f"{answer_text}\n\n{page_ref}\n\n_Note: AI chat requires a Gemini API key to be configured. This response shows the most relevant document excerpt._",
            "sources": sources[:5],
            "llm_used": False,
        }

    return {
        "answer": "I couldn't find enough information in the uploaded DRHP to answer that reliably.",
        "sources": [],
        "llm_used": False,
    }
