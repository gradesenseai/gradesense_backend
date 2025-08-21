# /backend/app/engine/model.py
import os, pathlib, logging

log = logging.getLogger("uvicorn.error")

# ENV VARS
WEIGHTS_PATH = os.getenv("WEIGHTS_PATH", "app/engine/deepscan.pt")
WEIGHTS_URL  = os.getenv("WEIGHTS_URL", "").strip()  # optional: https URL to .pt
ALLOW_STUB_FALLBACK = os.getenv("ALLOW_STUB_FALLBACK", "true").lower() in ("1","true","yes")

_model = None

def _ensure_weights():
    path = pathlib.Path(WEIGHTS_PATH)
    if path.exists():
        return str(path)

    if WEIGHTS_URL:
        # lazy import so requests isn't needed unless we actually download
        import requests
        path.parent.mkdir(parents=True, exist_ok=True)
        log.info(f"Downloading weights from {WEIGHTS_URL} -> {path}")
        r = requests.get(WEIGHTS_URL, timeout=300)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return str(path)

    if ALLOW_STUB_FALLBACK:
        log.warning(f"Missing weights at {path}. Using stub fallback.")
        return None

    raise ValueError(f"The provided filename {path} does not exist and WEIGHTS_URL not set")

def _stub_predict(front_path: str, back_path: str):
    # deterministic stub values
    return {
        "overall": 8.7,
        "centering": 9.0,
        "corners": 8.5,
        "edges": 8.8,
        "surface": 8.6
    }

def _load_model():
    global _model
    if _model is not None:
        return _model

    weights = _ensure_weights()
    if weights is None:
        _model = None
        return None

    import torch  # heavy import only when needed
    _model = torch.jit.load(weights, map_location="cpu")
    _model.eval()
    return _model

def predict(front_path: str, back_path: str):
    model = _load_model()
    if model is None:
        return _stub_predict(front_path, back_path)

    # If your JIT takes two tensors, adapt accordingly.
    # Minimal preprocessing to keep it generic:
    from PIL import Image
    import torch
    from torchvision import transforms

    tfm = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
    ])

    f = tfm(Image.open(front_path).convert("RGB")).unsqueeze(0)
    b = tfm(Image.open(back_path).convert("RGB")).unsqueeze(0)

    with torch.no_grad():
        out = model(f, b)  # adjust to your model’s forward signature

    # Map your model outputs to the contract below
    # Replace this mapping with the real outputs
    return {
        "overall": float(out["overall"]),
        "centering": float(out["centering"]),
        "corners": float(out["corners"]),
        "edges": float(out["edges"]),
        "surface": float(out["surface"]),
    }
