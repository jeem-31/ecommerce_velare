# Docker Setup for Velare

## Prerequisites
- Docker installed ([Download Docker](https://www.docker.com/products/docker-desktop))
- Docker Compose installed (included with Docker Desktop)

## Quick Start

### 1. Build and Run with Docker Compose
```bash
docker-compose up --build
```

The application will be available at: `http://localhost:5000`

### 2. Run in Background (Detached Mode)
```bash
docker-compose up -d
```

### 3. Stop the Application
```bash
docker-compose down
```

### 4. View Logs
```bash
docker-compose logs -f
```

## Docker Commands

### Build the Image
```bash
docker build -t velare-app .
```

### Run the Container
```bash
docker run -p 5000:5000 --env-file .env velare-app
```

### Access Container Shell
```bash
docker exec -it velare-app /bin/bash
```

### Remove All Containers and Images
```bash
docker-compose down --rmi all --volumes
```

## Environment Variables

Make sure your `.env` file contains:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_secret_key
```

## Production Deployment

### Using Gunicorn (Production Server)

Update `Dockerfile` CMD to:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

### Environment Variables for Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Volumes

The following directories are persisted:
- `./static/uploads` - User uploaded files (products, profiles, documents)

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Permission Issues with Uploads
```bash
chmod -R 777 static/uploads
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Clear Cache and Rebuild
```bash
docker-compose build --no-cache
docker-compose up
```

## Docker Hub Deployment (Optional)

### 1. Tag the Image
```bash
docker tag velare-app yourusername/velare-app:latest
```

### 2. Push to Docker Hub
```bash
docker push yourusername/velare-app:latest
```

### 3. Pull and Run on Server
```bash
docker pull yourusername/velare-app:latest
docker run -p 5000:5000 --env-file .env yourusername/velare-app:latest
```

## Notes

- The application runs in development mode by default
- Hot reload is enabled when mounting code as volume
- For production, use Gunicorn and disable debug mode
- Make sure to secure your `.env` file and never commit it to Git
