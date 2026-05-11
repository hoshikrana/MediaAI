import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
from backend.api.v1.schemas.analysis import NERResult

class NERExtractor:
    ENTITY_MAP = {
        "DISEASE": "diseases",
        "SYMPTOM": "symptoms",
        "MEDICATION": "medications",
        "ANATOMY": "anatomy"
    }
    
    @staticmethod
    def extract_fallback(text: str) -> NERResult:
        import re

        if not text or not text.strip():
            return NERResult(diseases=[], symptoms=[], medications=[], anatomy=[], raw_entities=[])

        vocab = {
            "diseases": [
                "pneumonia", "pleural effusion", "cardiomegaly", "atelectasis",
                "pneumothorax", "tuberculosis", "covid-19", "bronchitis",
                "asthma", "pulmonary edema", "fibrosis", "emphysema",
            ],
            "symptoms": [
                "chest pain", "shortness of breath", "dyspnea", "fever", "cough",
                "fatigue", "wheezing", "night sweats", "weight loss", "sputum",
            ],
            "medications": [
                "albuterol", "amoxicillin", "azithromycin", "steroid", "inhaler",
                "antibiotic", "aspirin", "warfarin",
            ],
            "anatomy": ["chest", "lung", "lungs", "pleura", "heart", "rib", "diaphragm"],
        }
        label_map = {
            "diseases": "DISEASE",
            "symptoms": "SYMPTOM",
            "medications": "MEDICATION",
            "anatomy": "ANATOMY",
        }

        grouped = {key: [] for key in vocab}
        raw_entities = []
        for group, terms in vocab.items():
            for term in terms:
                for match in re.finditer(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE):
                    matched = text[match.start():match.end()]
                    if matched.lower() not in {item.lower() for item in grouped[group]}:
                        grouped[group].append(matched)
                    raw_entities.append({
                        "text": matched,
                        "entity_type": label_map[group],
                        "confidence": 0.72,
                        "start": match.start(),
                        "end": match.end(),
                    })

        return NERResult(
            diseases=grouped["diseases"],
            symptoms=grouped["symptoms"],
            medications=grouped["medications"],
            anatomy=grouped["anatomy"],
            raw_entities=raw_entities,
        )

    @staticmethod
    def extract(text: str, nlp_model: any) -> NERResult:
        if not text or not text.strip():
            return NERResult(diseases=[], symptoms=[], medications=[], anatomy=[], raw_entities=[])
            
        if nlp_model is None:
            return NERExtractor.extract_fallback(text)
            
        doc = nlp_model(text)
        
        grouped = {"diseases": [], "symptoms": [], "medications": [], "anatomy": []}
        raw_entities = []
        
        for ent in doc.ents:
            # scispaCy entity types: DISEASE, CHEMICAL, GENE, PROTEIN, etc.
            # Map them to our schema
            label = ent.label_
            mapped_type = "SYMPTOM" # Default fallback
            
            if label == "DISEASE": mapped_type = "DISEASE"
            elif label == "CHEMICAL": mapped_type = "MEDICATION"
            
            group_key = NERExtractor.ENTITY_MAP.get(mapped_type)
            if group_key:
                entity_text = ent.text.strip()
                if entity_text and entity_text not in grouped[group_key]:
                    grouped[group_key].append(entity_text)
            
            raw_entities.append({
                "text": ent.text,
                "entity_type": mapped_type,
                "confidence": 0.85, # scispaCy doesn't give direct confidence easily, use a high constant for pre-trained
                "start": ent.start_char,
                "end": ent.end_char
            })
                    
        return NERResult(
            diseases=grouped["diseases"], symptoms=grouped["symptoms"],
            medications=grouped["medications"], anatomy=grouped["anatomy"],
            raw_entities=raw_entities
        )

    @staticmethod
    def _chunk_text(text: str, tokenizer, max_length: int = 400, overlap: int = 50) -> list[tuple[str, int]]:
        words = text.split()
        chunks = []
        current_words = []
        current_length = 0
        char_offset = 0
        
        for word in words:
            word_tokens = tokenizer(word, add_special_tokens=False)["input_ids"]
            if current_length + len(word_tokens) > max_length and current_words:
                chunk_text = " ".join(current_words)
                chunks.append((chunk_text, char_offset))
                
                overlap_words = current_words[-overlap//4:]
                char_offset += len(" ".join(current_words[:-len(overlap_words)])) + 1
                current_words = overlap_words
                current_length = sum(len(tokenizer(w, add_special_tokens=False)["input_ids"]) for w in current_words)
                
            current_words.append(word)
            current_length += len(word_tokens)
            
        if current_words:
            chunks.append((" ".join(current_words), char_offset))
            
        return chunks if chunks else [(text, 0)]

def highlight_entities(text: str, entities: list[dict]) -> str:
    COLORS = {
        "DISEASE": "#FF6B6B", "SYMPTOM": "#FFD93D",
        "MEDICATION": "#6BCB77", "ANATOMY": "#4D96FF"
    }
    sorted_entities = sorted(entities, key=lambda e: e["start"], reverse=True)
    result = text
    for entity in sorted_entities:
        entity_type = entity["entity_type"].replace("B-", "").replace("I-", "")
        color = COLORS.get(entity_type, "#cccccc")
        span = (
            f'<mark style="background:{color};padding:2px 4px;border-radius:3px;'
            f'font-size:0.85em" title="{entity_type} ({entity["confidence"]:.0%})">'
            f'{entity["text"]}</mark>'
        )
        result = result[:entity["start"]] + span + result[entity["end"]:]
    return result
