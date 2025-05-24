import os
import gdown

def download_sam_model():
    os.makedirs("models", exist_ok=True)
    output = "models/sam_vit_h_4b8939.pth"
    if os.path.exists(output):
        print("Model đã tồn tại.")
        return

    file_id = "17bAEzcG9p4Fj0m61chTDLE_BH3pjZmN4"
    url = f"https://drive.google.com/uc?id={file_id}"
    print("Đang tải mô hình SAM từ Google Drive...")
    gdown.download(url, output, quiet=False)

if __name__ == "__main__":
    download_sam_model()
