 
# NYC Taxi Trip Analysis - Full Stack Application

## Overview
This is a comprehensive full-stack application for analyzing NYC Taxi Trip data, built as part of an enterprise-level urban mobility analysis project. The application processes ~1.45M taxi trip records, stores them in a relational database, and provides an interactive dashboard for exploring urban mobility patterns.

## Video Walkthrough
[Link to video demonstration will be added here]

## System Architecture
- **Frontend**: Interactive HTML/CSS/JavaScript dashboard
- **Backend**: Flask-based REST API with data processing pipeline
- **Database**: PostgreSQL with normalized schema and indexing
- **Data Processing**: Custom algorithms for cleaning, enrichment, and analysis

## Project Structure
```
nyc-taxi-analysis/
├── README.md
├── requirements.txt
├── setup.sh
├── backend/
│   ├── app.py                 # Flask application
│   ├── models.py              # Database models
│   ├── routes.py              # API endpoints
│   ├── config.py              # Configuration
│   └── utils.py               # Utility functions
├── frontend/
│   ├── index.html             # Main dashboard
│   ├── styles.css             # Styling
│   ├── app.js                 # Frontend logic
│   └── charts.js              # Visualization components
├── data_processing/
│   ├── data_cleaner.py        # Data cleaning pipeline
│   ├── feature_engineering.py # Derived features
│   ├── custom_algorithms.py   # Manual implementations
│   └── data_loader.py         # Database loading
├── database/
│   ├── schema.sql             # Database schema
│   ├── indexes.sql            # Database indexes
│   └── sample_queries.sql     # Example queries
└── documentation/
    └── technical_report.md    # Technical documentation
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (optional, for enhanced frontend features)

### Step 1: Clone and Setup Environment
```bash
cd /home/treasure/Documents/Taxi/nyc-taxi-analysis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Secure Configuration Setup
🔐 **Important**: This application uses environment variables for secure credential management.

**Option A: Automated Setup (Recommended)**
```bash
# Run the secure setup script
./setup_secure.sh
```

**Option B: Manual Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your actual database credentials
nano .env
```

### Step 3: Database Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database (replace 'your_password' with your actual password)
PGPASSWORD=your_password createdb -h localhost -U postgres nyc_taxi_db

# Initialize database schema
PGPASSWORD=your_password psql -h localhost -U postgres -d nyc_taxi_db -f database/schema.sql
PGPASSWORD=your_password psql -h localhost -U postgres -d nyc_taxi_db -f database/indexes.sql
```

### Step 4: Data Processing
```bash
# Copy the train.csv file to the project directory
cp ../train.csv data/

# Run data processing pipeline (make sure .env is configured)
cd data_processing
python data_cleaner.py
python feature_engineering.py
python data_loader.py
```

### Step 5: Start Backend Server
```bash
# Make sure your .env file is configured (see Step 2)
cd backend
python app.py
# The app will automatically load environment variables from .env
```

### Step 6: Launch Frontend
```bash
cd frontend
# Serve static files (using Python's built-in server)
python3 -m http.server 8000
```

### Step 7: Access Application
LINK to Dashboard:http://127.0.0.1:5500/frontend/index.html

## 🔒 Security Features

### Environment-Based Configuration
- **No Hardcoded Credentials**: All sensitive information stored in environment variables
- **Secure .env File**: Database passwords and API keys stored securely
- **Git Ignore Protection**: Sensitive files automatically excluded from version control

### Security Best Practices
- `.env` file has restricted permissions (600)
- Database passwords never stored in source code
- Configuration validation on application startup
- Secure secret key generation for Flask sessions

### Environment Variables Required
```bash
DB_HOST=localhost
DB_NAME=nyc_taxi_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
```

## Features
- **Data Cleaning**: Handles missing values, outliers, and invalid records
- **Feature Engineering**: Trip speed, idle time, fare efficiency metrics
- **Interactive Dashboard**: Filter by time, location, distance, fare
- **Real-time Visualizations**: Charts, maps, and statistical summaries
- **Custom Algorithms**: Manual implementations for sorting, filtering, and analysis

## API Endpoints
- `GET /api/trips` - Retrieve trip data with filters
- `GET /api/stats` - Get statistical summaries
- `GET /api/insights` - Get derived insights
- `GET /api/locations` - Get popular pickup/dropoff locations

## Technical Highlights
- Custom sorting and filtering algorithms (no pandas/numpy sort functions)
- Efficient database indexing for geographic and temporal queries
- Responsive design with dynamic data visualization
- Comprehensive data validation and error handling

## Contributing
This is an academic project. Please refer to the technical documentation for detailed implementation notes.

## License
Educational use only.
