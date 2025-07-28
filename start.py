#!/usr/bin/env python3
"""
Start script for the MedRAG application.

This script initializes and starts the FastAPI application with proper logging
and configuration.
"""
import os
import sys
import logging
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Configure logging before importing app to ensure all logs are captured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# Reduce watchfiles logging noise
logging.getLogger('watchfiles').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def load_environment() -> bool:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info("Loaded environment variables from .env file")
        return True
    else:
        logger.warning("No .env file found. Using system environment variables.")
        return False

def check_required_vars() -> bool:
    """Check if required environment variables are set."""
    required_vars = [
        # Add any required environment variables here
        # Example: "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def create_required_directories() -> bool:
    """Create required directories if they don't exist."""
    required_dirs = [
        "data/uploads",
        "data/vector_store",
        "static",
        "templates",
        "logs"
    ]
    
    try:
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create required directories: {str(e)}")
        return False

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_environment()
    
    # Check required environment variables
    if not check_required_vars():
        sys.exit(1)
    
    # Create required directories
    if not create_required_directories():
        sys.exit(1)
    
    # Import the FastAPI app after environment is set up
    from app.main import app
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting MedRAG application on http://{host}:{port}")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="warning",  # Reduced from info to warning to minimize log output
        workers=1
    )

if __name__ == "__main__":
    main()
