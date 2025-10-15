#!/bin/bash

# NYC Taxi Analysis - Complete Project Setup Script
# This script sets up the entire project environment

echo "=========================================="
echo "NYC Taxi Analysis - Project Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "README.md" ]; then
    print_error "Please run this script from the project root directory (nyc-taxi-analysis/)"
    exit 1
fi

print_step "1. Checking system requirements..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    POSTGRES_VERSION=$(psql --version | cut -d " " -f 3)
    print_status "PostgreSQL found: $POSTGRES_VERSION"
else
    print_warning "PostgreSQL not found. Please install PostgreSQL 12+"
    echo "Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "macOS: brew install postgresql"
    echo "Continue after installing PostgreSQL..."
    read -p "Press Enter to continue after installing PostgreSQL..."
fi

print_step "2. Setting up Python environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python packages
print_status "Installing Python packages..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Failed to install Python packages"
    exit 1
fi

print_step "3. Database setup..."

# Check if train.csv exists
if [ ! -f "train.csv" ]; then
    if [ -f "../train.csv" ]; then
        print_status "Copying train.csv to project directory..."
        cp ../train.csv .
    else
        print_error "train.csv not found. Please ensure the dataset is available."
        print_warning "Expected location: ./train.csv or ../train.csv"
        exit 1
    fi
fi

# Database configuration
DB_NAME="nyc_taxi_db"
DB_USER="postgres"
DB_PASSWORD="Tresor26"

print_status "Setting up PostgreSQL database..."

# Create database and user (requires sudo access to postgres)
print_warning "The following commands require PostgreSQL admin access:"
echo "If prompted for password, enter your system password or PostgreSQL admin password"

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database may already exist"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;" 2>/dev/null

# Test database connection
print_status "Testing database connection..."
export PGPASSWORD=$DB_PASSWORD
if psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
    print_status "Database connection successful"
else
    print_error "Database connection failed"
    print_warning "Please check PostgreSQL installation and credentials"
    print_warning "You may need to edit pg_hba.conf to allow local connections"
    exit 1
fi

# Initialize database schema
print_status "Initializing database schema..."
psql -h localhost -U $DB_USER -d $DB_NAME -f database/schema.sql

if [ $? -eq 0 ]; then
    print_status "Database schema created successfully"
else
    print_error "Failed to create database schema"
    exit 1
fi

# Create indexes
print_status "Creating database indexes..."
psql -h localhost -U $DB_USER -d $DB_NAME -f database/indexes.sql

if [ $? -eq 0 ]; then
    print_status "Database indexes created successfully"
else
    print_error "Failed to create database indexes"
    exit 1
fi

print_step "4. Data processing pipeline..."

# Update backend configuration with database credentials
print_status "Updating backend configuration..."
cat > backend/.env << EOF
FLASK_ENV=development
FLASK_APP=app.py
DB_HOST=localhost
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432
EOF

# Create data directory if it doesn't exist
mkdir -p data_processing/data

# Move to data processing directory
cd data_processing

# Run data cleaning
print_status "Running data cleaning pipeline..."
print_warning "This may take several minutes for large datasets..."
python data_cleaner.py

if [ $? -ne 0 ]; then
    print_error "Data cleaning failed"
    exit 1
fi

# Run feature engineering
print_status "Running feature engineering..."
python feature_engineering.py

if [ $? -ne 0 ]; then
    print_error "Feature engineering failed"
    exit 1
fi

# Load data into database
print_status "Loading data into database..."
print_warning "This may take 10-15 minutes for large datasets..."
python data_loader.py

if [ $? -ne 0 ]; then
    print_error "Data loading failed"
    exit 1
fi

# Return to project root
cd ..

print_step "5. Testing setup..."

# Test backend API
print_status "Testing backend API..."
cd backend
python -c "
from app import create_app
app = create_app()
with app.app_context():
    print('Backend configuration successful')
"

if [ $? -eq 0 ]; then
    print_status "Backend test passed"
else
    print_error "Backend test failed"
    exit 1
fi

cd ..

print_step "6. Creating startup scripts..."

