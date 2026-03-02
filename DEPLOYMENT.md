# 云服务器部署指南

本文档介绍如何将项目部署到云服务器（阿里云、腾讯云、AWS 等）。

## 前置要求

- 云服务器（推荐配置：2核4G， Ubuntu 20.04 或 22.04）
- 服务器已安装 Docker 和 Docker Compose
- 域名（可选，用于配置 HTTPS）

---

## 一、上传项目到服务器

### 方式 1：使用 SCP 上传

```bash
# 在本地执行，将项目打包上传
tar -czf enterprise-agent.tar.gz --exclude='.git' --exclude='node_modules' --exclude='venv' --exclude='__pycache__' enterprise-agent/
scp enterprise-agent.tar.gz root@your-server-ip:/root/
```

### 方式 2：使用 Git（推荐）

```bash
# 在服务器上执行
git clone https://github.com/yourusername/Enterprise-MultiAgent-System.git
cd Enterprise-MultiAgent-System
```

---

## 二、服务器配置

### 1. 安装 Docker 和 Docker Compose

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 配置防火墙

```bash
# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # 前端（可选）
sudo ufw enable
```

---

## 三、配置环境变量

```bash
# 在服务器上进入项目目录
cd Enterprise-MultiAgent-System

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

**必须修改的配置：**

```env
# 数据库密码（生产环境务必修改！）
POSTGRES_PASSWORD=your_secure_password_here

# LLM API Keys
SILICONFLOW_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# JWT 密钥（至少32位随机字符串）
JWT_SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
```

---

## 四、启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

**等待时间：**
- Milvus 启动需要 30-60 秒
- 后端启动需要 10-20 秒
- 前端启动需要 5-10 秒

---

## 五、验证部署

### 1. 检查服务状态

```bash
docker-compose ps
# 所有服务状态应该是 "Up"
```

### 2. 访问服务

| 服务 | 地址 |
|------|------|
| 前端界面 | `http://your-server-ip:3000` |
| 后端 API | `http://your-server-ip:8000` |
| API 文档 | `http://your-server-ip:8000/docs` |

---

## 六、配置 Nginx 反向代理（可选）

如果需要使用域名和 HTTPS，配置 Nginx：

### 安装 Nginx 和 Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 配置 Nginx

创建配置文件 `/etc/nginx/sites-available/enterprise-agent`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 启用配置并申请 SSL 证书

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/enterprise-agent /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx

# 申请 SSL 证书
sudo certbot --nginx -d your-domain.com
```

---

## 七、常用运维命令

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 单个服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f milvus-standalone
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 停止服务

```bash
docker-compose down

# 停止并删除数据卷（谨慎！）
docker-compose down -v
```

---

## 八、故障排查

### 问题 1：服务启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
sudo netstat -tulpn | grep :8000
```

### 问题 2：Milvus 连接失败

```bash
# 等待 Milvus 完全启动（30-60秒）
docker-compose logs milvus-standalone | grep "successfully started"
```

### 问题 3：前端无法连接后端

检查 `frontend/Dockerfile` 中的代理配置是否正确。

---

## 九、生产环境建议

1. **定期备份数据库**
   ```bash
   docker-compose exec postgres pg_dump -U postgres enterprise_agent > backup.sql
   ```

2. **监控服务状态**
   - 使用 `docker-compose ps` 定期检查
   - 配置日志轮转

3. **更新安全补丁**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **配置自动重启**
   - 已在 docker-compose.yml 中配置 `restart: unless-stopped`

---

## 十、性能优化建议

1. **增加服务器资源**（根据负载调整）
2. **配置 Redis 缓存**
3. **使用负载均衡器**（多实例部署）
4. **优化 Milvus 配置**（增加内存分配）
