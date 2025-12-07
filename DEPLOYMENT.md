# Audio to MIDI Converter - Deployment Guide

## Overview

This guide covers deploying the Audio to MIDI Converter application using Docker and Docker Compose. The deployment includes:

- **Backend**: FastAPI with ML processing capabilities
- **Frontend**: React application with modern UI
- **Database**: MongoDB for job persistence
- **Proxy**: Nginx for serving frontend and API routing
- **Cache**: Redis for session management (optional)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM (ML processing is resource-intensive)
- At least 10GB storage space
- Git for cloning the repository

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd mp3stemxml
```

### 2. Configure Environment

```bash
# Copy production environment template
cp .env.production .env

# Edit the environment file
nano .env
```

**Important: Update these values in `.env`:**
- `MONGO_PASSWORD` - Set a secure MongoDB password
- `CORS_ORIGINS` - Set your domain(s)
- `FRONTEND_URL` - Set your frontend URL
- `REACT_APP_BACKEND_URL` - Set your backend URL

### 3. Deploy

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

## Detailed Deployment

### Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Nginx     │    │   Backend   │
│   (React)   │────│   Proxy     │────│  (FastAPI)  │
│   Port 80   │    │   Port 80   │    │  Port 8001  │
└─────────────┘    └─────────────┘    └─────────────┘
                                         │
                                         ▼
                                   ┌─────────────┐
                                   │  MongoDB    │
                                   │  Port 27017 │
                                   └─────────────┘
```

### Services

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| Frontend | nginx:alpine | Serves React app | 80, 443 |
| Backend | Custom Python | FastAPI + ML processing | 8001 |
| MongoDB | mongo:7.0 | Database for jobs | 27017 |
| Redis | redis:7-alpine | Caching (optional) | 6379 |

### Environment Variables

#### Backend (.env)
```bash
# Database
MONGO_URL=mongodb://admin:password@mongodb:27017
DB_NAME=audio_converter

# Application
CORS_ORIGINS=https://yourdomain.com
PYTHONPATH=/app

# Performance
MAX_WORKERS=4
UPLOAD_MAX_SIZE=100MB
PROCESSING_TIMEOUT=1800
```

#### Frontend (build-time)
```bash
REACT_APP_BACKEND_URL=https://yourdomain.com/api
```

## Deployment Commands

### Basic Commands

```bash
# Deploy application
./scripts/deploy.sh deploy

# Check health
./scripts/deploy.sh health

# View logs
./scripts/deploy.sh logs

# Stop services
./scripts/deploy.sh stop

# Restart services
./scripts/deploy.sh restart
```

### Maintenance Commands

```bash
# Update application
./scripts/deploy.sh update

# Clean up old containers/images
./scripts/deploy.sh cleanup
```

### Docker Compose Direct

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend (if needed)
docker-compose up -d --scale backend=2

# Stop services
docker-compose down
```

## Production Considerations

### Security

1. **Change default passwords** in `.env`
2. **Use HTTPS** with SSL certificates
3. **Restrict CORS origins** to your domain only
4. **Enable firewalls** to restrict access
5. **Regular updates** of Docker images

### Performance

1. **Resource allocation**: Minimum 4GB RAM for ML processing
2. **Storage**: Monitor disk space for processed files
3. **Scaling**: Use `--scale backend=N` for multiple workers
4. **Monitoring**: Consider adding monitoring tools

### File Management

```bash
# Monitor storage usage
docker exec mp3stemxml_backend du -sh /app/processed /app/uploads

# Clean old processed files (add to cron)
find /app/processed -type f -mtime +7 -delete
```

### Backup Strategy

```bash
# Backup MongoDB
docker exec mp3stemxml_mongodb mongodump --out /backup

# Backup user files
docker run --rm -v mp3stemxml_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

## SSL/HTTPS Setup

### Using Let's Encrypt

```bash
# Add to docker-compose.yml for SSL
certbot:
  image: certbot/certbot
  volumes:
    - ./certbot/conf:/etc/letsencrypt
    - ./certbot/www:/var/www/certbot
  command: certonly --webroot --webroot-path=/var/www/certbot --email your@email.com --agree-tos --no-eff-email -d yourdomain.com
```

### Nginx SSL Configuration

Update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL settings...
}
```

## Monitoring

### Health Checks

The application includes built-in health checks:

- Backend: `GET /`
- Frontend: `GET /health`
- Database: MongoDB ping

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Metrics (Optional)

Add monitoring with Prometheus/Grafana:

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  
grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
```

## Troubleshooting

### Common Issues

1. **Backend fails to start**
   ```bash
   # Check logs
   docker-compose logs backend
   
   # Check MongoDB connection
   docker-compose exec backend python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('DB OK')"
   ```

2. **Frontend not loading**
   ```bash
   # Check Nginx configuration
   docker-compose exec frontend nginx -t
   
   # Check build files
   docker-compose exec frontend ls -la /usr/share/nginx/html
   ```

3. **Processing failures**
   ```bash
   # Check ML models
   docker-compose exec backend python -c "import demucs, basic_pitch; print('ML OK')"
   
   # Check disk space
   df -h
   ```

### Performance Issues

1. **High memory usage**: Reduce `MAX_WORKERS` in `.env`
2. **Slow processing**: Check if ML models are downloaded
3. **Upload failures**: Increase `UPLOAD_MAX_SIZE` and timeouts

## Scaling

### Horizontal Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Add load balancer (optional)
# Use HAProxy or cloud load balancer
```

### Vertical Scaling

Increase resources in Docker daemon or cloud provider settings.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          echo "${{ secrets.DOCKER_COMPOSE }}" | base64 -d > docker-compose.prod.yml
          docker-compose -f docker-compose.prod.yml up -d
```

## Support

For deployment issues:

1. Check logs: `./scripts/deploy.sh logs`
2. Verify environment: `./scripts/deploy.sh health`
3. Review this documentation
4. Check GitHub issues for common problems

---

**Deployment completed! 🎵**

Your Audio to MIDI Converter should now be running at:
- Frontend: `http://localhost` (or your domain)
- Backend API: `http://localhost:8001/api`
