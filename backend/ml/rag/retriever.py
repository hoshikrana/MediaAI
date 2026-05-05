import re
from backend.ml.rag.vectorstore import vector_store

class MedicalRAG:
    """Retrieval-Augmented Generation for medical Q&A."""
    MAX_CONTEXT_TOKENS = 800
    MAX_HISTORY_TURNS = 6
    SAFETY_DISCLAIMER = "\n\n*Note: This is AI-generated information for educational purposes only. Please consult a licensed physician for medical advice.*"
    DRUG_DOSAGE_PATTERNS = [r"\b\d+\s*mg\b", r"how much.*take", r"dosage", r"dose of"]

    @staticmethod
    def retrieve(query: str, session_result: dict | None, n_results: int = 5) -> list[dict]:
        enriched_query = query
        if session_result:
            primary_dx = session_result.get("nlp", {}).get("primary_diagnosis", "")
            symptoms = session_result.get("nlp", {}).get("entities", {}).get("symptoms", [])
            if primary_dx:
                enriched_query = f"{query} {primary_dx} {' '.join(symptoms[:3])}"
        return vector_store.search(enriched_query, n_results=n_results)

    @staticmethod
    def build_prompt(query: str, retrieved_chunks: list[dict], chat_history: list[dict], session_result: dict | None) -> str:
        parts = []
        if session_result:
            vision, nlp = session_result.get("vision", {}), session_result.get("nlp", {})
            if vision or nlp:
                parts.append("Patient analysis context:")
                if vision:
                    parts.append(f"- Imaging: {vision.get('risk_level', 'unknown')} risk (anomaly score: {vision.get('anomaly_score', 'N/A')}/100)")
                if nlp:
                    parts.append(f"- Primary impression: {nlp.get('primary_diagnosis', 'unknown')}")
                parts.append("")

        if retrieved_chunks:
            parts.append("Relevant medical information:")
            for chunk in retrieved_chunks[:3]:
                parts.append(f"- {chunk['text'][:200]}...")
            parts.append("")

        recent_history = chat_history[-MedicalRAG.MAX_HISTORY_TURNS:]
        for msg in recent_history:
            role = "Patient" if msg["role"] == "user" else "Assistant"
            parts.append(f"{role}: {msg['content'][:100]}")

        parts.append(f"Patient: {query}\nAssistant:")
        return "\n".join(parts)

    @staticmethod
    def is_safe_query(query: str) -> tuple[bool, str | None]:
        for pattern in MedicalRAG.DRUG_DOSAGE_PATTERNS:
            if re.search(pattern, query.lower()):
                return False, "Please consult a physician for specific dosage information."
        return True, None
