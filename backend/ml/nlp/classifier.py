import threading
from backend.api.v1.schemas.analysis import NERResult

CHEST_CONDITIONS = [
    "Pneumonia", "Pleural Effusion", "Cardiomegaly", "Atelectasis",
    "Pneumothorax", "Pulmonary Edema", "Tuberculosis", "Lung Cancer",
    "COVID-19", "Chronic Obstructive Pulmonary Disease", "Asthma",
    "Pulmonary Fibrosis", "Bronchitis", "Emphysema", "Heart Failure",
    "Aortic Aneurysm", "Pulmonary Embolism", "Sarcoidosis",
    "No significant finding", "Other condition"
]

class DiseaseClassifier:
    """Zero-shot classifier. No fine-tuning needed. Always runs on CPU."""
    
    @staticmethod
    def classify(text: str, entities: NERResult, model_pipe: any = None, top_k: int = 3) -> dict:
        if not text or not text.strip():
            return {"primary": "Insufficient information", "confidence": 0.0, "differential": []}

        fallback = DiseaseClassifier._classify_with_rules(text, entities, top_k)
        
        # If no model provided, use rule-based fallback immediately
        if model_pipe is None:
            return fallback

        enriched_text = DiseaseClassifier._build_enriched_text(text, entities)
        try:
            result = model_pipe(
                enriched_text,
                candidate_labels=CHEST_CONDITIONS,
                multi_label=False
            )
        except Exception:
            return fallback
        
        scores_dict = dict(zip(result["labels"], result["scores"]))
        sorted_labels = sorted(scores_dict, key=scores_dict.get, reverse=True)
        
        primary = sorted_labels[0]
        primary_confidence = scores_dict[primary]
        
        differential = [
            {"disease": label, "confidence": round(scores_dict[label], 3)}
            for label in sorted_labels[1:top_k]
        ]
        
        return {
            "primary": primary,
            "confidence": round(primary_confidence, 3),
            "differential": differential
        }

    @staticmethod
    def _build_enriched_text(original: str, entities: NERResult) -> str:
        parts = [original]
        if entities.diseases:
            parts.append(f"Diagnosed conditions: {', '.join(entities.diseases)}")
        if entities.symptoms:
            parts.append(f"Presenting symptoms: {', '.join(entities.symptoms)}")
        if entities.medications:
            parts.append(f"Current medications: {', '.join(entities.medications)}")
            
        enriched = ". ".join(parts)
        return enriched[:1024]

    @staticmethod
    def _classify_with_rules(text: str, entities: NERResult, top_k: int = 3) -> dict:
        text_lower = text.lower()
        scores = {condition: 0.05 for condition in CHEST_CONDITIONS}
        rules = {
            "Pneumonia": ["fever", "cough", "sputum", "opacity", "consolidation"],
            "Pleural Effusion": ["effusion", "pleural", "fluid"],
            "Cardiomegaly": ["cardiomegaly", "enlarged heart", "cardiac"],
            "Pneumothorax": ["pneumothorax", "collapsed lung", "pleuritic"],
            "Tuberculosis": ["night sweats", "weight loss", "tuberculosis", "tb"],
            "Asthma": ["wheezing", "inhaler", "asthma"],
            "Pulmonary Edema": ["edema", "heart failure", "orthopnea"],
            "Bronchitis": ["bronchitis", "productive cough"],
        }
        for condition, keywords in rules.items():
            scores[condition] += sum(0.22 for keyword in keywords if keyword in text_lower)

        for disease in entities.diseases:
            for condition in CHEST_CONDITIONS:
                if disease.lower() in condition.lower() or condition.lower() in disease.lower():
                    scores[condition] += 0.45

        if not any(value > 0.05 for value in scores.values()):
            scores["No significant finding"] = 0.42

        sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        primary, primary_score = sorted_items[0]
        differential = [
            {"disease": label, "confidence": round(min(score, 0.92), 3)}
            for label, score in sorted_items[1:top_k]
        ]
        return {
            "primary": primary,
            "confidence": round(min(primary_score, 0.92), 3),
            "differential": differential,
        }

if __name__ == "__main__":
    test_text = "Patient complains of severe chest pain and shortness of breath."
    entities = NERResult(diseases=[], symptoms=["chest pain", "shortness of breath"], medications=[], anatomy=[], raw_entities=[])
    res = DiseaseClassifier.classify(test_text, entities)
    print("Classification result:", res)
