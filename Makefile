.PHONY: dev dev-frontend dev-backend install install-frontend install-backend help

# Default target
help:
	@echo "Available targets:"
	@echo "  make install        - Install all dependencies (frontend and backend)"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make dev           - Start both frontend and backend"
	@echo "  make dev-frontend  - Start only the frontend"
	@echo "  make dev-backend   - Start only the backend"
	@echo "  make help          - Show this help message"

# Install all dependencies
install: install-backend install-frontend
	@echo "All dependencies installed!"

# Install frontend dependencies
install-frontend:
	@echo "Installing frontend dependencies..."
	@cd frontend-rayan && npm install

# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	@cd backend && uv sync || pip install -e .

# Check if frontend dependencies are installed
check-frontend:
	@test -d frontend/node_modules || (echo "Frontend dependencies not installed. Run 'make install-frontend' first." && exit 1)

# Start both frontend and backend
dev: check-frontend
	@echo "Starting both frontend and backend..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@trap 'kill 0' INT TERM EXIT; \
	(cd backend && source .venv/bin/activate &&  cd .. && uvicorn backend.api.main:app --reload --port 8000) & \
	(cd frontend-rayan && npm run dev) & \
	wait

# Start only the frontend
dev-frontend: check-frontend
	@echo "Starting frontend..."
	@echo "Frontend will run on http://localhost:3000"
	@cd frontend-rayan && npm run dev

# Start only the backend
dev-backend:
	@echo "Starting backend..."
	@echo "Backend will run on http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	@cd backend && source .venv/bin/activate &&  cd .. && uvicorn backend.api.main:app --reload --port 8000

