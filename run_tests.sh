#!/bin/bash

# Comprehensive Test Runner for Trading Platform
# Runs both backend and frontend tests with coverage reports

set -e  # Exit on any error

echo "🧪 Starting Comprehensive Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create test results directory
TEST_RESULTS_DIR="test_results"
mkdir -p $TEST_RESULTS_DIR

# Backend Tests
print_status "Running Backend Tests..."
echo "------------------------"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if not installed
print_status "Installing test dependencies..."
pip install pytest-cov pytest-mock > /dev/null 2>&1

# Run backend tests with coverage
print_status "Executing backend test suite..."
pytest --cov=. --cov-report=html:../test_results/backend_coverage --cov-report=term-missing --junitxml=../test_results/backend_junit.xml -v

BACKEND_EXIT_CODE=$?

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    print_success "Backend tests passed!"
else
    print_error "Backend tests failed with exit code $BACKEND_EXIT_CODE"
fi

# Code quality checks
print_status "Running code quality checks..."
echo "black --check ." && black --check . || print_warning "Code formatting issues found (run 'black .' to fix)"
echo "isort --check-only ." && isort --check-only . || print_warning "Import sorting issues found (run 'isort .' to fix)"
echo "flake8 ." && flake8 . || print_warning "Code style issues found"

cd ..

# Frontend Tests
print_status "Running Frontend Tests..."
echo "-------------------------"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_error "Node modules not found. Please run: npm install"
    exit 1
fi

# Run frontend tests with coverage
print_status "Executing frontend test suite..."
CI=true npm run test:coverage 2>&1 | tee ../test_results/frontend_test_output.log

FRONTEND_EXIT_CODE=${PIPESTATUS[0]}

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    print_success "Frontend tests passed!"
else
    print_error "Frontend tests failed with exit code $FRONTEND_EXIT_CODE"
fi

# Move coverage report
if [ -d "coverage" ]; then
    mv coverage ../test_results/frontend_coverage
fi

cd ..

# Integration Tests (if API is running)
print_status "Checking for running backend..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    print_status "Backend detected, running integration tests..."
    
    # Basic API integration tests
    cd backend
    python -c "
import requests
import sys

def test_api_health():
    try:
        response = requests.get('http://localhost:8000/api/health')
        assert response.status_code == 200
        print('✓ API health check passed')
        return True
    except Exception as e:
        print(f'✗ API health check failed: {e}')
        return False

def test_api_endpoints():
    endpoints = [
        '/api/trades',
        '/api/sentiment',
        '/api/performance',
        '/api/stocks'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            if response.status_code == 200:
                print(f'✓ {endpoint} accessible')
            else:
                print(f'✗ {endpoint} returned {response.status_code}')
        except Exception as e:
            print(f'✗ {endpoint} failed: {e}')

if __name__ == '__main__':
    print('Running API integration tests...')
    test_api_health()
    test_api_endpoints()
    print('Integration tests completed')
"
    cd ..
else
    print_warning "Backend not running, skipping integration tests"
    print_warning "To run integration tests, start the backend with: cd backend && python main.py"
fi

# Test Results Summary
echo ""
echo "📊 Test Results Summary"
echo "======================="

# Backend Results
if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    print_success "Backend Tests: PASSED"
else
    print_error "Backend Tests: FAILED"
fi

# Frontend Results  
if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    print_success "Frontend Tests: PASSED"
else
    print_error "Frontend Tests: FAILED"
fi

# Coverage Reports
echo ""
echo "📈 Coverage Reports:"
echo "-------------------"
echo "Backend Coverage:  test_results/backend_coverage/index.html"
echo "Frontend Coverage: test_results/frontend_coverage/lcov-report/index.html"
echo "JUnit XML:         test_results/backend_junit.xml"

# Overall Status
OVERALL_EXIT_CODE=$((BACKEND_EXIT_CODE + FRONTEND_EXIT_CODE))

if [ $OVERALL_EXIT_CODE -eq 0 ]; then
    print_success "🎉 All tests passed successfully!"
    echo ""
    echo "Next steps:"
    echo "- Review coverage reports to identify untested code"
    echo "- Run integration tests with backend running"
    echo "- Consider adding more edge case tests"
else
    print_error "❌ Some tests failed. Please review the output above."
    echo ""
    echo "Debugging tips:"
    echo "- Check test_results/ directory for detailed reports"
    echo "- Run individual test suites for more focused debugging"
    echo "- Ensure all dependencies are installed"
fi

echo ""
echo "Test run completed at: $(date)"

exit $OVERALL_EXIT_CODE