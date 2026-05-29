import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

from backend.ml.registry import ModelRegistry
from backend.core.exceptions import InvalidFileError, InferenceError, ModelNotLoadedError
from backend.api.v1.schemas.analysis import (
    AnalysisResult, VisionResult, NLPResult, FusionResult, ProcessingTimings
)

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    async def run(self, session_id: str, image_path: Path, symptoms_text: str) -> AnalysisResult:
        timings = {}
        warnings = []
        vision_result = None
        nlp_result = None
        fusion_result = None
        report_text = None
        
        # ── STEP 1: VALIDATE INPUT ────────────────────────────
        t0 = time.monotonic()
        try:
            if not image_path.exists():
                raise InvalidFileError("Image file not found")
            processed_image_path = await asyncio.to_thread(self._preprocess_image, image_path)
        except Exception as e:
            raise InferenceError(f"Input validation failed: {e}")
        timings["preprocess_ms"] = int((time.monotonic() - t0) * 1000)

        # ── STEP 2: VISION ANALYSIS (GPU) ─────────────────────
        t0 = time.monotonic()
        try:
            # We wrap this in resilience layers in resilience.py
            vision_result = await self._run_vision(processed_image_path)
        except (InvalidFileError, ModelNotLoadedError, InferenceError):
            raise
        except Exception as e:
            logger.warning(f"Vision analysis failed for session {session_id}: {e}")
            raise InferenceError(f"Chest X-ray vision analysis failed: {type(e).__name__}")
        timings["vision_ms"] = int((time.monotonic() - t0) * 1000)

        # ── STEP 3: VRAM CLEANUP ───────────────────────────────
        if vision_result is not None:
            import torch
            if torch.cuda.is_available():
                await asyncio.to_thread(torch.cuda.empty_cache)
                await asyncio.sleep(0.1)

        # ── STEP 4: NLP ANALYSIS (GPU/CPU) ────────────────────
        t0 = time.monotonic()
        if symptoms_text.strip():
            try:
                nlp_result = await self._run_nlp(symptoms_text)
            except Exception as e:
                logger.warning(f"NLP analysis failed for session {session_id}: {e}")
                warnings.append(f"NLP analysis unavailable: {type(e).__name__}")
        else:
            warnings.append("No symptoms text provided — NLP analysis skipped")
        timings["nlp_ms"] = int((time.monotonic() - t0) * 1000)

        # ── STEP 5: MULTIMODAL FUSION ─────────────────────────
        t0 = time.monotonic()
        if vision_result is not None and nlp_result is not None:
            try:
                fusion_result = await self._run_fusion(processed_image_path, symptoms_text)
            except Exception as e:
                logger.warning(f"Fusion failed for session {session_id}: {e}")
                warnings.append(f"Multimodal fusion unavailable: {type(e).__name__}")
        else:
            warnings.append("Fusion skipped: requires both vision and NLP results")
        timings["fusion_ms"] = int((time.monotonic() - t0) * 1000)

        # ── STEP 6: REPORT GENERATION ─────────────────────────
        t0 = time.monotonic()
        try:
            report_text = await self._generate_report(vision_result, nlp_result, fusion_result)
        except Exception as e:
            logger.warning(f"Report generation failed: {e}")
            report_text = self._fallback_report(vision_result, nlp_result)
            warnings.append("Using template report — AI report generation unavailable")
        timings["report_ms"] = int((time.monotonic() - t0) * 1000)

        # ── STEP 7: DETERMINE OVERALL STATUS ──────────────────
        if vision_result is None and nlp_result is None:
            overall_status = "FAILED"
        elif vision_result is None or nlp_result is None:
            overall_status = "PARTIAL"
        else:
            overall_status = "COMPLETE"

        timings["total_ms"] = sum(timings.values())

        return AnalysisResult(
            session_id=session_id, patient_id="", timestamp=datetime.now(timezone.utc),
            vision=vision_result, nlp=nlp_result, fusion=fusion_result,
            report_text=report_text, overall_status=overall_status,
            timings=ProcessingTimings(**timings), warnings=warnings
        )

    def _preprocess_image(self, image_path: Path) -> Path:
        from PIL import Image
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img = img.resize((224, 224), Image.LANCZOS)
            output_path = image_path.with_suffix(".processed.png")
            img.save(output_path, "PNG")
        return output_path

    async def _run_vision(self, image_path: Path) -> VisionResult:
        if not self.registry:
            raise ModelNotLoadedError("Chest X-ray vision model is not configured.")

        from backend.ml.vision.anomaly import AnomalyDetector
        from backend.ml.vision.pulmonary_anomaly import PulmonaryModelWrapper, onnx_reconstruction_panel

        state = await self.registry.get("convae_anomaly")
            
        if not state.is_available:
            raise ModelNotLoadedError(f"Chest X-ray vision model unavailable: {state.load_error or 'not loaded'}")
        
        if state.model is None:
            raise ModelNotLoadedError("Chest X-ray vision model unavailable: no trained artifact loaded.")

        if isinstance(state.model, PulmonaryModelWrapper):
            anomaly_score, model_confidence, heatmap_b64, top_regions = await asyncio.to_thread(
                state.model.predict, image_path
            )
        else:
            anomaly_score, model_confidence, reconstructed_np = await asyncio.to_thread(
                AnomalyDetector.score_convae, image_path, state.model, state.stats
            )
            heatmap_b64, top_regions = await asyncio.to_thread(
                onnx_reconstruction_panel, image_path, reconstructed_np, anomaly_score
            )
        
        risk_level = "LOW" if anomaly_score < 40 else "MEDIUM" if anomaly_score < 70 else "HIGH"
        return VisionResult(
            anomaly_score=round(anomaly_score, 1), risk_level=risk_level,
            heatmap_base64=heatmap_b64, top_regions=top_regions, model_confidence=model_confidence
        )

    async def _run_nlp(self, text: str) -> NLPResult:
        from backend.ml.nlp.ner import NERExtractor
        from backend.ml.nlp.classifier import DiseaseClassifier

        entities = None
        if self.registry:
            try:
                ner_state = await self.registry.get("scispacy_ner")
                if ner_state.is_available:
                    entities = await asyncio.to_thread(
                        NERExtractor.extract, text, ner_state.model
                    )
            except Exception as e:
                logger.warning(f"NER extraction failed: {e}")
                entities = None

        if entities is None:
            entities = await asyncio.to_thread(NERExtractor.extract_fallback, text)

        classifier_model = None
        if self.registry:
            try:
                clf_state = await self.registry.get("classifier")
                if clf_state.is_available:
                    classifier_model = clf_state.model
            except Exception:
                pass

        diagnosis = await asyncio.to_thread(DiseaseClassifier.classify, text, entities, classifier_model)
        return NLPResult(
            entities=entities, primary_diagnosis=diagnosis["primary"],
            diagnosis_confidence=diagnosis["confidence"], differential=diagnosis["differential"]
        )

    async def _run_fusion(self, image_path: Path, text: str) -> FusionResult:
        from backend.ml.fusion.medclip import MultimodalFusion, FallbackFusion

        try:
            state = await self.registry.get("biomedvlp") if self.registry else None
        except Exception:
            state = None
        if state and state.is_available and state.model is not None and state.tokenizer is not None:
            similarity, alignment = await asyncio.to_thread(
                MultimodalFusion.compute_similarity, image_path, text, state.model, state.tokenizer, state.current_device
            )
        else:
            similarity, alignment = await asyncio.to_thread(FallbackFusion.compute_similarity, image_path, text)
        final_risk = "HIGH" if similarity < 0.3 else "MEDIUM" if similarity < 0.7 else "LOW"
        return FusionResult(image_text_similarity=round(similarity, 3), alignment=alignment, final_risk=final_risk)

    async def _generate_report(self, vision: VisionResult | None, nlp: NLPResult | None, fusion: FusionResult | None) -> str:
        from backend.ml.rag.generator import ReportGenerator
        
        if not self.registry:
            raise ModelNotLoadedError("Report generation unavailable")

        try:
            state = await self.registry.get("biogpt_base")
        except Exception as exc:
            raise ModelNotLoadedError("Report generation unavailable") from exc
        if not state.is_available or state.model is None or state.tokenizer is None:
            raise ModelNotLoadedError("Report generation unavailable")
            
        return await asyncio.to_thread(
            ReportGenerator.generate, vision, nlp, fusion, state.model, state.tokenizer
        )

    def _fallback_report(self, vision: VisionResult | None, nlp: NLPResult | None) -> str:
        parts = ["## AI-Assisted Analysis Report\n\n*Note: This is an automated template report.*\n"]
        if vision:
            parts.append(f"**Imaging Findings:** Anomaly score of {vision.anomaly_score}/100 indicates {vision.risk_level.lower()} risk findings.")
        if nlp:
            diseases = ", ".join(nlp.entities.diseases) if nlp.entities.diseases else "none identified"
            symptoms = ", ".join(nlp.entities.symptoms) if nlp.entities.symptoms else "none documented"
            parts.append(f"**Clinical Impression:** {nlp.primary_diagnosis} (confidence: {nlp.diagnosis_confidence:.0%}). Identified conditions: {diseases}. Symptoms: {symptoms}.")
        parts.append("\n**Recommendation:** Please consult a licensed physician for diagnosis and treatment.")
        return "\n".join(parts)

    def _run_demo_vision(self, image_path: Path) -> VisionResult:
        from PIL import Image, ImageOps, ImageDraw
        import io
        import base64
        import numpy as np

        with Image.open(image_path) as img:
            original = ImageOps.exif_transpose(img).convert("L").resize((224, 224))

        arr = np.asarray(original, dtype=np.float32) / 255.0
        contrast = float(arr.std())
        dark_ratio = float((arr < 0.18).mean())
        bright_ratio = float((arr > 0.82).mean())
        anomaly_score = min(100.0, max(5.0, 35.0 + contrast * 120.0 + dark_ratio * 25.0 - bright_ratio * 10.0))
        confidence = min(0.95, max(0.25, abs(anomaly_score - 50.0) / 55.0))

        heat = np.uint8(np.clip(np.abs(arr - arr.mean()) / (arr.std() + 1e-6), 0, 1) * 255)
        heat_img = Image.fromarray(heat, mode="L").resize((224, 224)).convert("RGB")
        heat_pixels = heat_img.load()
        for y in range(224):
            for x in range(224):
                v = heat_pixels[x, y][0]
                heat_pixels[x, y] = (v, max(0, v - 80), max(0, 80 - v // 3))

        original_rgb = original.convert("RGB")
        overlay = Image.blend(original_rgb, heat_img, 0.45)
        panel = Image.new("RGB", (692, 254), (6, 18, 32))
        panel.paste(original_rgb, (0, 0))
        panel.paste(heat_img, (234, 0))
        panel.paste(overlay, (468, 0))
        draw = ImageDraw.Draw(panel)
        draw.text((8, 230), "Original", fill=(220, 230, 235))
        draw.text((242, 230), "Demo Heatmap", fill=(220, 230, 235))
        draw.text((476, 230), f"Overlay ({anomaly_score:.1f})", fill=(220, 230, 235))

        buffer = io.BytesIO()
        panel.save(buffer, format="PNG", optimize=True)
        heatmap_b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

        risk_level = "LOW" if anomaly_score < 40 else "MEDIUM" if anomaly_score < 70 else "HIGH"
        return VisionResult(
            anomaly_score=round(anomaly_score, 1),
            risk_level=risk_level,
            heatmap_base64=heatmap_b64,
            top_regions=[{"x": 76, "y": 56, "width": 72, "height": 86, "confidence": round(confidence, 3)}],
            model_confidence=round(confidence, 3),
        )
