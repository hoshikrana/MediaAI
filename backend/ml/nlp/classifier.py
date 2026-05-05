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
    _pipeline = None
    _pipeline_lock = threading.Lock()
    
    @classmethod
    def _get_pipeline(cls):
        if cls._pipeline is None:
            with cls._pipeline_lock:
                if cls._pipeline is None:
                    from transformers import pipeline
                    # Note: For faster inference use "valhalla/distilbart-mnli-12-1" 
                    # We stick to bart-large-mnli as instructed, but it takes ~2-4s on CPU
                    cls._pipeline = pipeline(
                        "zero-shot-classification",
                        model="facebook/bart-large-mnli",
                        device=-1
                    )
        return cls._pipeline
        
    @staticmethod
    def classify(text: str, entities: NERResult, top_k: int = 3) -> dict:
        if not text or not text.strip():
            return {"primary": "Insufficient information", "confidence": 0.0, "differential": []}
            
        enriched_text = DiseaseClassifier._build_enriched_text(text, entities)
        pipe = DiseaseClassifier._get_pipeline()
        
        result = pipe(
            enriched_text,
            candidate_labels=CHEST_CONDITIONS,
            multi_label=False
        )
        
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

if __name__ == "__main__":
    test_text = "Patient complains of severe chest pain and shortness of breath."
    entities = NERResult(diseases=[], symptoms=["chest pain", "shortness of breath"], medications=[], anatomy=[], raw_entities=[])
    res = DiseaseClassifier.classify(test_text, entities)
    print("Classification result:", res)
