"""Gemini API integration for MedSight AI chat.
Provides high-quality medical Q&A with session-aware context."""

import os
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)

_client = None
_model = None


def _get_model():
    """Lazy-initialize the Gemini model."""
    global _client, _model
    if _model is not None:
        return _model
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — Gemini chat unavailable")
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPT,
            generation_config={
                "temperature": 0.4,
                "top_p": 0.85,
                "max_output_tokens": 600,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        logger.info("✅ Gemini model initialized (gemini-2.0-flash)")
        return _model
    except Exception as e:
        logger.error(f"Gemini init failed: {e}")
        return None


_SYSTEM_PROMPT = """You are MedSight AI Assistant — a clinical decision-support chatbot embedded in a pulmonary anomaly detection platform. 

Your capabilities:
• You have access to patient scan analysis results including anomaly scores, risk levels, and AI-generated diagnoses.
• You explain medical imaging findings in clear, empathetic language.
• You reference specific values from the analysis (anomaly scores, confidence levels, differential diagnoses).
• You provide evidence-based medical information about pulmonary conditions.

Communication guidelines:
• Use markdown formatting: **bold** for emphasis, bullet points for lists.
• Be concise but thorough — aim for 150-300 words per response.
• Always reference the patient's specific results when relevant.
• Use clinical terminology but explain it in plain language.
• Structure complex answers with clear sections.
• Include relevant follow-up questions the patient might want to ask.

Safety rules:
• NEVER provide specific drug dosages or prescribe medications.
• ALWAYS remind users this is AI-assisted analysis and to consult their physician.
• If asked about treatment, provide general information and emphasize professional consultation.
• Do not diagnose — present findings as "the AI analysis suggests" or "the scan indicates".

End every response with a brief safety note: 
⚠️ *This is AI-generated educational content. Always consult a licensed physician for medical decisions.*"""


def _build_context(session_result: dict | None, query: str, history: list[dict], chunks: list[dict] | None = None) -> str:
    """Build a rich prompt with all available patient context."""
    parts = []

    if session_result and isinstance(session_result, dict):
        vision = session_result.get("vision") or {}
        nlp_data = session_result.get("nlp") or {}
        fusion = session_result.get("fusion") or {}
        
        parts.append("## Current Patient Analysis Results")
        if vision:
            parts.append(f"- **Risk Level:** {vision.get('risk_level', 'UNKNOWN')}")
            parts.append(f"- **Anomaly Score:** {vision.get('anomaly_score', 'N/A')}/100")
            parts.append(f"- **Confidence:** {vision.get('confidence', 'N/A')}")
            regions = vision.get("top_regions") or []
            if regions:
                parts.append(f"- **Anomaly Regions Detected:** {len(regions)} region(s) flagged")
        
        if nlp_data:
            parts.append(f"- **Primary Diagnosis:** {nlp_data.get('primary_diagnosis', 'N/A')}")
            parts.append(f"- **Diagnosis Confidence:** {nlp_data.get('diagnosis_confidence', 0) * 100:.0f}%")
            diff = nlp_data.get("differential") or []
            if diff:
                diff_strs = [f"{d.get('disease', '?')} ({d.get('confidence', 0) * 100:.0f}%)" for d in diff[:3]]
                parts.append(f"- **Differential Diagnoses:** {', '.join(diff_strs)}")
            entities = nlp_data.get("entities") or {}
            if isinstance(entities, dict):
                symptoms = entities.get("symptoms") or []
                if symptoms:
                    parts.append(f"- **Reported Symptoms:** {', '.join(symptoms[:5])}")
        
        if fusion:
            parts.append(f"- **Image-Text Alignment:** {fusion.get('alignment', 'N/A')}")
            parts.append(f"- **Similarity Score:** {fusion.get('image_text_similarity', 'N/A')}")
        
        parts.append("")

    if chunks:
        parts.append("## Relevant Medical Literature (from knowledge base)")
        for i, chunk in enumerate(chunks[:3], 1):
            text = chunk.get("text", "")[:250]
            parts.append(f"{i}. {text}")
        parts.append("")

    # Add conversation history
    if history:
        parts.append("## Recent Conversation")
        for msg in history[-6:]:
            role = "Patient" if msg["role"] == "user" else "Assistant"
            parts.append(f"**{role}:** {msg['content'][:200]}")
        parts.append("")

    parts.append(f"## Current Patient Question\n{query}")
    return "\n".join(parts)


async def generate_gemini_stream(
    query: str,
    session_result: dict | None,
    history: list[dict],
    chunks: list[dict] | None = None
) -> AsyncIterator[str] | None:
    """Stream tokens from Gemini. Returns None if unavailable."""
    model = _get_model()
    if model is None:
        return None
    
    context = _build_context(session_result, query, history, chunks)
    
    try:
        response = model.generate_content(context, stream=True)
        async def _stream():
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        return _stream()
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        return None


def is_available() -> bool:
    """Check if Gemini is configured and ready."""
    return bool(os.getenv("GEMINI_API_KEY", ""))
