from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import shutil, tempfile, uuid, os, logging

router = APIRouter()
log = logging.getLogger("uvicorn.error")

class EstimateResponse(BaseModel):
    request_id: str = Field(...)
    estimated_grade: float = Field(..., ge=1.0, le=10.0)
    subgrades: dict = Field(default_factory=dict)
    notes: Optional[str] = None
    disclaimer: str = ("All grade outputs are estimates for educational purposes only and "
                       "are not affiliated with or guaranteed by PSA or BGS.")

def _stub_result():
    return 8.8, {"centering": 9.0, "corners": 8.5, "edges": 9.0, "surface": 8.5}, "Placeholder estimate (stub)."

@router.post("/estimate", response_model=EstimateResponse)
async def estimate(
    front: UploadFile = File(...),
    back: UploadFile = File(...),
    card_meta: Optional[str] = Form(None),
):
    valid_types = {"image/jpeg", "image/png", "image/webp"}
    if front.content_type not in valid_types or back.content_type not in valid_types:
        raise HTTPException(status_code=415, detail="Images must be JPEG, PNG, or WEBP.")

    req_id = str(uuid.uuid4())
    tmp_dir = tempfile.mkdtemp(prefix=f"gradesense_{req_id}_")

    def _save(upload: UploadFile, name: str) -> str:
        path = os.path.join(tmp_dir, name)
        with open(path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        return path

    front_path = _save(front, "front")
    back_path  = _save(back, "back")

    # Toggle stub vs. model via env (safe fallback if model not ready)
    use_stub = os.getenv("USE_STUB", "true").lower() in ("1","true","yes")

    try:
        if use_stub:
            overall, subs, note = _stub_result()
        else:
            # Import lazily to avoid import errors when stubbing
            from app.engine.model import predict
            out = predict(front_path, back_path)  # must return dict-like values
            overall = float(out["overall"])
            subs = {
                "centering": float(out["centering"]),
                "corners": float(out["corners"]),
                "edges": float(out["edges"]),
                "surface": float(out["surface"]),
            }
            note = "Deep Scan model inference"
    except Exception as e:
        log.exception(f"[{req_id}] Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference error: {type(e).__name__}: {e}")

    payload = EstimateResponse(
        request_id=req_id,
        estimated_grade=overall,
        subgrades=subs,
        notes=note
    )
    return JSONResponse(content=payload.model_dump())
