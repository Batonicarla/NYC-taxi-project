"""
Flask Backend Application Configuration
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'nyc_taxi_db'
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD')  # Must be set via environment variable
    DB_PORT = os.environ.get('DB_PORT') or 5432
    
    # API configuration
    API_TITLE = 'NYC Taxi Trip Analysis API'
    API_VERSION = 'v1.0'
    MAX_RESULTS_PER_PAGE = 1000
    DEFAULT_PAGE_SIZE = 100
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:8000', 
        'http://127.0.0.1:8000',
        'http://localhost:5500',
        'http://127.0.0.1:5500',
        'http://localhost:3000',  # Common development port
        'http://127.0.0.1:3000'
    ]
    
    # Cache settings
    CACHE_TIMEOUT = timedelta(minutes=15)
    
    @staticmethod
    def validate_config():
        """Validate that required environment variables are set"""
        required_vars = ['DB_PASSWORD']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DB_NAME = 'test_nyc_taxi_db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
