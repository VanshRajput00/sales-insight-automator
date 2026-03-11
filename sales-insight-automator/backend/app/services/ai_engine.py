# Lead Engineer Note: ai_engine.py is the ONLY file that knows about Gemini.
# If we ever swap to Groq, OpenAI, or a local model, we change ONE file.
# This is the Adapter pattern — the rest of the app calls `generate_sales_brief()`
# and never cares what's behind it.

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Model Initialization ---
# Lead Engineer Note: We initialize the client once at module load time, not
# inside the function. Re-initializing on every request adds ~200ms latency
# and wastes API handshake overhead.
if _GEMINI_API_KEY:
    genai.configure(api_key=_GEMINI_API_KEY)
    _model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.4,       # Low temp = consistent, professional tone
            max_output_tokens=1024, # Enough for detailed executive brief
        ),
    )
else:
    _model = None


SYSTEM_PROMPT = """You are a Senior Sales Analyst presenting to a CEO. 
Your writing is precise, confident, and data-driven. You never use filler phrases 
like "It's worth noting" or "Certainly!". You speak in outcomes, not observations."""

ANALYSIS_PROMPT_TEMPLATE = """
{system}

Analyze the following Q1 2026 sales figures and produce a 3-bullet executive brief.

Rules:
- Each bullet must start with a bold metric or key finding
- Bullet 1: Overall revenue performance vs implied expectations
- Bullet 2: Top-performing segment and what it signals
- Bullet 3: A risk, gap, or strategic recommendation based on the data
- Tone: Board-room ready. No fluff. Max 40 words per bullet.

--- DATA ---
{stats}
--- END DATA ---

Executive Brief:
"""


def generate_sales_brief(stats_summary: str) -> str:
    """
    Calls Gemini to generate a 3-bullet executive brief from sales stats.

    Args:
        stats_summary: Human-readable stats string from processor.py

    Returns:
        AI-generated executive brief as a string.

    Raises:
        RuntimeError: If the API key is missing or the Gemini call fails.
    """
    if not _model:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file and restart the server."
        )

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        system=SYSTEM_PROMPT,
        stats=stats_summary,
    )

    try:
        response = _model.generate_content(prompt)

        # Lead Engineer Note: Gemini can return empty content if the prompt
        # triggers a safety filter. We surface this as a clear error rather
        # than returning an empty string that would confuse the frontend.
        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response. "
                "The content may have been blocked by a safety filter."
            )

        return response.text.strip()

    except Exception as e:
        # Re-raise with context so the router can return a clean 502
        raise RuntimeError(f"Gemini API call failed: {str(e)}")
