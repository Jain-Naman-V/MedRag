# MedRAG - Document Analysis and Summarization System

MedRAG is a powerful document analysis and summarization system designed to extract valuable information from medical, legal, and academic PDF documents. The system uses Retrieval-Augmented Generation (RAG) to provide accurate and contextually relevant summaries.

## Features

- **Document Upload**: Upload PDF documents for processing
- **Text Extraction**: Extract text and metadata from PDFs
- **Document Analysis**: Analyze document structure and content
- **AI-Powered Summarization**: Generate concise and accurate summaries
- **Structured Data Extraction**: Extract key information like patient details, dates, and more
- **Vector Search**: Find similar documents using semantic search

## Tech Stack

- **Frontend**: React.js + Tailwind CSS
- **Backend**: Python (FastAPI)
- **PDF Processing**: PyMuPDF (fitz), pdfplumber
- **Embeddings**: OpenAI Embeddings / HuggingFace
- **Vector Store**: FAISS / ChromaDB
- **LLM**: OpenAI GPT-4 / Anthropic Claude / Local Models
- **Deployment**: Docker, FastAPI

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) Docker and Docker Compose

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medrag
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the application**
   ```bash
   python init_app.py
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the application**
   Open your browser and go to `http://localhost:8000`

## 🚀 Free Deployment

### Option 1: Railway (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Create new project → Deploy from GitHub repo
   - Select your repository
   - Deploy automatically

3. **Your app will be live at**: `https://your-app-name.railway.app`

### Option 2: Render

1. **Push to GitHub** (same as above)

2. **Deploy to Render**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub
   - Create new Web Service
   - Connect your repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Your app will be live at**: `https://your-app-name.onrender.com`

### 🔑 API Key Configuration

**No environment variables needed!** Users configure their own OpenAI API keys through the web interface:

1. Visit your deployed app
2. Enter your OpenAI API key on the home page
3. Click "Test & Save API Key"
4. Start using all AI features!

This makes deployment super easy - no backend configuration required!

## Usage

### Running the Application

1. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

2. **Access the API documentation**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### API Endpoints

- `POST /api/documents/upload` - Upload a PDF document
- `GET /api/documents/{document_id}` - Get document details
- `GET /api/documents/{document_id}/text` - Get document text
- `POST /api/summaries/generate` - Generate a summary
- `GET /api/summaries/{summary_id}` - Get a summary

### Using Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - API: `http://localhost:8000`
   - Frontend: `http://localhost:3000` (if frontend is set up)

## Project Structure

```
medrag/
├── app/                      # Main application package
│   ├── api/                  # API routes
│   ├── core/                 # Core functionality
│   ├── models/               # Database models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   ├── __init__.py
│   └── main.py               # FastAPI application
├── data/                     # Data storage
│   ├── uploads/              # Uploaded documents
│   └── vector_store/         # Vector embeddings
├── static/                   # Static files
├── templates/                # HTML templates
├── tests/                    # Test files
├── .env                      # Environment variables
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt          # Python dependencies
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Application environment (development, production) | `development` |
| `DEBUG` | Enable debug mode | `True` in development |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `MAX_UPLOAD_SIZE` | Maximum file upload size in bytes | `10485760` (10MB) |
| `ALLOWED_EXTENSIONS` | Allowed file extensions | `pdf` |
| `UPLOAD_FOLDER` | Path to store uploaded files | `./data/uploads` |
| `VECTOR_STORE_PATH` | Path to store vector embeddings | `./data/vector_store` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `HUGGINGFACEHUB_API_TOKEN` | HuggingFace Hub API token | - |

## Development

### Setting Up for Development

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Run linter**
   ```bash
   flake8 app tests
   ```

4. **Run formatter**
   ```bash
   black app tests
   ```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [LangChain](https://python.langchain.com/) - Framework for LLM applications
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF text extraction
- [FAISS](https://github.com/facebookresearch/faiss) - Efficient similarity search

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
