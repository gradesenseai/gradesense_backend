from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import shutil
import tempfile
import uuid

router = APIRouter()

class EstimateResponse(BaseModel):
    request_id: str = Field(..., description="Server-generated request identifier")
    estimated_grade: float = Field(..., ge=1.0, le=10.0)
    subgrades: dict = Field(
        default_factory=dict,
        description="Estimated subgrades for centering/corners/edges/surface"
    )
    notes: Optional[str] = None
    disclaimer: str = (
        "All grade outputs are estimates for educational purposes only and are "
        "not affiliated with or guaranteed by PSA or BGS."
    )

@router.post("/estimate", response_model=EstimateResponse)
async def estimate(
    front: UploadFile = File(..., description="Front image file"),
    back: UploadFile = File(..., description="Back image file"),
    card_meta: Optional[str] = Form(
        None, description="Optional JSON string with card metadata"
    ),
):
    # Basic content-type validation
    valid_types = {"image/jpeg", "image/png", "image/webp"}
    if front.content_type not in valid_types or back.content_type not in valid_types:
        raise HTTPException(status_code=415, detail="Images must be JPEG, PNG, or WEBP.")

    # Persist to temp for downstream processing (replace with object storage later)
    req_id = str(uuid.uuid4())
    tmp_dir = tempfile.mkdtemp(prefix=f"gradesense_{req_id}_")

    def _save(upload: UploadFile, name: str) -> str:
        path = f"{tmp_dir}/{name}"
        with open(path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        return path

    front_path = _save(front, "front")
    back_path = _save(back, "back")

    # TODO: Replace this stub with your real model inference pipeline.
    # For now, return a sane placeholder so the frontend can integrate immediately.
    # You can attach logs/telemetry here as needed.
    subgrades = {
        "centering": 9.0,
        "corners": 8.5,
        "edges": 9.0,
        "surface": 8.5,
    }

    payload = EstimateResponse(
        request_id=req_id,
        estimated_grade=8.8,
        subgrades=subgrades,
        notes="Placeholder estimate. Connect to model inference for live results."
    )
    return JSONResponse(content=payload.model_dump())
