import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.schemas.chat import ChatRequest
from backend.core.dependencies import get_model_registry, get_current_user
from backend.db.models import AnalysisSession, ChatMessage
from backend.db.session import get_db
from sqlalchemy import select
from backend.ml.rag.retriever import MedicalRAG
from backend.ml.rag.generator import ChatGenerator

router = APIRouter()

@router.get("/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(AnalysisSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    query = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "sources": m.sources_json or [],
            "created_at": m.created_at.isoformat()
        } for m in messages
    ]

@router.post("")
@router.post("/", include_in_schema=False)
async def chat(
    body: ChatRequest,
    registry = Depends(get_model_registry),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(AnalysisSession, body.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Session not found or not authorized")

    _is_safe, warning = MedicalRAG.is_safe_query(body.message)
    
    # Save user message to DB
    user_msg = ChatMessage(session_id=body.session_id, role="user", content=body.message)
    db.add(user_msg)
    await db.commit()
    
    # Fetch actual DB history
    history_query = select(ChatMessage).where(ChatMessage.session_id == body.session_id).order_by(ChatMessage.created_at)
    history_result = await db.execute(history_query)
    history_msgs = history_result.scalars().all()
    history_dicts = [{"role": m.role, "content": m.content} for m in history_msgs]
    
    session_result = session.result_json if hasattr(session, 'result_json') else {}
    chunks = MedicalRAG.retrieve(body.message, session_result, n_results=5)
    prompt = MedicalRAG.build_prompt(body.message, chunks, history_dicts, session_result)
    
    biogpt_state = await registry.get("biogpt_base") if registry else None
    biogpt_ready = biogpt_state and biogpt_state.is_available and biogpt_state.model is not None and biogpt_state.tokenizer is not None
    full_response = []
    
    async def stream_generator():
        yield f"data: {json.dumps({'type': 'sources', 'sources': chunks[:3]})}\n\n"
        
        final_text = ""
        if not biogpt_ready:
            fallback = ChatGenerator.generate_fallback(body.message, session_result, chunks)
            final_text = fallback
            yield f"data: {json.dumps({'type': 'token', 'token': fallback})}\n\n"
        else:
            token_gen = await asyncio.to_thread(lambda: list(ChatGenerator.generate_stream(prompt, biogpt_state.model, biogpt_state.tokenizer)))
            for token in token_gen:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                await asyncio.sleep(0.02) # Optional smoothing
            final_text = "".join(full_response)
                
        if warning:
            final_text += f"\n\n{warning}"
            yield f"data: {json.dumps({'type': 'token', 'token': warning})}\n\n"
            
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        # Save assistant message to DB after stream finishes
        # Must use a new session since the stream runs after the endpoint returns
        from backend.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as bg_db:
            ast_msg = ChatMessage(session_id=body.session_id, role="assistant", content=final_text, sources_json=chunks[:3])
            bg_db.add(ast_msg)
            await bg_db.commit()
        
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
