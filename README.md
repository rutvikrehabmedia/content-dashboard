# Search & Scrape Dashboard

A full-stack application for managing search operations and web scraping tasks with real-time monitoring.

## Features

- Advanced search functionality with customizable parameters
- Bulk search and scraping capabilities
- Real-time progress monitoring
- Export functionality (JSON/CSV)
- Whitelist/Blacklist management
- Responsive dashboard interface

## Tech Stack

### Backend
- FastAPI (Python)
- MongoDB
- Motor (Async MongoDB driver)
- BeautifulSoup4 (Web scraping)
- Pydantic (Data validation)

### Frontend
- React
- TypeScript
- Material-UI
- React Router
- Axios

## Setup & Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB 4.4+
- Docker & Docker Compose (optional)

### Local Development Setup

1. Clone the repository:

```
bash
git clone <repository-url>
cd search-scrape-dashboard

```


2. Backend Setup:

```
bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

3. Frontend Setup:

```
bash
cd frontend
npm install
cp .env.example .env # Update with your settings
npm start
```


### Docker Setup

1. Build and run using Docker Compose:

```
bash
docker-compose up --build
```


## Production Deployment

### Using Docker (Recommended)

1. Update environment variables in `.env` files
2. Build and deploy using Docker Compose:

```
bash
docker-compose -f docker-compose.prod.yml up -d
```


### Manual Deployment

1. Backend Deployment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

2. Frontend Deployment:
   ```bash
   cd frontend
   npm install
   npm run build
   # Serve the build directory using Nginx or other static file server
   ```

3. MongoDB Setup:
   - Set up MongoDB instance with authentication
   - Configure backups
   - Set up monitoring

### Environment Variables

Backend (.env):

```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=search_dashboard
API_KEY=your-api-key
CORS_ORIGINS=http://localhost:3000
MAX_WORKERS=4
LOG_LEVEL=info
```

Frontend (.env):

```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key
```


## API Documentation

The API documentation is available at the following endpoints:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
