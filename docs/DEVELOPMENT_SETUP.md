# Development Environment Setup Guide

This guide provides step-by-step instructions for setting up the Trading Platform development environment on your local machine.

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Docker & Docker Compose** ([Download](https://www.docker.com/get-started))
- **Git** ([Download](https://git-scm.com/downloads))

### Recommended Tools

- **VS Code** with Python and React extensions
- **Postman** or similar API testing tool
- **PostgreSQL client** (optional, for database inspection)

## Step 1: Repository Setup

### 1.1 Clone Repository

```bash
git clone https://github.com/your-username/trading-platform.git
cd trading-platform
```

### 1.2 Verify Repository Structure

```bash
ls -la
# Should show: backend/, frontend/, terraform/, docs/, etc.
```

## Step 2: Backend Setup

### 2.1 Navigate to Backend Directory

```bash
cd backend
```

### 2.2 Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Create Backend Environment File

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```bash
# Database
DATABASE_URL=sqlite:///data/trading.db

# API Keys (get from respective services)
NEWS_API_KEY=your_news_api_key_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Security
SECRET_KEY=your-secret-key-here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# CORS (for local development)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 2.5 Initialize Database

```bash
# Run database migrations
python -c "from database import init_db; init_db()"

# Or use the initialization script if available
python init_db.py
```

### 2.6 Test Backend Setup

```bash
# Start the backend server
python main.py

# Should see output like:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

In another terminal, test the API:
```bash
curl http://localhost:8000/
# Should return: {"status":"healthy","google_client_id_configured":true}
```

## Step 3: Frontend Setup

### 3.1 Navigate to Frontend Directory

```bash
cd ../frontend  # From backend directory
# OR
cd frontend     # From root directory
```

### 3.2 Install Node.js Dependencies

```bash
npm install
```

### 3.3 Create Frontend Environment File

```bash
cp .env.example .env.local
```

Edit `.env.local` file:
```bash
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# Google OAuth Client ID (same as backend)
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

### 3.4 Test Frontend Setup

```bash
# Start the frontend development server
npm start

# Should open browser at http://localhost:3000
```

## Step 4: Google OAuth Setup

Follow the [Google OAuth Setup Guide](./GOOGLE_OAUTH_SETUP.md) to configure authentication.

**Quick Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth client ID
3. Add `http://localhost:3000` to authorized origins
4. Copy client ID to both backend and frontend `.env` files

## Step 5: Development Workflow

### 5.1 Starting Development Environment

**Option A: Manual Start** (Recommended for debugging)
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py

# Terminal 2: Frontend
cd frontend
npm start
```

**Option B: Docker Compose** (Alternative)
```bash
# From root directory
docker-compose up --build
```

### 5.2 Verify Everything Works

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/
   ```

2. **Frontend Access**:
   - Open http://localhost:3000
   - Should see Trading Platform login page

3. **Google OAuth**:
   - Click "Sign in with Google"
   - Should open Google OAuth flow

4. **API Integration**:
   - After login, check browser dev tools
   - Should see successful API calls to backend

## Step 6: Development Tools

### 6.1 Running Tests

**Backend Tests**:
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend Tests**:
```bash
cd frontend
npm test
```

**Run All Tests**:
```bash
# From root directory
./run_tests.sh
```

### 6.2 Code Linting

**Backend Linting**:
```bash
cd backend
pip install black flake8 isort
black .
flake8 .
isort .
```

**Frontend Linting**:
```bash
cd frontend
npm run lint
npm run lint:fix  # Auto-fix issues
```

### 6.3 Database Management

**View Database**:
```bash
# SQLite browser or command line
sqlite3 backend/data/trading.db
.tables
.schema stocks
```

**Reset Database**:
```bash
cd backend
rm data/trading.db
python -c "from database import init_db; init_db()"
```

## Common Development Tasks

### Adding a New API Endpoint

1. Add route in `backend/main.py`
2. Add schema in `backend/schemas.py`
3. Update API documentation
4. Add tests in `backend/tests/`
5. Update frontend API client if needed

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Add to relevant page in `frontend/src/pages/`
3. Update routing if needed
4. Add tests in `__tests__/` directory

### Environment Variables

- **Backend**: Add to `backend/.env` and `backend/config.py`
- **Frontend**: Add to `frontend/.env.local` (must start with `REACT_APP_`)
- **Production**: Update GitHub secrets and EC2 environment

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.9+

# Check virtual environment
which python  # Should point to venv

# Check dependencies
pip list | grep fastapi
```

#### Frontend Won't Start
```bash
# Check Node version
node --version  # Should be 18+

# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Database Issues
```bash
# Check database file exists
ls -la backend/data/

# Recreate database
rm backend/data/trading.db
cd backend && python -c "from database import init_db; init_db()"
```

#### CORS Errors
- Verify backend CORS_ORIGINS includes `http://localhost:3000`
- Check frontend is making requests to correct backend URL
- Restart both backend and frontend after changes

#### Authentication Issues
- Verify Google Client ID is set in both environments
- Check Google Cloud Console authorized origins
- Clear browser cache and cookies

### Port Conflicts

If default ports are in use:

**Backend** (change from 8000):
```bash
# In backend/.env
PORT=8001

# Start with custom port
uvicorn main:app --port 8001
```

**Frontend** (change from 3000):
```bash
# Set environment variable
PORT=3001 npm start
```

### Getting Help

1. Check existing documentation in `docs/`
2. Review [Troubleshooting Guide](./TROUBLESHOOTING.md)
3. Check GitHub issues for similar problems
4. Use browser dev tools for frontend issues
5. Check backend logs for API issues

## Next Steps

After successful setup:

1. Read [API Documentation](../backend/docs/api.md)
2. Review [Frontend Architecture](../frontend/README.md)
3. Check [Deployment Guide](./DEPLOYMENT_GUIDE.md) for production setup
4. Explore [SaaS Operations Guide](./SAAS_OPERATIONS.md) for advanced features

## Development Best Practices

- Always use virtual environments for Python
- Keep dependencies up to date
- Write tests for new features
- Use consistent code formatting
- Commit frequently with descriptive messages
- Test Google OAuth flow before deploying
- Monitor backend logs during development

Happy coding! 🚀