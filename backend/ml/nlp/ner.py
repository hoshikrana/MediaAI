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
    def extract(text: str, model: AutoModelForTokenClassification, tokenizer: AutoTokenizer, device: str = "cuda") -> NERResult:
        if not text or not text.strip():
            return NERResult(diseases=[], symptoms=[], medications=[], anatomy=[], raw_entities=[])
            
        chunks = NERExtractor._chunk_text(text, tokenizer, max_length=400, overlap=50)
        
        all_entities = []
        seen_spans = set()
        
        for chunk_text, char_offset in chunks:
            chunk_entities = NERExtractor._extract_chunk(chunk_text, model, tokenizer, device, char_offset)
            for entity in chunk_entities:
                span_key = (entity["text"].lower(), entity["entity_type"])
                if span_key not in seen_spans:
                    seen_spans.add(span_key)
                    all_entities.append(entity)
                    
        grouped = {"diseases": [], "symptoms": [], "medications": [], "anatomy": []}
        for entity in all_entities:
            entity_type = entity["entity_type"].split("-")[-1]
            group_key = NERExtractor.ENTITY_MAP.get(entity_type)
            if group_key:
                entity_text = entity["text"].strip()
                if entity_text and entity_text not in grouped[group_key]:
                    grouped[group_key].append(entity_text)
                    
        return NERResult(
            diseases=grouped["diseases"], symptoms=grouped["symptoms"],
            medications=grouped["medications"], anatomy=grouped["anatomy"],
            raw_entities=all_entities
        )
        
    @staticmethod
    def _extract_chunk(text: str, model, tokenizer, device: str, char_offset: int = 0) -> list[dict]:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, return_offsets_mapping=True, padding=False)
        offset_mapping = inputs.pop("offset_mapping")[0]
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            
        predictions = torch.argmax(outputs.logits, dim=-1)[0]
        entities = []
        current_entity = None
        
        for idx, (pred_id, offsets) in enumerate(zip(predictions, offset_mapping)):
            label = model.config.id2label[pred_id.item()]
            start, end = offsets[0].item(), offsets[1].item()
            
            if start == 0 and end == 0: # Special token
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue
                
            token_text = text[start:end]
            
            if label.startswith("B-"):
                if current_entity: entities.append(current_entity)
                current_entity = {
                    "text": token_text, "entity_type": label,
                    "start": start + char_offset, "end": end + char_offset,
                    "confidence": torch.softmax(outputs.logits[0][idx], dim=-1).max().item()
                }
            elif label.startswith("I-") and current_entity:
                current_entity["text"] += token_text if not token_text.startswith("##") else token_text[2:]
                current_entity["end"] = end + char_offset
            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                    
        if current_entity:
            entities.append(current_entity)
            
        return [e for e in entities if e["confidence"] > 0.7]

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
