from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Any, Tuple, List

T = TypeVar("T")

async def paginate(db: AsyncSession, query: Any, page: int, limit: int) -> Tuple[List[T], int]:
    """Generic pagination. Returns (items, total_count)"""
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)
    
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    return items, total_count

async def get_or_404(db: AsyncSession, model: type[T], id: str) -> T:
    """Get by ID or raise HTTPException 404"""
    obj = await db.get(model, id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj

async def exists(db: AsyncSession, model: type[T], **filters) -> bool:
    """Check if record exists matching filters"""
    query = select(model).filter_by(**filters)
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none() is not None
