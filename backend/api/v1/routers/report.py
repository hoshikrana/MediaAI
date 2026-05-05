from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
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
        
    temp_pdf_path = safe_temp_path(f"report_{session_id}.pdf")
    
    # Generate blocking PDF creation in a thread to not block ASGI
    import asyncio
    await asyncio.to_thread(MedicalReportGenerator.generate, session.__dict__, temp_pdf_path)
    
    background_tasks.add_task(cleanup_file, str(temp_pdf_path))
    
    return FileResponse(
        path=str(temp_pdf_path),
        media_type="application/pdf",
        filename=f"medsight_report_{session_id[:8]}.pdf",
        headers={"Cache-Control": "no-store"}
    )
