# GGG Auto Mapping - Golden Gate Group

Hệ thống tự động xử lý Social Listening cho dự án Golden Gate Group.

## 🚀 Chạy với Docker

### Yêu cầu
- Docker
- Docker Compose

### Khởi động ứng dụng

#### Cách 1: Sử dụng Makefile (khuyến nghị)

```bash
# Xem tất cả commands
make help

# Build Docker image
make build

# Khởi động ứng dụng
make up

# Xem logs
make logs

# Dừng ứng dụng
make down

# Khởi động lại
make restart

# Rebuild từ đầu
make rebuild

# Dừng và xóa volumes
make clean
```

#### Cách 2: Sử dụng Docker Compose trực tiếp

```bash
# Build và chạy container
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng ứng dụng
docker-compose down

# Dừng và xóa volumes
docker-compose down -v
```

### Truy cập ứng dụng

Mở trình duyệt và truy cập: http://localhost:8501

## 📁 Cấu trúc dự án

```
ggg/
├── app.py                    # Streamlit UI chính
├── ggg_pipeline.py          # Pipeline xử lý dữ liệu
├── requirements.txt         # Python dependencies
├── topic_brand_mapping.json # Mapping Topic -> Brand Code
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
└── .dockerignore          # Files to exclude from Docker image
```

## 🔧 Chạy local (không dùng Docker)

### Cài đặt dependencies

```bash
# Cài đặt PyTorch CPU-only (nhẹ hơn)
pip install torch==2.0.0+cpu torchvision==0.15.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Cài đặt các dependencies khác
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
streamlit run app.py
```

## ⚙️ Tối ưu cho Server CPU

Ứng dụng đã được tối ưu để chạy trên server chỉ có CPU:

- **PyTorch CPU-only**: Sử dụng phiên bản CPU của PyTorch (nhẹ hơn ~2GB so với GPU version)
- **Multi-threading**: Tối ưu số lượng threads cho CPU (OMP_NUM_THREADS=4)
- **Batch processing**: Xử lý dữ liệu theo batch để tối ưu memory
- **Lazy loading**: Model chỉ được load khi cần thiết

### Điều chỉnh số lượng CPU threads

Chỉnh sửa trong `docker-compose.yml`:

```yaml
environment:
  - OMP_NUM_THREADS=4  # Thay đổi số này tùy theo số CPU cores
  - MKL_NUM_THREADS=4
  - OPENBLAS_NUM_THREADS=4
```

## 📊 Tính năng

- Upload file Buzz Data (bắt buộc)
- Upload file Demographic (tùy chọn)
- Tự động xử lý và mapping dữ liệu
- Dự đoán Labels bằng AI model
- Join demographic data
- Download kết quả dạng Excel

## 🛠️ Development

### Rebuild Docker image

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Mount code để development

Uncomment các dòng volume trong `docker-compose.yml`:

```yaml
volumes:
  - ./app.py:/app/app.py
  - ./ggg_pipeline.py:/app/ggg_pipeline.py
```

## 📝 Ghi chú

- Model AI: `Khoa/kompa-ggg-032026`
- Uploads và outputs được lưu trong Docker volumes
- Container tự động restart khi có lỗi
- Health check mỗi 30 giây

## 🏢 Powered by Kompa AI
