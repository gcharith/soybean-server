import torch
import torch.nn as nn
import numpy as np
from torchvision import models, transforms
from PIL import Image
import torch.nn.functional as F
from fastapi import Depends

class_names = [
    "bacterial_blight",
    "cercospora_leaf_blight",
    "downey_mildew",
    "frogeye",
    "healthy",
    "potassium_deficiency",
    "soybean_rust",
    "target_spot"
]


img_size = 224
model_wts = "best_resnet50_leaf_images_0619.pth"
device = torch.device("cpu")

def get_transforms():
    return transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],  
            std=[0.229, 0.224, 0.225],
        ),
    ])

def load_model():
    """Build the ResNet-50 architecture and load trained weights, cached."""
    model = models.resnet50(weights=None)  

    in_features = model.fc.in_features  # 2048 for ResNet-50
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, len(class_names)),
    )

    state_dictionary = torch.load(model_wts, map_location=device)

    # handle both plain state_dict and {"model_state_dict": ...}
    model.load_state_dict(state_dictionary)
    model.to(device)
    model.eval()
    return model

def model_prediction(image_path: str):
    """Run prediction on a single PIL image."""
    image = Image.open(image_path).convert("RGB")
    model = load_model()
    transform = get_transforms()
    img_t = transform(image).unsqueeze(0).to(device)  # [1, C, H, W]

    with torch.no_grad():
        outputs = model(img_t)               # [1, num_classes]
        probs = F.softmax(outputs, dim=1)[0] # [num_classes]

    conf, pred_idx = torch.max(probs, dim=0)
    predicted_class = class_names[pred_idx.item()]
    confidence = conf.item()
    return predicted_class, confidence

