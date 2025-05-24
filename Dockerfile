FROM python:3.10-slim

# Cài đặt gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy và cài đặt requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tạo thư mục models
RUN mkdir -p models

# Copy mã nguồn (chỉ copy những file cần thiết)
COPY main.py .
COPY download_model.py .
COPY models/ ./models/
COPY static/ ./static/ 2>/dev/null || true
COPY templates/ ./templates/ 2>/dev/null || true

# Tải model SAM nếu chưa có
RUN python download_model.py

# Expose port
EXPOSE 8000

# Chạy server với hypercorn
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000"] 