# Invoice AI 

A comprehensive invoice management system powered by AI that combines OCR (Optical Character Recognition) with an intelligent chatbot interface for seamless invoice processing and querying.

## Features

### AI-Powered Invoice Processing
- **Smart OCR**: Extract structured data from invoice images (JPG, PNG, WebP) and PDFs using Google Gemini AI
- **Automatic Categorization**: Intelligently categorizes invoices (Hardware & Construction, Utilities, Security Services, Office Supplies, Technology, Logistics, Professional Services, Maintenance, Other)
- **Data Validation**: Robust parsing of invoice numbers, vendor names, dates, amounts, and itemized details

### Intelligent Chatbot
- **Natural Language Queries**: Ask questions about your invoices in plain English
- **Invoice Analytics**: Get insights on total amounts, unpaid invoices, vendor analysis, and more
- **Contextual Responses**: AI understands your specific invoice data and provides relevant answers
- **Markdown Tables**: Clean, formatted responses for invoice listings and summaries

### Secure Authentication
- **JWT-based Authentication**: Secure token-based user authentication
- **Password Encryption**: Industry-standard bcrypt password hashing
- **User Isolation**: Each user can only access their own invoices

### Invoice Management
- **Upload & Process**: Drag-and-drop invoice upload with instant AI processing
- **Status Tracking**: Monitor invoice status (Paid/Unpaid)
- **Date Parsing**: Flexible date format recognition and standardization
- **Vendor Management**: Automatic vendor extraction and categorization

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM)
- **SQLite**: Lightweight database for invoice and user data
- **Google Gemini AI**: Advanced AI model for OCR and data extraction
- **Groq**: High-performance inference for chatbot responses
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **React**: Modern JavaScript library for building user interfaces
- **Create React App**: Streamlined React development setup
- **Service Worker**: Progressive Web App (PWA) capabilities

### AI & Machine Learning
- **Google Gemini 1.5 Flash**: State-of-the-art multimodal AI for document processing
- **Llama 3.1**: Advanced language model for conversational AI via Groq

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- Google AI API Key (for Gemini)
- Groq API Key (for chatbot)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Wasifzf/Inv_AI.git
cd Inv_AI
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_google_ai_api_key_here
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
ADMIN_SECRET=your_admin_secret_here
```

### 4. Database Initialization
The database will be automatically created when you first run the application with sample users:
- Username: `user1`, Password: `password1`
- Username: `user2`, Password: `password2`

### 5. Start the Backend
```bash
uvicorn main:main --reload
```
The API will be available at `http://localhost:8000`

### 6. Frontend Setup
```bash
cd frontend
npm install
npm start
```
The web application will be available at `http://localhost:3000`

## API Documentation

### Authentication Endpoints
- `POST /login` - User authentication
- `POST /debug/reset-password` - Admin password reset (debug only)

### Invoice Management
- `GET /invoices/` - List user's invoices
- `POST /upload-invoice/` - Upload and process invoice
- `POST /chatbot/` - Query invoices using natural language

### Debug Endpoints
- `GET /debug/users` - List all users (debug only)
- `GET /debug/db-schema` - Database schema information

## Configuration

### Supported File Types
- **Images**: JPG, JPEG, PNG, WebP
- **Documents**: PDF

### AI Models
- **OCR Model**: `gemini-1.5-flash-001` (configurable via `GEMINI_MODEL_ID`)
- **Chat Model**: `llama-3.1-70b-versatile`

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key for Gemini | Required |
| `GROQ_API_KEY` | Groq API key for chatbot | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `supersecretkey` |
| `ADMIN_SECRET` | Admin secret for debug endpoints | `dev-secret` |
| `GEMINI_MODEL_ID` | Gemini model identifier | `gemini-1.5-flash-001` |

## 💡 Usage Examples

### Uploading an Invoice
1. Navigate to the upload section
2. Select an invoice image or PDF
3. The AI will automatically extract:
   - Invoice number
   - Vendor information
   - Date and due date
   - Line items and amounts
   - Appropriate category

### Chatbot Queries
- "How many invoices do I have?"
- "What's my total outstanding amount?"
- "Show me all unpaid invoices"
- "List invoices from last month"
- "What's the total amount from Acme Corp?"

## Project Structure

```
├── main.py              # FastAPI application entry point
├── database.py          # Database models and configuration
├── models.py            # Pydantic data models
├── ocr.py              # Google Gemini AI integration
├── chatbot.py          # Groq chatbot implementation
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── invoices.db        # SQLite database (auto-generated)
└── frontend/          # React frontend application
    ├── src/
    │   ├── components/
    │   │   ├── Chat.js
    │   │   ├── FileUpload.js
    │   │   ├── Invoices.js
    │   │   └── Login.js
    │   ├── App.js
    │   └── api.js
    └── public/
```
