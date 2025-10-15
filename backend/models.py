"""
Database Models for NYC Taxi Analysis
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool as pg_pool
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import json

class DatabaseManager:
    """
    Database connection and query manager
    """
    
    def __init__(self, config):
        # Extract database configuration from config object
        self.db_config = {
            'host': config.DB_HOST,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'port': config.DB_PORT
        }
        self.pool = None
        self.connection = None  # Deprecated: maintained for backward compatibility
        self.cursor = None      # Deprecated: do not use a shared cursor
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Close existing pool if any
            if self.pool is not None:
                try:
                    self.pool.closeall()
                except Exception:
                    pass
                self.pool = None

            # Initialize connection pool
            # Min 1, max 10 connections; adjust if needed via config in future
            self.pool = pg_pool.SimpleConnectionPool(1, 10, **self.db_config)
            print("Initialized PostgreSQL connection pool")
            
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            self.pool = None
            self.connection = None
            self.cursor = None
    

    
    def disconnect(self):
        """Close database connection"""
        try:
            if self.pool is not None:
                self.pool.closeall()
                self.pool = None
        finally:
            # Close any legacy connection/cursor if present
            try:
                if self.cursor:
                    self.cursor.close()
            except Exception:
                pass
            try:
                if self.connection:
                    self.connection.close()
            except Exception:
                pass
        print("Disconnected from PostgreSQL")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results"""
        try:
            if self.pool is None:
                self.connect()

            conn = self.pool.getconn()
            try:
                conn.autocommit = True
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    try:
                        rows = cur.fetchall()
                    except psycopg2.ProgrammingError as e:
                        if "no results to fetch" in str(e):
                            rows = []
                        else:
                            raise
                return rows
            except psycopg2.Error as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise e
            finally:
                if self.pool and conn:
                    self.pool.putconn(conn)
        except psycopg2.Error as e:
            print(f"Query execution error: {e}")
            # Note: connection rolled back above; nothing else to do here
            return []
    
    def execute_single(self, query: str, params: tuple = None) -> Dict:
        """Execute query and return a single result as dict"""
        try:
            if self.pool is None:
                self.connect()

            conn = self.pool.getconn()
            try:
                conn.autocommit = True
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    try:
                        result = cur.fetchone()
                    except psycopg2.ProgrammingError as e:
                        if "no results to fetch" in str(e):
                            result = None
                        else:
                            raise
                return dict(result) if result else {}
            except psycopg2.Error as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                raise e
            finally:
                if self.pool and conn:
                    self.pool.putconn(conn)
        except psycopg2.Error as e:
            print(f"Query execution error: {e}")
            # Note: connection rolled back above
            return {}

