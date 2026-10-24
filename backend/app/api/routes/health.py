from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies import get_db, get_settings
from app.api.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db), settings = Depends(get_settings)):
    # Check database
    db_status = "disconnected"
    try:
        result = db.execute(text("SELECT 1"))
        db.commit()
        db_status = "connected"
        print(f"DEBUG: Database query result: {result.fetchone()}")
        print(f"DEBUG: Database status set to: {db_status}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Database connection failed: {e}")
        print(f"DEBUG: Exception type: {type(e).__name__}")

    # Check vector DB
    from pathlib import Path
    vector_path = Path(settings.vector_db_path)
    vec_status = "connected" if vector_path.exists() else "not_initialized"

    print(f"DEBUG: Returning database status: {db_status}")

    return HealthResponse(
        status="healthy",
        database=db_status,
        vector_db=vec_status,
        llm_provider=settings.llm_provider
    )