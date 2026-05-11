from pydantic import BaseModel
from typing import Literal, List, Optional
from datetime import datetime

class EntityItem(BaseModel):
    text: str
    entity_type: str
    confidence: float
    start: int
    end: int

class NERResult(BaseModel):
    diseases: List[str]
    symptoms: List[str]
    medications: List[str]
    anatomy: List[str]
    raw_entities: List[EntityItem]

class DiagnosisDifferential(BaseModel):
    disease: str
    confidence: float

class NLPResult(BaseModel):
    entities: NERResult
    primary_diagnosis: str
    diagnosis_confidence: float
    differential: List[DiagnosisDifferential]
    error: Optional[str] = None

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: float

class VisionResult(BaseModel):
    model_config = {'protected_namespaces': ()}
    anomaly_score: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    heatmap_base64: Optional[str] = None
    top_regions: List[BoundingBox]
    model_confidence: float
    error: Optional[str] = None

class FusionResult(BaseModel):
    image_text_similarity: float
    alignment: Literal["LOW", "MEDIUM", "HIGH"]
    final_risk: Literal["LOW", "MEDIUM", "HIGH"]
    error: Optional[str] = None

class ProcessingTimings(BaseModel):
    vision_ms: int
    nlp_ms: int
    fusion_ms: int
    report_ms: int
    total_ms: int

class AnalysisResult(BaseModel):
    session_id: str
    patient_id: str
    timestamp: datetime
    vision: Optional[VisionResult] = None
    nlp: Optional[NLPResult] = None
    fusion: Optional[FusionResult] = None
    report_text: Optional[str] = None
    overall_status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    timings: ProcessingTimings
    warnings: List[str]

class TaskSubmitResponse(BaseModel):
    task_id: str
    session_id: str
    estimated_wait_seconds: int
    position_in_queue: int

class TaskStatusResponse(BaseModel):
    task_id: str
    session_id: str
    status: str
    position_in_queue: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
