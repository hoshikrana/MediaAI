import json
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas.chat import ChatRequest
from backend.core.dependencies import get_session_or_404, get_model_registry, get_current_user
from backend.db.session import get_db
# Note: Assume session_manager is built in db/utils.py to manage chat history records
# from backend.db.utils import session_manager 
from backend.ml.rag.retriever import MedicalRAG
from backend.ml.rag.generator import ChatGenerator

router = APIRouter()

@router.post("/")
async def chat(
    body: ChatRequest,
    session = Depends(get_session_or_404),
    registry = Depends(get_model_registry),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_safe, warning = MedicalRAG.is_safe_query(body.message)
    
    # Placeholder for actual DB history fetch
    history_dicts = [] 
    
    session_result = session.result_json if hasattr(session, 'result_json') else {}
    chunks = MedicalRAG.retrieve(body.message, session_result, n_results=5)
    prompt = MedicalRAG.build_prompt(body.message, chunks, history_dicts, session_result)
    
    biogpt_state = await registry.get("biogpt_base")
    full_response = []
    
    async def stream_generator():
        yield f"data: {json.dumps({'type': 'sources', 'sources': chunks[:3]})}\n\n"
        
        if not biogpt_state.is_available:
            fallback = "I cannot provide a detailed answer right now as the AI system is unavailable."
            yield f"data: {json.dumps({'type': 'token', 'token': fallback})}\n\n"
        else:
            token_gen = await asyncio.to_thread(lambda: list(ChatGenerator.generate_stream(prompt, biogpt_state.model, biogpt_state.tokenizer)))
            for token in token_gen:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                await asyncio.sleep(0.02) # Optional smoothing
                
        if warning:
            yield f"data: {json.dumps({'type': 'token', 'token': warning})}\n\n"
            
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
