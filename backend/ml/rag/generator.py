import torch
from threading import Thread
from transformers import TextIteratorStreamer

class ReportGenerator:
    @staticmethod
    def generate(vision, nlp, fusion, model, tokenizer) -> str:
        parts = ["Generate a medical radiology report based on these findings:"]
        if vision: parts.append(f"Imaging: {vision.risk_level} risk, anomaly score {vision.anomaly_score}/100")
        if nlp: parts.append(f"Clinical: {nlp.primary_diagnosis}, confidence {nlp.diagnosis_confidence:.0%}")
        if fusion: parts.append(f"Image-text alignment: {fusion.alignment}")
        parts.append("Report:")
        
        prompt = " ".join(parts)
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs, max_new_tokens=300, do_sample=False, num_beams=4,
                early_stopping=True, pad_token_id=tokenizer.eos_token_id, repetition_penalty=1.3
            )
            
        generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return ReportGenerator._format_report(generated, vision, nlp)

    @staticmethod
    def _format_report(raw_text: str, vision, nlp) -> str:
        sections = ["## AI Diagnostic Report\n"]
        if vision:
            risk_emoji = "🔴" if vision.risk_level == "HIGH" else "🟡" if vision.risk_level == "MEDIUM" else "🟢"
            sections.append(f"### Imaging Findings\n{risk_emoji} **Risk Level:** {vision.risk_level}  \n**Anomaly Score:** {vision.anomaly_score}/100\n")
        if nlp:
            sections.append(f"### Clinical Assessment\n**Primary Impression:** {nlp.primary_diagnosis}\n")
        sections.append(f"### AI Analysis\n{raw_text.strip()}\n\n### Recommendation\nPlease consult a licensed physician.")
        return "\n".join(sections)

