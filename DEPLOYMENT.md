# MedRAG Deployment Guide

This guide will help you deploy your MedRAG application to GitHub and various cloud platforms.

## 🚀 Quick Start

### 1. Local Development Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd medrag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your settings

# Initialize the application
python init_app.py

# Run the application
uvicorn app.main:app --reload
```

### 2. GitHub Repository Setup

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: MedRAG application"

# Add remote repository
git remote add origin https://github.com/yourusername/medrag.git

# Push to GitHub
git push -u origin main
```

## 📋 Pre-deployment Checklist

- [ ] ✅ All sensitive data is in `.env` file (not committed)
- [ ] ✅ API keys are properly secured
- [ ] ✅ Database is properly configured
- [ ] ✅ All dependencies are in `requirements.txt`
- [ ] ✅ Docker configuration is ready (if using containers)
- [ ] ✅ Environment variables are documented

## 🌐 Deployment Options

### Option 1: Railway (Recommended for beginners)

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub repository**
3. **Add environment variables** in Railway dashboard:
   ```
   APP_NAME=MedRAG
   APP_ENV=production
   DEBUG=False
   HOST=0.0.0.0
   PORT=8000
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secret_key
   ```
4. **Deploy** - Railway will automatically build and deploy

### Option 2: Render

1. **Sign up** at [render.com](https://render.com)
2. **Create a new Web Service**
3. **Connect your GitHub repository**
4. **Configure the service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Add environment variables**
6. **Deploy**

### Option 3: Heroku

1. **Install Heroku CLI**
2. **Create Heroku app**:
   ```bash
   heroku create your-medrag-app
   ```
3. **Add buildpacks**:
   ```bash
   heroku buildpacks:add heroku/python
   ```
4. **Set environment variables**:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set SECRET_KEY=your_secret
   ```
5. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 4: DigitalOcean App Platform

1. **Sign up** at [digitalocean.com](https://digitalocean.com)
2. **Create a new App**
3. **Connect your GitHub repository**
4. **Configure the app**:
   - **Source**: GitHub repository
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Add environment variables**
6. **Deploy**

## 🔧 Environment Variables

Create a `.env` file with the following variables:

```env
# Application Settings
APP_NAME=MedRAG
APP_ENV=production
DEBUG=False

# Server Settings
HOST=0.0.0.0
PORT=8000

# File Upload Settings
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=pdf
UPLOAD_FOLDER=./data/uploads
VECTOR_STORE_PATH=./data/vector_store

# OpenAI Settings
OPENAI_API_KEY=your_openai_api_key_here

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🐳 Docker Deployment

### Build and run with Docker:

```bash
# Build the image
docker build -t medrag .

# Run the container
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key medrag
```

### Using Docker Compose:

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## 🔒 Security Considerations

1. **Never commit sensitive data**:
   - API keys
   - Database credentials
   - Secret keys

2. **Use environment variables** for all sensitive data

3. **Enable HTTPS** in production

4. **Set up proper CORS** for your domain

5. **Use strong secret keys**

## 📊 Monitoring and Logging

### Add logging configuration:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

## 🚨 Troubleshooting

### Common Issues:

1. **Port already in use**:
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill the process
   kill -9 <PID>
   ```

2. **Database connection issues**:
   - Check database file permissions
   - Ensure data directory exists

3. **API key issues**:
   - Verify API key is valid
   - Check environment variable is set correctly

4. **Import errors**:
   - Ensure all dependencies are installed
   - Check Python version compatibility

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f app.log`
2. Verify environment variables
3. Test locally first
4. Check the deployment platform's documentation

## 🔄 Continuous Deployment

Set up GitHub Actions for automatic deployment:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Railway
      uses: railway/deploy@v1
      with:
        token: ${{ secrets.RAILWAY_TOKEN }}
```

Remember to add your deployment tokens as GitHub secrets! 