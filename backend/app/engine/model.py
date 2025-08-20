import torch
from torchvision import transforms
from PIL import Image

# Load once at startup
_model = None

def load_model():
    global _model
    if _model is None:
        # Replace with your actual model file path
        _model = torch.jit.load("app/engine/deepscan.pt", map_location="cpu")
        _model.eval()
    return _model

def preprocess(img_path: str):
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
    ])
    img = Image.open(img_path).convert("RGB")
    return transform(img).unsqueeze(0)

def predict(front_path: str, back_path: str):
    model = load_model()
    f = preprocess(front_path)
    b = preprocess(back_path)
    with torch.no_grad():
        out = model(f, b)  # adjust signature depending on training
    return out
