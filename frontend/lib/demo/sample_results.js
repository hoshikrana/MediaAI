export const SAMPLE_RESULT = {
    session_id: "demo-session-001",
    patient_id: "DEMO-PT-001",
    timestamp: "2025-01-15T14:32:00Z",
    vision: {
        anomaly_score: 67.3,
        risk_level: "MEDIUM",
        heatmap_base64: null,  
        top_regions: [
            {x: 45, y: 62, width: 85, height: 70, confidence: 0.79},
            {x: 130, y: 40, width: 60, height: 55, confidence: 0.64}
        ],
        model_confidence: 0.83
    },
    nlp: {
        entities: {
            diseases: ["pleural effusion"],
            symptoms: ["shortness of breath", "chest pain", "fatigue"],
            medications: [],
            anatomy: ["right lung", "pleural space"],
            raw_entities: []
        },
        primary_diagnosis: "Pleural Effusion",
        diagnosis_confidence: 0.79,
        differential: [
            {disease: "Heart Failure", confidence: 0.12},
            {disease: "Pneumonia", confidence: 0.06}
        ]
    },
    fusion: {
        image_text_similarity: 0.68,
        alignment: "MEDIUM",
        final_risk: "MEDIUM"
    },
    report_text: "## AI Diagnostic Report\n\n### Imaging Findings\n🟡 **Risk Level:** MEDIUM\n**Anomaly Score:** 67.3/100\n\n### Clinical Assessment\n**Primary Impression:** Pleural Effusion (79% confidence)\n\n### AI Analysis\nThe imaging demonstrates findings consistent with right-sided pleural effusion. The clinical symptoms of shortness of breath and chest pain are consistent with this diagnosis.\n\n### Recommendation\nPlease consult a licensed physician for clinical correlation and treatment planning.",
    overall_status: "COMPLETE",
    timings: {vision_ms: 2340, nlp_ms: 1560, fusion_ms: 890, report_ms: 4320, total_ms: 9110},
    warnings: []
}
