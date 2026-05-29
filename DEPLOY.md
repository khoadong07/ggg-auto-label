# Hướng dẫn Deploy lên Server

## 📋 Yêu cầu Server

- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **CPU**: Tối thiểu 2 cores, khuyến nghị 4 cores
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB
- **Disk**: Tối thiểu 10GB free space
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

## 🚀 Các bước Deploy

### 1. Cài đặt Docker và Docker Compose

#### Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

#### CentOS/RHEL
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Upload code lên server

#### Cách 1: Sử dụng Git
```bash
# Clone repository
git clone <your-repo-url>
cd ggg

# Hoặc pull latest changes
git pull origin main
```

#### Cách 2: Sử dụng SCP
```bash
# Từ máy local
scp -r /path/to/ggg user@server-ip:/home/user/

# SSH vào server
ssh user@server-ip
cd /home/user/ggg
```

### 3. Build và chạy ứng dụng

#### Development mode
```bash
# Build image
make build

# Khởi động
make up

# Xem logs
make logs
```

#### Production mode (khuyến nghị)
```bash
# Build và chạy với resource limits
make rebuild-prod

# Xem logs
docker-compose -f docker-compose.prod.yml logs -f

# Kiểm tra resource usage
make stats
```

### 4. Cấu hình Firewall

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 8501/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

### 5. Truy cập ứng dụng

Mở trình duyệt và truy cập:
```
http://your-server-ip:8501
```

## 🔒 Cấu hình Reverse Proxy (Nginx)

### Cài đặt Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

### Cấu hình Nginx

Tạo file `/etc/nginx/sites-available/ggg`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/ggg /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Cài đặt SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## 📊 Monitoring và Maintenance

### Xem logs
```bash
# Real-time logs
make logs

# Last 100 lines
docker-compose logs --tail=100

# Logs của container cụ thể
docker logs ggg-auto-mapping
```

### Kiểm tra resource usage
```bash
# Container stats
make stats

# Disk usage
docker system df

# Detailed info
docker inspect ggg-auto-mapping
```

### Backup volumes
```bash
# Backup uploads
docker run --rm -v ggg_ggg-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup.tar.gz -C /data .

# Backup outputs
docker run --rm -v ggg_ggg-outputs:/data -v $(pwd):/backup \
  alpine tar czf /backup/outputs-backup.tar.gz -C /data .
```

### Restore volumes
```bash
# Restore uploads
docker run --rm -v ggg_ggg-uploads:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/uploads-backup.tar.gz"
```

### Dọn dẹp Docker
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

## 🔄 Update ứng dụng

```bash
# Pull latest code
git pull origin main

# Rebuild và restart
make rebuild-prod

# Verify
make logs
```

## 🐛 Troubleshooting

### Container không start
```bash
# Check logs
docker logs ggg-auto-mapping

# Check container status
docker ps -a

# Restart container
docker restart ggg-auto-mapping
```

### Out of memory
```bash
# Increase memory limit trong docker-compose.prod.yml
memory: 8G  # Tăng từ 4G lên 8G

# Rebuild
make rebuild-prod
```

### Port đã được sử dụng
```bash
# Check port usage
sudo lsof -i :8501

# Kill process
sudo kill -9 <PID>

# Hoặc đổi port trong docker-compose.yml
ports:
  - "8502:8501"  # Đổi từ 8501 sang 8502
```

## 📝 Auto-start on Boot

### Sử dụng systemd

Tạo file `/etc/systemd/system/ggg-app.service`:

```ini
[Unit]
Description=GGG Auto Mapping
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/ggg
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=user

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ggg-app
sudo systemctl start ggg-app
sudo systemctl status ggg-app
```

## 🔐 Security Best Practices

1. **Firewall**: Chỉ mở port cần thiết
2. **SSL**: Luôn sử dụng HTTPS trong production
3. **Updates**: Thường xuyên update Docker và dependencies
4. **Backups**: Backup volumes định kỳ
5. **Monitoring**: Setup monitoring và alerting
6. **Resource Limits**: Sử dụng docker-compose.prod.yml với resource limits

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Docker logs: `make logs`
2. Container status: `docker ps -a`
3. Resource usage: `make stats`
4. Disk space: `df -h`
5. Memory: `free -h`
