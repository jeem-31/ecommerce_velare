# How to Dockerize Your System - Complete Guide

This guide will help you containerize any application using Docker, based on the Velare E-Commerce project setup.

## What is Docker?

Docker packages your application and all its dependencies into a container, so it runs the same way on any machine. Think of it as a portable box that contains everything your app needs to run.

## Prerequisites

- Docker Desktop installed on your machine
- Basic understanding of your application's requirements
- Your application code ready

## Step-by-Step Dockerization Process

### Step 1: Create a Dockerfile

The Dockerfile is a recipe that tells Docker how to build your application container.

**For a Python/Flask Application:**

```dockerfile
# Start with a base image (Python version)
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Expose the port your app runs on
EXPOSE 5000

# Command to run your application
CMD ["python", "app.py"]
```

**For a Node.js Application:**

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### Step 2: Create a .dockerignore File

This tells Docker which files to ignore (like .gitignore).

```
# Environment variables
.env
.env.local

# Python
__pycache__/
*.pyc
venv/
env/

# Node.js
node_modules/
npm-debug.log

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Documentation
*.md
!README.md

# Tests
tests/
*.test.js

# Logs
*.log
```

### Step 3: Create docker-compose.yml (Optional but Recommended)

Docker Compose helps manage multi-container applications and makes running Docker easier.

**Basic Setup:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"  # host:container
    environment:
      - ENV_VAR_1=value1
      - ENV_VAR_2=value2
    volumes:
      - .:/app  # Mount code for development
    restart: unless-stopped
```

**With Database:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
    depends_on:
      - db
    volumes:
      - .:/app
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Step 4: Build Your Docker Image

```bash
# Build the image
docker build -t my-app-name .

# Or with docker-compose
docker-compose build
```

### Step 5: Run Your Container

```bash
# Run with Docker
docker run -p 5000:5000 my-app-name

# Or with docker-compose (recommended)
docker-compose up

# Run in background (detached mode)
docker-compose up -d
```

### Step 6: Test Your Application

Open your browser and go to:
- `http://localhost:5000` (or whatever port you exposed)

### Step 7: Stop Your Container

```bash
# With docker-compose
docker-compose down

# With Docker
docker stop <container-id>
```

## Common Dockerization Patterns

### Pattern 1: Web Application with Static Files

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create directories for uploads
RUN mkdir -p static/uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Pattern 2: Multi-Stage Build (Smaller Images)

```dockerfile
# Build stage
FROM python:3.10 as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000
CMD ["python", "app.py"]
```

### Pattern 3: Development vs Production

**docker-compose.dev.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app  # Live code reload
    environment:
      - FLASK_ENV=development
      - DEBUG=True
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "80:5000"
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    restart: always
```

Run with:
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables Best Practices

### Option 1: .env File (Development)

Create `.env` file:
```
DATABASE_URL=postgresql://user:pass@localhost:5432/db
SECRET_KEY=your-secret-key
API_KEY=your-api-key
```

Update `docker-compose.yml`:
```yaml
services:
  app:
    env_file:
      - .env
```

### Option 2: Environment Variables (Production)

```yaml
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
```

Then set them in your hosting platform (AWS, Heroku, etc.)

## Useful Docker Commands

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View logs
docker logs <container-id>
docker-compose logs -f

# Execute command in running container
docker exec -it <container-id> bash
docker-compose exec app bash

# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# View disk usage
docker system df

# Clean up everything
docker system prune -a --volumes
```

## Troubleshooting

### Issue: Port already in use
```bash
# Find what's using the port
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Mac/Linux

# Kill the process or use a different port
```

### Issue: Container exits immediately
```bash
# Check logs
docker logs <container-id>

# Run interactively to debug
docker run -it my-app-name bash
```

### Issue: Changes not reflecting
```bash
# Rebuild without cache
docker-compose build --no-cache
docker-compose up --force-recreate
```

### Issue: Permission denied
```bash
# On Linux, you might need to add user to docker group
sudo usermod -aG docker $USER
# Then log out and back in
```

## Deployment Checklist

- [ ] Dockerfile created and tested
- [ ] .dockerignore configured
- [ ] docker-compose.yml configured
- [ ] Environment variables secured (not in code)
- [ ] Volumes configured for persistent data
- [ ] Health checks added (optional)
- [ ] Logging configured
- [ ] Security: Run as non-root user
- [ ] Image size optimized
- [ ] Documentation updated

## Example: Complete Flask App Dockerization

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - ./static/uploads:/app/static/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**.dockerignore:**
```
__pycache__
*.pyc
.env
.git
.vscode
tests/
*.md
!README.md
```

## Next Steps

1. Test locally with `docker-compose up`
2. Push your image to Docker Hub or container registry
3. Deploy to cloud platform (AWS, Azure, Google Cloud, Heroku)
4. Set up CI/CD to automatically build and deploy

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Hub](https://hub.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Remember:** Docker makes your application portable and consistent across all environments. Once dockerized, it will run the same way on your laptop, your colleague's machine, and in production!
