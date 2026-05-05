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
