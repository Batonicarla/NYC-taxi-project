"""
Flask Application for NYC Taxi Analysis
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
import sys

# Import application modules
from config import config
from routes import api_bp, init_models

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    config_instance = config[config_name]
    app.config.from_object(config_instance)
    
    # Validate configuration (check for required environment variables)
    try:
        config_instance.validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please set the required environment variables before running the application.")
        sys.exit(1)
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize models with config instance
    init_models(config_instance)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Root endpoint
    @app.route('/')
    def index():
        """Root endpoint with API information"""
        return jsonify({
            'message': 'NYC Taxi Trip Analysis API',
            'version': app.config.get('API_VERSION', '1.0'),
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/api/health',
                'trips': '/api/trips',
                'statistics': '/api/stats/summary',
                'insights': '/api/insights/comprehensive',
                'documentation': 'See README.md for full API documentation'
            }
        })
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        """Log request information for debugging"""
        if app.debug:
            print(f"Request: {request.method} {request.url}")
            if request.is_json:
                print(f"JSON: {request.get_json()}")
            if request.args:
                print(f"Args: {dict(request.args)}")
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers and disable caching for API responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Disable caching for API responses
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    
    return app

def main():
    """Main application entry point"""
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("=" * 50)
    print("NYC TAXI ANALYSIS API SERVER")
    print("=" * 50)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"API Version: {app.config.get('API_VERSION', '1.0')}")
    print("=" * 50)
    print("Available endpoints:")
    print("  GET  /                     - API information")
    print("  GET  /api/health           - Health check")
    print("  GET  /api/trips            - Get trips (with filters)")
    print("  GET  /api/trips/<id>       - Get specific trip")
    print("  GET  /api/stats/summary    - Overall statistics")
    print("  GET  /api/stats/hourly     - Hourly statistics")
    print("  GET  /api/stats/daily      - Daily statistics")
    print("  GET  /api/locations/popular - Popular locations")
    print("  GET  /api/insights/speed   - Speed insights")
    print("  GET  /api/insights/efficiency - Efficiency insights")
    print("  GET  /api/insights/comprehensive - All insights")
    print("=" * 50)
    
    # Start the application
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
