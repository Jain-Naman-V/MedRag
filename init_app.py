#!/usr/bin/env python3
"""
Initialize the MedRAG application.

This script ensures all necessary directories exist and have the correct permissions.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define directories to create
REQUIRED_DIRS = [
    "data/uploads",
    "data/vector_store",
    "static",
    "templates",
    "logs"
]

def setup_directories(base_dir: str) -> Tuple[bool, List[str]]:
    """
    Create required directories if they don't exist.
    
    Args:
        base_dir: Base directory path
        
    Returns:
        Tuple of (success, messages)
    """
    base_path = Path(base_dir)
    messages = []
    success = True
    
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            messages.append(f"✓ Created directory: {full_path}")
        except Exception as e:
            success = False
            messages.append(f"✗ Failed to create {full_path}: {str(e)}")
    
    return success, messages

def check_environment() -> Tuple[bool, List[str]]:
    """
    Check if required environment variables are set.
    
    Returns:
        Tuple of (success, messages)
    """
    messages = []
    success = True
    
    # Check for required environment variables
    required_vars = [
        # Add any required environment variables here
        # Example: "OPENAI_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            success = False
            messages.append(f"✗ Required environment variable not set: {var}")
    
    if success:
        messages.append("✓ All required environment variables are set")
    
    return success, messages

def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if required Python packages are installed.
    
    Returns:
        Tuple of (success, messages)
    """
    messages = []
    success = True
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "python-multipart",
        "PyMuPDF",
        "python-dotenv",
        "openai",
        "langchain",
        "faiss-cpu",
        "chromadb",
        "pydantic",
        "python-jose",
        "passlib",
        "weasyprint",
        "pytest",
        "httpx"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.split(">=")[0].split("[")[0])
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        success = False
        messages.append("✗ Missing required Python packages:")
        for pkg in missing_packages:
            messages.append(f"   - {pkg}")
        messages.append("\nInstall them using: pip install -r requirements.txt")
    else:
        messages.append("✓ All required Python packages are installed")
    
    return success, messages

def main() -> int:
    """Main entry point for the initialization script."""
    script_dir = Path(__file__).parent.absolute()
    
    print("\n=== MedRAG Application Initialization ===\n")
    
    # Setup directories
    print("1. Setting up directories...")
    dir_success, dir_messages = setup_directories(script_dir)
    for msg in dir_messages:
        print(f"   {msg}")
    
    # Check environment
    print("\n2. Checking environment...")
    env_success, env_messages = check_environment()
    for msg in env_messages:
        print(f"   {msg}")
    
    # Check dependencies
    print("\n3. Checking dependencies...")
    deps_success, deps_messages = check_dependencies()
    for msg in deps_messages:
        print(f"   {msg}")
    
    # Print summary
    print("\n=== Initialization Summary ===")
    print(f"Directories: {'✓' if dir_success else '✗'}")
    print(f"Environment: {'✓' if env_success else '✗'}")
    print(f"Dependencies: {'✓' if deps_success else '✗'}")
    
    if all([dir_success, env_success, deps_success]):
        print("\n✅ Initialization completed successfully!")
        print("\nTo start the application, run:")
        print("   uvicorn app.main:app --reload")
        print("\nThen open your browser to: http://localhost:8000")
        return 0
    else:
        print("\n❌ Initialization failed. Please check the messages above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
