from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import cv2
import torch
from PIL import Image
import io
import os
import base64
import download_model
download_model.download_sam_model()


from segment_anything import sam_model_registry, SamPredictor

app = FastAPI()

# CORS cho phép gọi từ frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mô hình SAM
MODEL_TYPE = "vit_h"
CHECKPOINT_PATH = "models/sam_vit_h_4b8939.pth"

device = "cuda" if torch.cuda.is_available() else "cpu"
sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
sam.to(device)
predictor = SamPredictor(sam)

def apply_perspective_transform(image, src_points, dst_points):
    """Áp dụng phép biến đổi phối cảnh"""
    M = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))
    return warped

def blend_images(foreground, background, mask, alpha=0.7):
    """Blend hai ảnh với mask"""
    mask_3d = np.stack([mask] * 3, axis=-1)
    blended = background * (1 - mask_3d * alpha) + foreground * (mask_3d * alpha)
    return blended.astype(np.uint8)

def image_to_base64(image):
    """Chuyển ảnh numpy array thành base64 string"""
    _, buffer = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer).decode('utf-8')

@app.get("/")
def read_root():
    return {"message": "SAM + FastAPI server is running."}

@app.post("/segment")
async def segment_image(
    image: UploadFile = File(...),
    point_x: int = Form(...),
    point_y: int = Form(...)
):
    contents = await image.read()
    np_image = np.array(Image.open(io.BytesIO(contents)).convert("RGB"))

    predictor.set_image(np_image)
    input_point = np.array([[point_x, point_y]])
    input_label = np.array([1])

    masks, scores, _ = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True
    )

    # Chọn mask có điểm số cao nhất
    best_mask = masks[np.argmax(scores)]

    # Áp dụng mask lên ảnh (đổ màu xanh)
    result = np_image.copy()
    result[best_mask] = [0, 255, 0]  # RGB: xanh lá

    # Chuyển kết quả thành base64
    result_base64 = image_to_base64(result)
    
    return JSONResponse(content={
        "status": "success",
        "message": "Segmented mask applied.",
        "image": result_base64
    })

@app.post("/transform-perspective")
async def transform_perspective(
    image: UploadFile = File(...),
    src_points: str = Form(...),  # JSON string of 4 points
    dst_points: str = Form(...)   # JSON string of 4 points
):
    contents = await image.read()
    np_image = np.array(Image.open(io.BytesIO(contents)).convert("RGB"))
    
    # Parse points from JSON strings
    src = np.array(eval(src_points), dtype=np.float32)
    dst = np.array(eval(dst_points), dtype=np.float32)
    
    # Apply perspective transform
    result = apply_perspective_transform(np_image, src, dst)
    
    # Convert result to base64
    result_base64 = image_to_base64(result)
    
    return JSONResponse(content={
        "status": "success",
        "message": "Perspective transform applied.",
        "image": result_base64
    })

@app.post("/blend")
async def blend_images_endpoint(
    foreground: UploadFile = File(...),
    background: UploadFile = File(...),
    mask: UploadFile = File(...),
    alpha: float = Form(0.7)
):
    # Read images
    fg_contents = await foreground.read()
    bg_contents = await background.read()
    mask_contents = await mask.read()
    
    # Convert to numpy arrays
    fg_image = np.array(Image.open(io.BytesIO(fg_contents)).convert("RGB"))
    bg_image = np.array(Image.open(io.BytesIO(bg_contents)).convert("RGB"))
    mask_image = np.array(Image.open(io.BytesIO(mask_contents)).convert("L"))
    
    # Ensure all images have same dimensions
    if fg_image.shape[:2] != bg_image.shape[:2]:
        bg_image = cv2.resize(bg_image, (fg_image.shape[1], fg_image.shape[0]))
    
    # Apply blending
    result = blend_images(fg_image, bg_image, mask_image, alpha)
    
    # Convert result to base64
    result_base64 = image_to_base64(result)
    
    return JSONResponse(content={
        "status": "success",
        "message": "Images blended successfully.",
        "image": result_base64
    })

@app.post("/api/replace-tile/")
async def replace_tile(
    original: UploadFile = File(...),
    tile: UploadFile = File(...),
    point_x: int = Form(...),
    point_y: int = Form(...)
):
    # Đọc ảnh gốc và tile
    original_bytes = await original.read()
    tile_bytes = await tile.read()
    original_img = np.array(Image.open(io.BytesIO(original_bytes)).convert("RGB"))
    tile_img = np.array(Image.open(io.BytesIO(tile_bytes)).convert("RGB"))

    # Phân vùng vùng sàn bằng SAM
    predictor.set_image(original_img)
    input_point = np.array([[point_x, point_y]])
    input_label = np.array([1])
    masks, scores, _ = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True
    )
    best_mask = masks[np.argmax(scores)]

    # Resize/lặp tile cho vừa vùng mask
    mask_indices = np.where(best_mask)
    min_y, max_y = np.min(mask_indices[0]), np.max(mask_indices[0])
    min_x, max_x = np.min(mask_indices[1]), np.max(mask_indices[1])
    region_h = max_y - min_y + 1
    region_w = max_x - min_x + 1

    # Tính số lượng tile cần thiết
    num_tile_y = 6
    num_tile_x = 6

    # Tính kích thước mới cho tile để khớp với kích thước mask
    tile_h_new = region_h // num_tile_y
    tile_w_new = region_w // num_tile_x

    # Đảm bảo kích thước tile là số chẵn
    tile_h_new = (tile_h_new // 2) * 2
    tile_w_new = (tile_w_new // 2) * 2

    # Resize tile
    tile_img_resized = cv2.resize(tile_img, (tile_w_new, tile_h_new)).astype(np.uint8)
    
    # Tạo pattern tile với kích thước chính xác
    tiled = np.tile(tile_img_resized, (num_tile_y, num_tile_x, 1))
    tiled = tiled[:region_h, :region_w, :].astype(np.uint8)

    # Đảm bảo mask là bool và có kích thước chính xác
    region_mask = best_mask[min_y:max_y+1, min_x:max_x+1].astype(bool)
    
    # Tạo ảnh kết quả
    result = original_img.copy()
    region = result[min_y:max_y+1, min_x:max_x+1]

    # Thay thế từng kênh màu với kiểm tra kích thước
    for c in range(3):
        if region_mask.shape == tiled[..., c].shape:
            region[..., c][region_mask] = tiled[..., c][region_mask]
        else:
            print(f"Kích thước không khớp: mask={region_mask.shape}, tile={tiled[..., c].shape}")
            # Cắt mask hoặc tile để khớp kích thước
            min_h = min(region_mask.shape[0], tiled.shape[0])
            min_w = min(region_mask.shape[1], tiled.shape[1])
            region[:min_h, :min_w, c][region_mask[:min_h, :min_w]] = tiled[:min_h, :min_w, c][region_mask[:min_h, :min_w]]
    result[min_y:max_y+1, min_x:max_x+1] = region

    # Trả về ảnh trực tiếp
    _, buffer = cv2.imencode(".png", result)
    return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
