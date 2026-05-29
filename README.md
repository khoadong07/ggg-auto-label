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
pip install -r requirements.txt
pip install streamlit
```

### Chạy ứng dụng

```bash
streamlit run app.py
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
