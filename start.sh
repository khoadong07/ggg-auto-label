#!/bin/bash

# Script khởi động nhanh cho GGG Auto Mapping

echo "🍽️  GGG Auto Mapping - Golden Gate Group"
echo "========================================"
echo ""

# Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker chưa được cài đặt. Vui lòng cài đặt Docker trước."
    exit 1
fi

# Kiểm tra Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose chưa được cài đặt. Vui lòng cài đặt Docker Compose trước."
    exit 1
fi

echo "✅ Docker và Docker Compose đã sẵn sàng"
echo ""

# Build image
echo "🔨 Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Build thất bại!"
    exit 1
fi

echo ""
echo "✅ Build thành công!"
echo ""

# Khởi động container
echo "🚀 Khởi động ứng dụng..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Khởi động thất bại!"
    exit 1
fi

echo ""
echo "✅ Ứng dụng đã khởi động thành công!"
echo ""
echo "📊 Truy cập ứng dụng tại: http://localhost:8501"
echo ""
echo "📝 Các lệnh hữu ích:"
echo "   - Xem logs:        docker-compose logs -f"
echo "   - Dừng ứng dụng:   docker-compose down"
echo "   - Khởi động lại:   docker-compose restart"
echo ""