class ChatGenerator:

    # ── Medical knowledge snippets keyed by condition ──────────
    _CONDITION_INFO = {
        "pleural effusion": {
            "description": "Pleural effusion is the buildup of excess fluid between the layers of the pleura outside the lungs.",
            "causes": "Common causes include congestive heart failure, pneumonia, liver cirrhosis, pulmonary embolism, kidney disease, and malignancy.",
            "symptoms": "Typical symptoms include shortness of breath, chest pain (especially when breathing deeply), cough, and reduced ability to exercise.",
            "treatment": "Treatment depends on the underlying cause and may include thoracentesis (fluid drainage), diuretics, treating the underlying infection, or pleurodesis for recurrent cases.",
            "next_steps": "Your physician may order additional tests such as chest CT, pleural fluid analysis, blood tests (CBC, BMP, LDH, protein), or echocardiogram to determine the cause.",
        },
        "pneumonia": {
            "description": "Pneumonia is an infection that inflames the air sacs in one or both lungs, which may fill with fluid or pus.",
            "causes": "It can be caused by bacteria (most commonly Streptococcus pneumoniae), viruses, or fungi. Risk factors include age, smoking, chronic diseases, and weakened immunity.",
            "symptoms": "Symptoms include cough with phlegm, fever, chills, shortness of breath, chest pain, fatigue, and confusion (especially in older adults).",
            "treatment": "Treatment typically includes antibiotics (for bacterial pneumonia), rest, fluids, and fever-reducing medications. Severe cases may require hospitalization and oxygen therapy.",
            "next_steps": "Follow-up chest X-ray in 6-8 weeks is recommended to confirm resolution. Pneumococcal vaccination should be considered for prevention.",
        },
        "cardiomegaly": {
            "description": "Cardiomegaly refers to an enlarged heart, which is a sign of an underlying condition rather than a disease itself.",
            "causes": "Common causes include high blood pressure, coronary artery disease, heart valve disease, cardiomyopathy, and congenital heart defects.",
            "symptoms": "Symptoms may include shortness of breath, swelling in legs/ankles, irregular heartbeat, dizziness, and fatigue.",
            "treatment": "Treatment focuses on the underlying cause and may include medications (ACE inhibitors, beta-blockers, diuretics), lifestyle changes, or surgical interventions.",
            "next_steps": "An echocardiogram, EKG, and blood tests (BNP, troponin) are typically recommended for further evaluation.",
        },
        "atelectasis": {
            "description": "Atelectasis is a complete or partial collapse of the lung or a lobe of the lung.",
            "causes": "Common causes include blockage of air passages (mucus plug, foreign body), pressure on the lung from outside, post-surgical complications, and prolonged bed rest.",
            "symptoms": "May cause shortness of breath, rapid shallow breathing, cough, and low oxygen levels. Small atelectasis may not cause symptoms.",
            "treatment": "Treatment includes deep breathing exercises, chest physiotherapy, incentive spirometry, bronchoscopy for obstruction removal, or positive pressure ventilation.",
            "next_steps": "Follow-up imaging and pulmonary function tests may be recommended to monitor resolution.",
        },
        "pulmonary edema": {
            "description": "Pulmonary edema is a condition caused by excess fluid in the lungs, making it difficult to breathe.",
            "causes": "Most commonly caused by congestive heart failure. Other causes include acute respiratory distress syndrome (ARDS), high altitude, kidney failure, and certain medications.",
            "symptoms": "Symptoms include extreme shortness of breath, difficulty breathing when lying down, wheezing, gasping, anxiety, and coughing up frothy sputum.",
            "treatment": "Emergency treatment may include oxygen, diuretics (furosemide), and vasodilators. Long-term management addresses the underlying cause (heart failure medications, lifestyle changes).",
            "next_steps": "Urgent evaluation with echocardiogram, BNP levels, chest CT, and cardiology consultation is recommended.",
        },
    }

    _DEFAULT_INFO = {
        "description": "The identified condition requires clinical correlation with your medical history and physical examination findings.",
        "causes": "Multiple factors may contribute to this finding. Your healthcare provider can best determine the underlying cause based on your complete clinical picture.",
        "symptoms": "Symptoms can vary widely depending on the specific condition and its severity. Discuss any symptoms you're experiencing with your healthcare provider.",
        "treatment": "Treatment options depend on the specific diagnosis, severity, and your overall health status. Your physician will develop an individualized treatment plan.",
        "next_steps": "Additional diagnostic tests, specialist referrals, or follow-up imaging may be recommended based on clinical judgment.",
    }

    @staticmethod
    def generate_fallback(query: str, session_result: dict | None, chunks: list[dict] | None = None) -> str:
        query_lower = query.lower().strip()
        vision = (session_result or {}).get("vision") or {}
        nlp = (session_result or {}).get("nlp") or {}
        fusion = (session_result or {}).get("fusion") or {}

        risk_level = vision.get("risk_level", "UNKNOWN")
        anomaly_score = vision.get("anomaly_score", "N/A")
        diagnosis = nlp.get("primary_diagnosis", "")
        confidence = nlp.get("diagnosis_confidence", 0)
        differential = nlp.get("differential", [])

        # Find matching condition info
        diagnosis_lower = diagnosis.lower() if diagnosis else ""
        condition_info = ChatGenerator._DEFAULT_INFO
        for key, info in ChatGenerator._CONDITION_INFO.items():
            if key in diagnosis_lower or key in query_lower:
                condition_info = info
                break

        # ── Intent detection ──────────────────────────────────
        intent = ChatGenerator._detect_intent(query_lower)

        # ── Build contextual response ─────────────────────────
        if intent == "risk":
            response = ChatGenerator._respond_risk(risk_level, anomaly_score, diagnosis, confidence)
        elif intent == "diagnosis":
            response = ChatGenerator._respond_diagnosis(diagnosis, confidence, differential, condition_info)
        elif intent == "treatment":
            response = ChatGenerator._respond_treatment(diagnosis, condition_info)
        elif intent == "causes":
            response = ChatGenerator._respond_causes(diagnosis, condition_info)
        elif intent == "symptoms":
            response = ChatGenerator._respond_symptoms(diagnosis, condition_info)
        elif intent == "next_steps":
            response = ChatGenerator._respond_next_steps(diagnosis, condition_info)
        elif intent == "explain":
            response = ChatGenerator._respond_explain(diagnosis, condition_info)
        elif intent == "severity":
            response = ChatGenerator._respond_severity(risk_level, anomaly_score, diagnosis, confidence, condition_info)
        else:
            response = ChatGenerator._respond_general(query, risk_level, anomaly_score, diagnosis, confidence, condition_info)

        response += "\n\n⚠️ *This is AI-generated educational content. Please consult a licensed physician for medical advice.*"
        return response

    @staticmethod
    def _detect_intent(query: str) -> str:
        patterns = {
            "risk": ["risk", "dangerous", "serious", "critical", "worried", "scared", "concerned", "bad", "severe", "fatal", "die", "life threatening"],
            "diagnosis": ["diagnos", "what do i have", "what is wrong", "finding", "impression", "condition", "disease", "identified"],
            "treatment": ["treat", "cure", "medicine", "medication", "therapy", "how to fix", "how to solve", "what to do", "solution", "manage"],
            "causes": ["cause", "why", "reason", "how did", "what leads"],
            "symptoms": ["symptom", "sign", "feel", "experience", "pain", "ache"],
            "next_steps": ["next step", "what now", "should i", "recommend", "advice", "follow up", "test", "doctor"],
            "explain": ["explain", "what is", "what does", "mean", "understand", "tell me about", "describe"],
            "severity": ["how bad", "how serious", "score", "anomaly", "level", "stage", "grade"],
        }
        for intent, keywords in patterns.items():
            if any(kw in query for kw in keywords):
                return intent
        return "general"

    @staticmethod
    def _respond_risk(risk_level, anomaly_score, diagnosis, confidence):
        risk_desc = {
            "HIGH": "The analysis indicates a **HIGH risk** level, which means the AI detected significant abnormalities that warrant prompt medical attention.",
            "MEDIUM": "The analysis indicates a **MEDIUM risk** level, suggesting some abnormalities were detected that should be evaluated by a healthcare provider.",
            "LOW": "The analysis indicates a **LOW risk** level, suggesting no major abnormalities were detected. However, clinical correlation is always recommended.",
        }
        parts = [risk_desc.get(risk_level, f"The risk level is currently **{risk_level}**.")]
        parts.append(f"\n\nThe anomaly score is **{anomaly_score}/100**. ")
        if risk_level == "HIGH":
            parts.append("A high anomaly score suggests notable deviations from normal patterns. This does NOT necessarily mean a life-threatening condition, but it does indicate findings that a radiologist should review carefully.")
        if diagnosis:
            parts.append(f"\n\nThe primary finding is **{diagnosis}** (confidence: {round(confidence * 100)}%). Your physician can assess the clinical significance in context with your symptoms and history.")
        return "".join(parts)

    @staticmethod
    def _respond_diagnosis(diagnosis, confidence, differential, condition_info):
        if not diagnosis:
            return "No specific diagnosis has been determined from this analysis yet. The AI analysis may still be processing, or the findings may be inconclusive."
        parts = [f"The AI analysis suggests **{diagnosis}** as the primary finding with **{round(confidence * 100)}% confidence**.\n\n"]
        parts.append(f"{condition_info['description']}\n")
        if differential:
            parts.append("\n**Other possibilities considered:**\n")
            for d in differential[:3]:
                parts.append(f"• {d.get('disease', 'Unknown')} — {round(d.get('confidence', 0) * 100)}% likelihood\n")
        parts.append(f"\nPlease note that AI confidence does not directly translate to diagnostic certainty. Clinical examination and additional tests are essential for confirmation.")
        return "".join(parts)

    @staticmethod
    def _respond_treatment(diagnosis, condition_info):
        parts = []
        if diagnosis:
            parts.append(f"Regarding treatment options for **{diagnosis}**:\n\n")
            parts.append(condition_info["treatment"])
            parts.append(f"\n\n**Important:** Treatment should be personalized by your healthcare provider based on your specific situation, medical history, and the confirmed diagnosis.")
        else:
            parts.append("Without a confirmed diagnosis, I cannot suggest specific treatments. Please consult your physician for an appropriate treatment plan.")
        return "".join(parts)

    @staticmethod
    def _respond_causes(diagnosis, condition_info):
        parts = []
        if diagnosis:
            parts.append(f"**Possible causes of {diagnosis}:**\n\n")
            parts.append(condition_info["causes"])
        else:
            parts.append("The specific cause cannot be determined without a confirmed diagnosis. Your physician can help identify the underlying factors.")
        return "".join(parts)

    @staticmethod
    def _respond_symptoms(diagnosis, condition_info):
        parts = []
        if diagnosis:
            parts.append(f"**Common symptoms associated with {diagnosis}:**\n\n")
            parts.append(condition_info["symptoms"])
            parts.append("\n\nIf you're experiencing any of these symptoms, especially if they're worsening, please seek medical attention promptly.")
        else:
            parts.append("Symptom information is best interpreted in the context of a specific diagnosis. Discuss your symptoms with your healthcare provider.")
        return "".join(parts)

    @staticmethod
    def _respond_next_steps(diagnosis, condition_info):
        parts = [f"**Recommended next steps:**\n\n"]
        parts.append(condition_info["next_steps"])
        parts.append("\n\n**General recommendations:**\n")
        parts.append("1. Schedule a follow-up appointment with your physician to discuss these results\n")
        parts.append("2. Bring any relevant medical records or prior imaging studies\n")
        parts.append("3. Prepare a list of your current medications and symptoms\n")
        parts.append("4. Don't hesitate to seek urgent care if symptoms worsen suddenly")
        return "".join(parts)

    @staticmethod
    def _respond_explain(diagnosis, condition_info):
        if diagnosis:
            return f"**{diagnosis}:**\n\n{condition_info['description']}\n\n**Common causes:** {condition_info['causes']}\n\n**Typical symptoms:** {condition_info['symptoms']}"
        return "The analysis has been completed, but I need more context about what you'd like me to explain. You can ask about the diagnosis, risk level, anomaly score, or any specific finding."

    @staticmethod
    def _respond_severity(risk_level, anomaly_score, diagnosis, confidence, condition_info):
        parts = [f"**Severity assessment:**\n\n"]
        parts.append(f"• **Risk Level:** {risk_level}\n")
        parts.append(f"• **Anomaly Score:** {anomaly_score}/100\n")
        if diagnosis:
            parts.append(f"• **Primary Finding:** {diagnosis} ({round(confidence * 100)}% confidence)\n")
        parts.append(f"\nThe anomaly score represents how much the imaging deviates from normal patterns. ")
        if isinstance(anomaly_score, (int, float)):
            if anomaly_score >= 75:
                parts.append("A score above 75 indicates significant abnormalities that need prompt evaluation.")
            elif anomaly_score >= 50:
                parts.append("A score between 50-75 suggests moderate abnormalities that should be investigated.")
            else:
                parts.append("A score below 50 suggests relatively minor deviations from normal.")
        parts.append("\n\nRemember, the AI score is one data point — your physician will consider the full clinical picture.")
        return "".join(parts)

    @staticmethod
    def _respond_general(query, risk_level, anomaly_score, diagnosis, confidence, condition_info):
        parts = [f"Thank you for your question. Here's what I can tell you based on the analysis:\n\n"]
        if diagnosis:
            parts.append(f"Your scan analysis identified **{diagnosis}** as the primary finding (confidence: {round(confidence * 100)}%).\n\n")
            parts.append(f"{condition_info['description']}\n\n")
        if risk_level != "UNKNOWN":
            parts.append(f"The overall risk level is **{risk_level}** with an anomaly score of **{anomaly_score}/100**.\n\n")
        parts.append("You can ask me more specific questions about:\n")
        parts.append("• The **diagnosis** — what was found and what it means\n")
        parts.append("• **Risk level** — how serious this might be\n")
        parts.append("• **Treatment** options for the condition\n")
        parts.append("• **Causes** — why this may have developed\n")
        parts.append("• **Next steps** — what to do now")
        return "".join(parts)

    @staticmethod
    def generate_stream(prompt: str, model, tokenizer, max_new_tokens: int = 200):
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        
        generation_kwargs = {
            **inputs, "streamer": streamer, "max_new_tokens": max_new_tokens,
            "do_sample": True, "temperature": 0.7, "top_p": 0.9,
            "repetition_penalty": 1.2, "pad_token_id": tokenizer.eos_token_id
        }
        
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        for token in streamer:
            yield token
