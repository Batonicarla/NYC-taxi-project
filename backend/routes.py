"""
API Routes for NYC Taxi Analysis Backend
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Import models
from models import TripModel, StatisticsModel, DatabaseManager

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global database manager (will be initialized in app.py)
db_manager = None
trip_model = None
stats_model = None

def init_models(app_config):
    """Initialize models with app configuration"""
    global db_manager, trip_model, stats_model
    db_manager = DatabaseManager(app_config)
    db_manager.connect()
    trip_model = TripModel(db_manager)
    stats_model = StatisticsModel(db_manager)

def handle_error(error_message: str, status_code: int = 400) -> tuple:
    """Standard error response handler"""
    return jsonify({
        'error': error_message,
        'status': 'error',
        'timestamp': datetime.now().isoformat()
    }), status_code

def parse_date(date_string: str) -> datetime:
    """Parse date string with error handling"""
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError(f"Invalid date format: {date_string}")

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    try:
        # Test database connection
        if db_manager and db_manager.connection:
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.now().isoformat(),
            'version': current_app.config.get('API_VERSION', '1.0')
        }), 200
    
    except Exception as e:
        return handle_error(f"Health check failed: {str(e)}", 500)

# Trip endpoints
@api_bp.route('/trips', methods=['GET'])
def get_trips():
    """
    Get trips with optional filtering
    Query parameters:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - vendor_id: 1 or 2
    - passenger_count: integer
    - time_of_day: Morning, Afternoon, Evening, Night
    - is_weekend: true/false
    - min_distance, max_distance: float
    - min_duration, max_duration: integer (seconds)
    - page: page number (default 1)
    - limit: results per page (default 100, max 1000)
    """
    try:
        # Parse query parameters
        filters = {}
        
        # Date filters
        if request.args.get('start_date'):
            filters['start_date'] = parse_date(request.args.get('start_date'))
        
        if request.args.get('end_date'):
            filters['end_date'] = parse_date(request.args.get('end_date'))
        
        # Numeric filters
        numeric_filters = ['vendor_id', 'passenger_count', 'min_distance', 'max_distance', 'min_duration', 'max_duration']
        for filter_name in numeric_filters:
            value = request.args.get(filter_name)
            if value:
                try:
                    if 'distance' in filter_name:
                        filters[filter_name] = float(value)
                    else:
                        filters[filter_name] = int(value)
                except ValueError:
                    return handle_error(f"Invalid {filter_name}: {value}")
        
        # String filters
        if request.args.get('time_of_day'):
            valid_times = ['Morning', 'Afternoon', 'Evening', 'Night']
            time_of_day = request.args.get('time_of_day')
            if time_of_day not in valid_times:
                return handle_error(f"Invalid time_of_day. Must be one of: {valid_times}")
            filters['time_of_day'] = time_of_day
        
        # Boolean filters
        if request.args.get('is_weekend'):
            filters['is_weekend'] = request.args.get('is_weekend').lower() == 'true'
        
        # Pagination
        page = max(1, int(request.args.get('page', 1)))
        limit = min(current_app.config.get('MAX_RESULTS_PER_PAGE', 1000), 
                   int(request.args.get('limit', current_app.config.get('DEFAULT_PAGE_SIZE', 100))))
        offset = (page - 1) * limit
        
        # Get trips
        result = trip_model.get_trips(filters, limit, offset)
        
        # Add pagination metadata
        result.update({
            'page': page,
            'limit': limit,
            'total_pages': (result['total_count'] + limit - 1) // limit,
            'filters_applied': filters,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify(result), 200
    
    except ValueError as e:
        return handle_error(str(e))
    except Exception as e:
        return handle_error(f"Error retrieving trips: {str(e)}", 500)

@api_bp.route('/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    """Get single trip by ID"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip:
            return handle_error(f"Trip {trip_id} not found", 404)
        
        return jsonify({
            'trip': dict(trip),
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving trip: {str(e)}", 500)

# Statistics endpoints
@api_bp.route('/stats/summary', methods=['GET'])
def get_statistics_summary():
    """Get overall trip statistics summary"""
    try:
        stats = trip_model.get_trip_statistics_summary()
        
        return jsonify({
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving statistics: {str(e)}", 500)

@api_bp.route('/stats/hourly', methods=['GET'])
def get_hourly_statistics():
    """Get hourly trip statistics"""
    try:
        stats = trip_model.get_hourly_statistics()
        
        return jsonify({
            'hourly_stats': stats,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving hourly stats: {str(e)}", 500)

@api_bp.route('/stats/daily', methods=['GET'])
def get_daily_statistics():
    """Get daily trip statistics"""
    try:
        days = min(365, int(request.args.get('days', 30)))
        stats = trip_model.get_daily_statistics(days)
        
        return jsonify({
            'daily_stats': stats,
            'days_requested': days,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving daily stats: {str(e)}", 500)

@api_bp.route('/stats/trends/hourly', methods=['GET'])
def get_hourly_trends():
    """Get hourly trends from pre-computed statistics"""
    try:
        days = min(30, int(request.args.get('days', 7)))
        trends = stats_model.get_hourly_trends(days)
        
        return jsonify({
            'hourly_trends': trends,
            'days_analyzed': days,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving hourly trends: {str(e)}", 500)

@api_bp.route('/stats/trends/daily', methods=['GET'])
def get_daily_trends():
    """Get daily trends from pre-computed statistics"""
    try:
        days = min(90, int(request.args.get('days', 30)))
        trends = stats_model.get_daily_trends(days)
        
        return jsonify({
            'daily_trends': trends,
            'days_analyzed': days,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving daily trends: {str(e)}", 500)

# Location endpoints
@api_bp.route('/locations/popular', methods=['GET'])
def get_popular_locations():
    """Get popular pickup/dropoff locations"""
    try:
        location_type = request.args.get('type', 'pickup')
        limit = min(50, int(request.args.get('limit', 10)))
        
        if location_type not in ['pickup', 'dropoff']:
            return handle_error("Invalid location type. Use 'pickup' or 'dropoff'")
        
        locations = trip_model.get_popular_locations(location_type, limit)
        
        return jsonify({
            'popular_locations': locations,
            'location_type': location_type,
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving popular locations: {str(e)}", 500)

# Insights endpoints
@api_bp.route('/insights/speed', methods=['GET'])
def get_speed_insights():
    """Get speed distribution insights"""
    try:
        speed_distribution = trip_model.get_speed_distribution()
        
        return jsonify({
            'speed_distribution': speed_distribution,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving speed insights: {str(e)}", 500)

@api_bp.route('/insights/efficiency', methods=['GET'])
def get_efficiency_insights():
    """Get trip efficiency insights"""
    try:
        efficiency_data = trip_model.get_efficiency_insights()
        
        # Calculate additional insights
        insights = []
        
        if efficiency_data:
            total_trips = efficiency_data.get('total_trips', 0)
            high_efficiency = efficiency_data.get('high_efficiency_trips', 0)
            low_efficiency = efficiency_data.get('low_efficiency_trips', 0)
            avg_idle_time = efficiency_data.get('avg_idle_time', 0)
            
            if total_trips > 0:
                insights.extend([
                    {
                        'type': 'efficiency_distribution',
                        'description': f"{(high_efficiency/total_trips)*100:.1f}% of trips have high efficiency (>80%)",
                        'value': (high_efficiency/total_trips)*100,
                        'category': 'positive' if (high_efficiency/total_trips) > 0.5 else 'concern'
                    },
                    {
                        'type': 'idle_time_impact',
                        'description': f"Average idle time per trip: {avg_idle_time:.0f} seconds",
                        'value': avg_idle_time,
                        'category': 'neutral'
                    },
                    {
                        'type': 'low_efficiency_concern',
                        'description': f"{(low_efficiency/total_trips)*100:.1f}% of trips have low efficiency (<40%)",
                        'value': (low_efficiency/total_trips)*100,
                        'category': 'concern' if (low_efficiency/total_trips) > 0.2 else 'positive'
                    }
                ])
        
        return jsonify({
            'efficiency_metrics': efficiency_data,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return handle_error(f"Error retrieving efficiency insights: {str(e)}", 500)

@api_bp.route('/insights/comprehensive', methods=['GET'])
def get_comprehensive_insights():
    """Get comprehensive data insights (for documentation)"""
    try:
        # Gather multiple data points
        summary_stats = trip_model.get_trip_statistics_summary()
        hourly_stats = trip_model.get_hourly_statistics()
        speed_distribution = trip_model.get_speed_distribution()
        efficiency_data = trip_model.get_efficiency_insights()
        popular_pickups = trip_model.get_popular_locations('pickup', 5)
        popular_dropoffs = trip_model.get_popular_locations('dropoff', 5)
        
        # Generate insights
        insights = []
        
        # Insight 1: Peak Hour Analysis
        if hourly_stats:
            peak_hour = max(hourly_stats, key=lambda x: x['trip_count'])
            insights.append({
                'title': 'Peak Hour Traffic Pattern',
                'description': f"Hour {int(peak_hour['hour'])}:00 has the highest trip volume with {peak_hour['trip_count']:,} trips",
                'data': {
                    'peak_hour': int(peak_hour['hour']),
                    'peak_trips': int(peak_hour['trip_count']),
                    'peak_avg_speed': float(peak_hour['avg_speed']) if peak_hour['avg_speed'] else 0
                },
                'visualization_type': 'bar_chart',
                'insight_type': 'temporal_pattern'
            })
        
        # Insight 2: Speed vs Efficiency Correlation
        if speed_distribution and efficiency_data:
            total_trips = efficiency_data.get('total_trips', 0)
            high_efficiency_trips = efficiency_data.get('high_efficiency_trips', 0)
            
            if total_trips > 0:
                efficiency_rate = (high_efficiency_trips / total_trips) * 100
                insights.append({
                    'title': 'Trip Efficiency Analysis',
                    'description': f"{efficiency_rate:.1f}% of trips achieve high efficiency (>80%), with average idle time of {efficiency_data.get('avg_idle_time', 0):.0f} seconds",
                    'data': {
                        'efficiency_rate': efficiency_rate,
                        'avg_idle_time': float(efficiency_data.get('avg_idle_time', 0)),
                        'median_efficiency': float(efficiency_data.get('median_efficiency', 0))
                    },
                    'visualization_type': 'gauge_chart',
                    'insight_type': 'performance_metric'
                })
        
        # Insight 3: Geographic Distribution
        if popular_pickups and popular_dropoffs:
            top_pickup = popular_pickups[0]
            top_dropoff = popular_dropoffs[0]
            
            insights.append({
                'title': 'Geographic Hotspot Analysis',
                'description': f"Most popular pickup location ({top_pickup['longitude']:.3f}, {top_pickup['latitude']:.3f}) has {top_pickup['trip_count']:,} trips",
                'data': {
                    'top_pickup_location': {
                        'longitude': float(top_pickup['longitude']),
                        'latitude': float(top_pickup['latitude']),
                        'trip_count': int(top_pickup['trip_count'])
                    },
                    'top_dropoff_location': {
                        'longitude': float(top_dropoff['longitude']),
                        'latitude': float(top_dropoff['latitude']),
                        'trip_count': int(top_dropoff['trip_count'])
                    }
                },
                'visualization_type': 'map_overlay',
                'insight_type': 'geographic_pattern'
            })
        
        return jsonify({
            'insights': insights,
            'data_summary': {
                'total_insights': len(insights),
                'analysis_timestamp': datetime.now().isoformat(),
                'data_sources': ['trips', 'statistics', 'locations']
            },
            'raw_data': {
                'summary_stats': summary_stats,
                'speed_distribution': speed_distribution[:3],  # Top 3 for brevity
                'efficiency_metrics': efficiency_data
            }
        }), 200
    
    except Exception as e:
        return handle_error(f"Error generating comprehensive insights: {str(e)}", 500)

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return handle_error("Endpoint not found", 404)

@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return handle_error("Method not allowed", 405)

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return handle_error("Internal server error", 500)