# Create backend startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "Starting NYC Taxi Analysis Backend..."
cd backend
source ../venv/bin/activate
export FLASK_ENV=development
export FLASK_APP=app.py
python app.py
EOF

chmod +x start_backend.sh

# Create frontend startup script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
echo "Starting NYC Taxi Analysis Frontend..."
cd frontend
echo "Frontend server starting on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
python3 -m http.server 8000
EOF

chmod +x start_frontend.sh

# Create combined startup script
cat > start_full_application.sh << 'EOF'
#!/bin/bash
echo "Starting Full NYC Taxi Analysis Application..."

# Start backend in background
echo "Starting backend server..."
./start_backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start frontend in background
echo "Starting frontend server..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "NYC Taxi Analysis Application Started!"
echo "=========================================="
echo "Backend API: http://localhost:5000"
echo "Frontend Dashboard: http://localhost:8000"
echo "Press Ctrl+C to stop both servers"
echo "=========================================="

# Wait for interrupt
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF

chmod +x start_full_application.sh

print_step "7. Generating project summary..."

# Create project status file
cat > PROJECT_STATUS.md << EOF
# NYC Taxi Analysis - Project Status

## Setup Completed Successfully ✅

**Setup Date:** $(date)
**Database:** $DB_NAME
**Records Processed:** $(psql -h localhost -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM trips;" 2>/dev/null | xargs)

## Quick Start

### Start Full Application:
\`\`\`bash
./start_full_application.sh
\`\`\`

### Start Components Individually:
\`\`\`bash
# Backend only
./start_backend.sh

# Frontend only (in another terminal)
./start_frontend.sh
\`\`\`

## Application URLs
- **Dashboard:** http://localhost:8000
- **API:** http://localhost:5000
- **API Health:** http://localhost:5000/api/health

## Key Features Available
- ✅ Interactive trip data filtering
- ✅ Real-time statistics dashboard
- ✅ Advanced data visualizations
- ✅ Custom algorithm implementations
- ✅ Comprehensive data insights
- ✅ Data export functionality

## Database Statistics
- **Total Trips:** $(psql -h localhost -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM trips;" 2>/dev/null | xargs)
- **Valid Trips:** $(psql -h localhost -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM trips WHERE is_valid = true;" 2>/dev/null | xargs)
- **Date Range:** $(psql -h localhost -U $DB_USER -d $DB_NAME -t -c "SELECT MIN(pickup_datetime)::date || ' to ' || MAX(pickup_datetime)::date FROM trips;" 2>/dev/null | xargs)

## Project Structure
\`\`\`
nyc-taxi-analysis/
├── backend/          # Flask API server
├── frontend/         # Web dashboard
├── data_processing/  # ETL pipeline
├── database/         # Schema and queries
├── documentation/    # Technical docs
└── requirements.txt  # Python dependencies
\`\`\`

## Troubleshooting
If you encounter issues:
1. Check that PostgreSQL is running
2. Verify database credentials in backend/.env
3. Ensure all Python packages are installed: \`pip install -r requirements.txt\`
4. Check the logs in the terminal for specific error messages

## Next Steps
1. Open http://localhost:8000 in your browser
2. Explore the interactive dashboard
3. Try different filters and visualizations
4. Review the technical documentation in \`documentation/technical_report.md\`
EOF

echo ""
echo "=========================================="
print_status "Setup completed successfully!"
echo "=========================================="
echo ""
print_status "Project summary saved to PROJECT_STATUS.md"
echo ""
print_step "To start the application:"
echo "  ./start_full_application.sh"
echo ""
print_step "To start components individually:"
echo "  Backend:  ./start_backend.sh"
echo "  Frontend: ./start_frontend.sh"
echo ""
print_step "Access URLs:"
echo "  Dashboard: http://localhost:8000"
echo "  API:       http://localhost:5000"
echo ""
print_warning "Make sure to activate the virtual environment when running manually:"
echo "  source venv/bin/activate"
echo ""
echo "=========================================="
print_status "Setup completed! Ready to analyze NYC taxi data!"
echo "=========================================="
