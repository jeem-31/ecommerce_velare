# Docker Build Issue on Windows

## Problem
When building the Docker image on Windows, you may encounter:
```
ERROR: failed to solve: invalid file request app.py
```

## Root Cause
This is a known issue with Docker Desktop on Windows related to:
1. File path handling between Windows and Linux containers
2. Build context transfer issues
3. Symlinks or special characters in file paths

## Workarounds

### Option 1: Use WSL2 (Recommended)
1. Install WSL2: https://docs.microsoft.com/en-us/windows/wsl/install
2. Move your project to WSL2 filesystem
3. Run Docker commands from WSL2 terminal

```bash
# In WSL2 terminal
cd /mnt/c/Users/justine/Documents/Velare\ Ecommerce/
docker-compose up --build
```

### Option 2: Simplify Dockerfile
Try copying files in smaller chunks:

```dockerfile
# Copy only necessary files first
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY app.py .
COPY blueprints/ ./blueprints/
COPY database/ ./database/
COPY static/ ./static/
COPY templates/ ./templates/
COPY utils/ ./utils/
```

### Option 3: Use Docker Buildx
```bash
docker buildx create --use
docker buildx build --platform linux/amd64 -t velare-app .
```

### Option 4: Run Without Docker (Development)
For local development, you can run directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## Alternative: Deploy to Cloud
Instead of running Docker locally on Windows, deploy directly to:
- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo
- **Render**: Connect GitHub repo
- **DigitalOcean App Platform**: Connect GitHub repo

These platforms will build the Docker image in their Linux environment.

## References
- https://github.com/docker/for-win/issues/8336
- https://docs.docker.com/desktop/windows/wsl/