class TripModel:
    """
    Model for taxi trip data operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_trips(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get trips with optional filtering
        """
        # Enforce reasonable limits to prevent huge data transfers
        limit = min(limit, 1000)
        # Base query
        base_query = """
        SELECT 
            trip_id, vendor_id, pickup_datetime, dropoff_datetime,
            passenger_count, pickup_longitude, pickup_latitude,
            dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
            trip_duration, trip_distance, trip_speed, idle_time,
            trip_efficiency, time_of_day, day_of_week, is_weekend,
            is_valid, quality_score, anomaly_flags
        FROM trips
        WHERE is_valid = true
        """
        
        # Build WHERE conditions
        conditions = []
        params = []
        param_counter = 1
        
        if filters:
            # Date range filter
            if 'start_date' in filters and filters['start_date']:
                conditions.append("pickup_datetime >= %s")
                params.append(filters['start_date'])
            
            if 'end_date' in filters and filters['end_date']:
                conditions.append("pickup_datetime <= %s")
                params.append(filters['end_date'])
            
            # Vendor filter
            if 'vendor_id' in filters and filters['vendor_id']:
                conditions.append("vendor_id = %s")
                params.append(int(filters['vendor_id']))
            
            # Passenger count filter
            if 'passenger_count' in filters and filters['passenger_count']:
                conditions.append("passenger_count = %s")
                params.append(int(filters['passenger_count']))
            
            # Time of day filter
            if 'time_of_day' in filters and filters['time_of_day']:
                conditions.append("time_of_day = %s")
                params.append(filters['time_of_day'])
            
            # Weekend filter
            if 'is_weekend' in filters and filters['is_weekend'] is not None:
                conditions.append("is_weekend = %s")
                params.append(bool(filters['is_weekend']))
            
            # Distance range filter
            if 'min_distance' in filters and filters['min_distance']:
                conditions.append("trip_distance >= %s")
                params.append(float(filters['min_distance']))
            
            if 'max_distance' in filters and filters['max_distance']:
                conditions.append("trip_distance <= %s")
                params.append(float(filters['max_distance']))
            
            # Duration range filter
            if 'min_duration' in filters and filters['min_duration']:
                conditions.append("trip_duration >= %s")
                params.append(int(filters['min_duration']))
            
            if 'max_duration' in filters and filters['max_duration']:
                conditions.append("trip_duration <= %s")
                params.append(int(filters['max_duration']))
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add ordering and pagination
        base_query += " ORDER BY pickup_datetime DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # Execute query
        trips = self.db.execute_query(base_query, tuple(params))
        
        # Get total count for pagination (use params without limit/offset)
        count_params = params[:-2]  # Remove limit and offset
        count_query = "SELECT COUNT(*) as total FROM trips WHERE is_valid = true"
        if conditions:
            count_query += " AND " + " AND ".join(conditions)
        
        count_result = self.db.execute_single(count_query, tuple(count_params) if count_params else None)
        total_count = count_result.get('total', 0) if count_result else 0
        
        return {
            'trips': [dict(trip) for trip in trips],
            'total_count': total_count,
            'page_size': limit,
            'offset': offset,
            'has_more': offset + limit < total_count
        }
    
    def get_trip_by_id(self, trip_id: str) -> Optional[Dict]:
        """Get single trip by ID"""
        query = """
        SELECT * FROM trips WHERE trip_id = %s
        """
        return self.db.execute_single(query, (trip_id,))
    
    def get_trip_statistics_summary(self) -> Dict[str, Any]:
        """Get overall trip statistics"""
        query = """
        SELECT 
            COUNT(*) as total_trips,
            COUNT(DISTINCT vendor_id) as unique_vendors,
            AVG(trip_duration) as avg_duration,
            AVG(trip_distance) as avg_distance,
            AVG(trip_speed) as avg_speed,
            AVG(passenger_count) as avg_passengers,
            MIN(pickup_datetime) as earliest_trip,
            MAX(pickup_datetime) as latest_trip,
            COUNT(CASE WHEN is_weekend = true THEN 1 END) as weekend_trips,
            COUNT(CASE WHEN is_weekend = false THEN 1 END) as weekday_trips
        FROM trips 
        WHERE is_valid = true
        """
        
        result = self.db.execute_single(query)
        if result:
            return dict(result)
        return {}
    
    def get_hourly_statistics(self) -> List[Dict]:
        """Get trip statistics by hour of day"""
        query = """
        SELECT 
            EXTRACT(hour FROM pickup_datetime)::integer as hour,
            COUNT(*) as trip_count,
            AVG(trip_duration)::decimal as avg_duration,
            AVG(trip_distance::decimal) as avg_distance,
            AVG(trip_speed::decimal) as avg_speed,
            AVG(passenger_count)::decimal as avg_passengers
        FROM trips 
        WHERE is_valid = true
          AND pickup_datetime IS NOT NULL
          AND trip_distance IS NOT NULL
          AND trip_speed IS NOT NULL
        GROUP BY EXTRACT(hour FROM pickup_datetime)
        ORDER BY hour
        """
        
        try:
            results = self.db.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"Error in get_hourly_statistics: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_daily_statistics(self, days: int = 30) -> List[Dict]:
        """Get trip statistics by day"""
        query = """
        SELECT 
            DATE(pickup_datetime) as date,
            COUNT(*) as trip_count,
            AVG(trip_duration) as avg_duration,
            AVG(trip_distance::numeric) as avg_distance,
            AVG(trip_speed::numeric) as avg_speed,
            COUNT(CASE WHEN is_weekend = true THEN 1 END) as weekend_trips,
            COUNT(CASE WHEN is_weekend = false THEN 1 END) as weekday_trips
        FROM trips 
        WHERE is_valid = true 
        GROUP BY DATE(pickup_datetime)
        ORDER BY date DESC
        LIMIT %s
        """
        
        results = self.db.execute_query(query, (days,))
        return [dict(row) for row in results]
    
    def get_popular_locations(self, location_type: str = 'pickup', limit: int = 10) -> List[Dict]:
        """Get most popular pickup or dropoff locations"""
        
        if location_type not in ['pickup', 'dropoff']:
            return []
        
        lon_col = f"{location_type}_longitude"
        lat_col = f"{location_type}_latitude"
        
        query = f"""
        SELECT 
            ROUND({lon_col}::numeric, 3) as longitude,
            ROUND({lat_col}::numeric, 3) as latitude,
            COUNT(*) as trip_count,
            AVG(trip_distance) as avg_distance,
            AVG(trip_duration) as avg_duration
        FROM trips 
        WHERE is_valid = true 
        AND {lon_col} IS NOT NULL 
        AND {lat_col} IS NOT NULL
        GROUP BY ROUND({lon_col}::numeric, 3), ROUND({lat_col}::numeric, 3)
        HAVING COUNT(*) > 5
        ORDER BY trip_count DESC
        LIMIT %s
        """
        
        results = self.db.execute_query(query, (limit,))
        return [dict(row) for row in results]
    
    def get_speed_distribution(self) -> List[Dict]:
        """Get trip speed distribution"""
        query = """
        SELECT 
            CASE 
                WHEN trip_speed < 10 THEN '0-10 km/h'
                WHEN trip_speed < 20 THEN '10-20 km/h'
                WHEN trip_speed < 30 THEN '20-30 km/h'
                WHEN trip_speed < 40 THEN '30-40 km/h'
                WHEN trip_speed < 50 THEN '40-50 km/h'
                ELSE '50+ km/h'
            END as speed_range,
            COUNT(*) as trip_count,
            AVG(trip_duration) as avg_duration,
            AVG(trip_distance) as avg_distance
        FROM trips 
        WHERE is_valid = true AND trip_speed > 0
        GROUP BY 
            CASE 
                WHEN trip_speed < 10 THEN '0-10 km/h'
                WHEN trip_speed < 20 THEN '10-20 km/h'
                WHEN trip_speed < 30 THEN '20-30 km/h'
                WHEN trip_speed < 40 THEN '30-40 km/h'
                WHEN trip_speed < 50 THEN '40-50 km/h'
                ELSE '50+ km/h'
            END
        ORDER BY MIN(trip_speed)
        """
        
        results = self.db.execute_query(query)
        return [dict(row) for row in results]
    
    def get_efficiency_insights(self) -> Dict[str, Any]:
        """Get trip efficiency insights"""
        query = """
        SELECT 
            AVG(trip_efficiency::decimal) as avg_efficiency,
            MIN(trip_efficiency::decimal) as min_efficiency,
            MAX(trip_efficiency::decimal) as max_efficiency,
            COUNT(CASE WHEN trip_efficiency::decimal > 80 THEN 1 END) as high_efficiency_trips,
            COUNT(CASE WHEN trip_efficiency::decimal < 40 THEN 1 END) as low_efficiency_trips,
            AVG(idle_time::decimal) as avg_idle_time,
            COUNT(*) as total_trips
        FROM trips 
        WHERE is_valid = true 
          AND trip_efficiency IS NOT NULL 
          AND trip_efficiency::decimal > 0
        """
        
        try:
            result = self.db.execute_single(query)
            if result:
                return dict(result)
            return {}
        except Exception as e:
            print(f"Error in get_efficiency_insights: {e}")
            import traceback
            traceback.print_exc()
            return {}

class StatisticsModel:
    """
    Model for pre-computed statistics operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_hourly_trends(self, days: int = 7) -> List[Dict]:
        """Get hourly trends from statistics table"""
        query = """
        SELECT 
            hour_period,
            AVG(total_trips) as avg_trips,
            AVG(avg_duration) as avg_duration,
            AVG(avg_distance) as avg_distance,
            AVG(avg_speed) as avg_speed
        FROM trip_statistics 
        WHERE date_period >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY hour_period 
        ORDER BY hour_period
        """
        
        results = self.db.execute_query(query, (days,))
        return [dict(row) for row in results]
    
    def get_daily_trends(self, days: int = 30) -> List[Dict]:
        """Get daily trends"""
        query = """
        SELECT 
            date_period,
            SUM(total_trips) as daily_trips,
            AVG(avg_duration) as avg_duration,
            AVG(avg_distance) as avg_distance,
            AVG(avg_speed) as avg_speed,
            SUM(total_passengers) as total_passengers
        FROM trip_statistics 
        WHERE date_period >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY date_period 
        ORDER BY date_period DESC
        LIMIT %s
        """
        
        results = self.db.execute_query(query, (days, days))
        return [dict(row) for row in results]
