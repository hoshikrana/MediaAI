from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import asyncio
import os

from backend.db.session import get_db
from backend.db.models import AnalysisSession
from backend.core.dependencies import get_current_user
from backend.utils.validators import safe_temp_path
from backend.utils.pdf import MedicalReportGenerator

router = APIRouter()

def cleanup_file(path: str):
    try:
        os.remove(path)
        # Also attempt to remove any temp images left behind by ReportLab
        img_temp = str(path).replace(".pdf", ".png").replace("report_", "temp_img_")
        if os.path.exists(img_temp):
            os.remove(img_temp)
    except Exception:
        pass

@router.get("/{session_id}")
async def download_report(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(AnalysisSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized or not found")
        
    if session.status != "READY":
        raise HTTPException(status_code=400, detail="Report not ready yet")
        
    # Create permanent PDF directory
    pdf_dir = Path("backend/uploads/pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # If the PDF hasn't been generated yet, create it permanently
    if not session.pdf_filename:
        safe_filename = f"medsight_report_{session_id}.pdf"
        permanent_pdf_path = pdf_dir / safe_filename
        
        # Build a clean session data dict
        session_data = {
            "id": session.id,
            "patient_id": session.patient_id,
            "status": session.status,
            "result_json": session.result_json or {},
            "risk_level": session.risk_level,
        }
        await asyncio.to_thread(MedicalReportGenerator.generate, session_data, str(permanent_pdf_path))
        
        # Save to DB
        session.pdf_filename = safe_filename
        await db.commit()
    
    pdf_path = pdf_dir / session.pdf_filename
    
    if not pdf_path.exists():
        # Fallback if file was deleted
        session.pdf_filename = None
        await db.commit()
        raise HTTPException(status_code=404, detail="PDF file was lost from disk. Please request again to regenerate.")
    
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"medsight_report_{session_id[:8]}.pdf"
    )
