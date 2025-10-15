"""
Utility Functions for NYC Taxi Analysis Backend
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import math

class DataValidator:
    """
    Data validation utilities
    """
    
    @staticmethod
    def validate_coordinates(longitude: float, latitude: float) -> bool:
        """Validate NYC coordinates"""
        # NYC approximate boundaries
        nyc_bounds = {
            'min_lat': 40.4774, 'max_lat': 40.9176,
            'min_lon': -74.2591, 'max_lon': -73.7004
        }
        
        return (nyc_bounds['min_lat'] <= latitude <= nyc_bounds['max_lat'] and
                nyc_bounds['min_lon'] <= longitude <= nyc_bounds['max_lon'])
    
    @staticmethod
    def validate_trip_duration(duration: int) -> bool:
        """Validate trip duration (1 minute to 2 hours)"""
        return 60 <= duration <= 7200
    
    @staticmethod
    def validate_passenger_count(count: int) -> bool:
        """Validate passenger count"""
        return 1 <= count <= 8
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
        """Validate date range"""
        if not start_date or not end_date:
            return True  # Allow None values
        return start_date <= end_date

class GeographicUtils:
    """
    Geographic calculation utilities
    """
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two points in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in kilometers
        earth_radius_km = 6371.0
        
        return earth_radius_km * c
    
    @staticmethod
    def get_borough_from_coordinates(latitude: float, longitude: float) -> str:
        """
        Estimate borough from coordinates (simplified)
        """
        # Simplified borough boundaries (approximate)
        borough_centers = {
            'Manhattan': (40.7831, -73.9712),
            'Brooklyn': (40.6782, -73.9442),
            'Queens': (40.7282, -73.7949),
            'Bronx': (40.8448, -73.8648),
            'Staten Island': (40.5795, -74.1502)
        }
        
        min_distance = float('inf')
        closest_borough = "Manhattan"  # Default
        
        for borough, (b_lat, b_lon) in borough_centers.items():
            distance = GeographicUtils.haversine_distance(latitude, longitude, b_lat, b_lon)
            if distance < min_distance:
                min_distance = distance
                closest_borough = borough
        
        return closest_borough

class TimeUtils:
    """
    Time-related utility functions
    """
    
    @staticmethod
    def get_time_period(hour: int) -> str:
        """Get time period from hour"""
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"
    
    @staticmethod
    def is_rush_hour(hour: int, is_weekend: bool) -> bool:
        """Determine if time is rush hour"""
        if is_weekend:
            return False
        return (7 <= hour <= 9) or (17 <= hour <= 19)
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human-readable format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

class StatisticalUtils:
    """
    Statistical calculation utilities
    """
    
    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile of a list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if percentile == 0:
            return sorted_values[0]
        elif percentile == 100:
            return sorted_values[-1]
        else:
            position = (percentile / 100.0) * (n - 1)
            lower_index = int(position)
            upper_index = min(lower_index + 1, n - 1)
            
            weight = position - lower_index
            return (sorted_values[lower_index] * (1 - weight) + 
                   sorted_values[upper_index] * weight)
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values"""
        if not values:
            return {}
        
        n = len(values)
        mean = sum(values) / n
        
        # Calculate variance and standard deviation
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)
        
        return {
            'count': n,
            'mean': mean,
            'std_dev': std_dev,
            'variance': variance,
            'min': min(values),
            'max': max(values),
            'range': max(values) - min(values)
        }
    
    @staticmethod
    def detect_outliers_iqr(values: List[float], multiplier: float = 1.5) -> List[int]:
        """Detect outliers using IQR method"""
        if len(values) < 4:
            return []
        
        q1 = StatisticalUtils.calculate_percentile(values, 25)
        q3 = StatisticalUtils.calculate_percentile(values, 75)
        
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices

class ResponseFormatter:
    """
    API response formatting utilities
    """
    
    @staticmethod
    def format_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format successful API response"""
        return {
            'status': 'success',
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def format_error_response(error_message: str, error_code: str = None) -> Dict[str, Any]:
        """Format error API response"""
        response = {
            'status': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_code:
            response['error_code'] = error_code
        
        return response
    
    @staticmethod
    def format_paginated_response(data: List[Any], page: int, limit: int, 
                                 total_count: int, additional_data: Dict = None) -> Dict[str, Any]:
        """Format paginated API response"""
        response = {
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': (total_count + limit - 1) // limit,
                'has_next': page * limit < total_count,
                'has_prev': page > 1
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_data:
            response.update(additional_data)
        
        return response

class CacheUtils:
    """
    Simple in-memory caching utilities
    """
    
    _cache = {}
    _cache_timestamps = {}
    
    @classmethod
    def get(cls, key: str, max_age_seconds: int = 900) -> Optional[Any]:  # 15 minutes default
        """Get cached value if not expired"""
        if key not in cls._cache:
            return None
        
        timestamp = cls._cache_timestamps.get(key)
        if timestamp and (datetime.now() - timestamp).total_seconds() > max_age_seconds:
            cls.delete(key)
            return None
        
        return cls._cache[key]
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set cached value with timestamp"""
        cls._cache[key] = value
        cls._cache_timestamps[key] = datetime.now()
    
    @classmethod
    def delete(cls, key: str) -> None:
        """Delete cached value"""
        cls._cache.pop(key, None)
        cls._cache_timestamps.pop(key, None)
    
    @classmethod
    def clear(cls) -> None:
        """Clear all cached values"""
        cls._cache.clear()
        cls._cache_timestamps.clear()

class DataExporter:
    """
    Data export utilities
    """
    
    @staticmethod
    def to_csv_string(data: List[Dict], columns: List[str] = None) -> str:
        """Convert list of dictionaries to CSV string"""
        if not data:
            return ""
        
        if not columns:
            columns = list(data[0].keys())
        
        # Header
        csv_lines = [','.join(columns)]
        
        # Data rows
        for row in data:
            csv_row = []
            for col in columns:
                value = row.get(col, '')
                # Escape commas and quotes
                if isinstance(value, str) and (',' in value or '"' in value):
                    value = f'"{value.replace('"', '""')}"'
                csv_row.append(str(value))
            csv_lines.append(','.join(csv_row))
        
        return '\n'.join(csv_lines)
    
    @staticmethod
    def to_json_string(data: Any, indent: int = 2) -> str:
        """Convert data to formatted JSON string"""
        def json_serializer(obj):
            """JSON serializer for datetime objects"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, indent=indent, default=json_serializer)

# Decorator utilities
def validate_request_data(required_fields: List[str] = None):
    """Decorator to validate request data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            if required_fields:
                if request.is_json:
                    data = request.get_json()
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return jsonify(ResponseFormatter.format_error_response(
                            f"Missing required fields: {missing_fields}"
                        )), 400
                else:
                    missing_fields = [field for field in required_fields if not request.args.get(field)]
                    if missing_fields:
                        return jsonify(ResponseFormatter.format_error_response(
                            f"Missing required parameters: {missing_fields}"
                        )), 400
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
