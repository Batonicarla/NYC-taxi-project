"""
Database Loader for Enhanced Taxi Data
Loads processed data into PostgreSQL database
"""

import csv
import os
import sys
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

class TaxiDataLoader:
    """
    Loads enhanced taxi data into PostgreSQL database
    """
    
    def __init__(self, csv_file: str, db_config: Dict[str, str]):
        self.csv_file = csv_file
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
        # Loading statistics
        self.stats = {
            'records_loaded': 0,
            'records_failed': 0,
            'batch_size': 1000,
            'total_batches': 0
        }
    
    def load_data(self) -> Dict[str, Any]:
        """
        Main data loading pipeline
        """
        print("Starting database loading...")
        
        try:
            # Connect to database
            self._connect_database()
            
            # Load data from CSV
            data = self._read_enhanced_data()
            print(f"Read {len(data)} records from CSV")
            
            # Insert data in batches
            self._insert_data_batches(data)
            
            # Update statistics
            self._update_trip_statistics()
            
            # Generate loading report
            self._generate_loading_report()
            
        except Exception as e:
            print(f"Error during loading: {e}")
            raise
        finally:
            self._close_connection()
        
        return self.stats
    
    def _connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                database=self.db_config.get('database', 'nyc_taxi_db'),
                user=self.db_config.get('user', 'taxi_user'),
                password=self.db_config.get('password', 'your_password'),
                port=self.db_config.get('port', 5432)
            )
            self.cursor = self.connection.cursor()
            print("Connected to database successfully")
            
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            sys.exit(1)
    
    def _read_enhanced_data(self) -> List[Dict[str, Any]]:
        """Read enhanced CSV data"""
        data = []
        
        with open(self.csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        
        return data
    
    def _insert_data_batches(self, data: List[Dict]):
        """Insert data in batches for better performance"""
        print("Inserting data in batches...")
        
        batch_size = self.stats['batch_size']
        total_records = len(data)
        total_batches = (total_records + batch_size - 1) // batch_size
        self.stats['total_batches'] = total_batches
        
        # Prepare insert query
        insert_query = """
        INSERT INTO trips (
            trip_id, vendor_id, pickup_datetime, dropoff_datetime,
            passenger_count, pickup_longitude, pickup_latitude,
            dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
            trip_duration, trip_distance, trip_speed, idle_time,
            trip_efficiency, time_of_day, day_of_week, is_weekend,
            is_valid, quality_score, anomaly_flags
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (trip_id) DO NOTHING
        """
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_records)
            batch_data = data[start_idx:end_idx]
            
            # Prepare batch records
            batch_records = []
            for record in batch_data:
                try:
                    processed_record = self._prepare_record(record)
                    batch_records.append(processed_record)
                except Exception as e:
                    print(f"Error preparing record: {e}")
                    self.stats['records_failed'] += 1
                    continue
            
            # Insert batch
            try:
                execute_batch(self.cursor, insert_query, batch_records, page_size=100)
                self.connection.commit()
                
                self.stats['records_loaded'] += len(batch_records)
                
                # Progress report
                progress = ((batch_num + 1) / total_batches) * 100
                print(f"Progress: {progress:.1f}% - Batch {batch_num + 1}/{total_batches}")
                
            except psycopg2.Error as e:
                print(f"Error inserting batch {batch_num + 1}: {e}")
                self.connection.rollback()
                self.stats['records_failed'] += len(batch_records)
        
        print(f"Data loading completed: {self.stats['records_loaded']} records loaded")
    
    def _prepare_record(self, record: Dict[str, str]) -> tuple:
        """Prepare a single record for database insertion"""
        try:
            # Extract and convert values
            trip_id = record.get('id', '')
            vendor_id = int(record.get('vendor_id', 1))
            
            # Parse datetime fields
            pickup_datetime = datetime.strptime(
                record['pickup_datetime'], '%Y-%m-%d %H:%M:%S'
            )
            dropoff_datetime = datetime.strptime(
                record['dropoff_datetime'], '%Y-%m-%d %H:%M:%S'
            )
            
            # Numeric fields
            passenger_count = int(record.get('passenger_count', 1))
            pickup_longitude = float(record.get('pickup_longitude', 0))
            pickup_latitude = float(record.get('pickup_latitude', 0))
            dropoff_longitude = float(record.get('dropoff_longitude', 0))
            dropoff_latitude = float(record.get('dropoff_latitude', 0))
            
            # Trip details
            store_and_fwd_flag = record.get('store_and_fwd_flag', 'N')
            trip_duration = int(record.get('trip_duration', 0))
            
            # Derived features
            trip_distance = float(record.get('trip_distance_km', 0))
            trip_speed = float(record.get('trip_speed_kmh', 0))
            idle_time = int(float(record.get('estimated_idle_time', 0)))
            trip_efficiency = float(record.get('efficiency_score', 0))
            
            # Temporal features
            time_of_day = record.get('time_of_day', 'Unknown')
            day_of_week = record.get('day_of_week', 'Unknown')
            is_weekend = record.get('is_weekend', 'False') == 'True'
            
            # Quality flags
            is_valid = record.get('outlier_flag', 'NORMAL') == 'NORMAL'
            quality_score = 100 if is_valid else 80
            anomaly_flags = record.get('trip_patterns', '')
            
            return (
                trip_id, vendor_id, pickup_datetime, dropoff_datetime,
                passenger_count, pickup_longitude, pickup_latitude,
                dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
                trip_duration, trip_distance, trip_speed, idle_time,
                trip_efficiency, time_of_day, day_of_week, is_weekend,
                is_valid, quality_score, anomaly_flags
            )
            
        except (ValueError, KeyError, TypeError) as e:
            raise Exception(f"Error preparing record {record.get('id', 'unknown')}: {e}")
    
    def _update_trip_statistics(self):
        """Generate and insert trip statistics"""
        print("Updating trip statistics...")
        
        # Clear existing statistics
        self.cursor.execute("DELETE FROM trip_statistics")
        
        # Generate daily statistics
        stats_query = """
        INSERT INTO trip_statistics (
            date_period, hour_period, total_trips, avg_duration,
            avg_distance, avg_speed, total_passengers
        )
        SELECT 
            DATE(pickup_datetime) as date_period,
            EXTRACT(hour FROM pickup_datetime) as hour_period,
            COUNT(*) as total_trips,
            AVG(trip_duration) as avg_duration,
            AVG(trip_distance) as avg_distance,
            AVG(trip_speed) as avg_speed,
            SUM(passenger_count) as total_passengers
        FROM trips 
        WHERE is_valid = true
        GROUP BY DATE(pickup_datetime), EXTRACT(hour FROM pickup_datetime)
        ORDER BY date_period, hour_period
        """
        
        try:
            self.cursor.execute(stats_query)
            self.connection.commit()
            print("Trip statistics updated successfully")
        except psycopg2.Error as e:
            print(f"Error updating statistics: {e}")
            self.connection.rollback()
    
    def _generate_loading_report(self):
        """Generate database loading report"""
        report_file = "database_loading_report.txt"
        
        # Get database statistics
        try:
            self.cursor.execute("SELECT COUNT(*) FROM trips")
            total_trips = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM trips WHERE is_valid = true")
            valid_trips = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT DATE(pickup_datetime)) FROM trips")
            total_days = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM trip_statistics")
            stat_records = self.cursor.fetchone()[0]
            
        except psycopg2.Error:
            total_trips = valid_trips = total_days = stat_records = 0
        
        with open(report_file, 'w') as file:
            file.write("DATABASE LOADING REPORT\n")
            file.write("=" * 50 + "\n\n")
            
            file.write(f"CSV file: {self.csv_file}\n")
            file.write(f"Database: {self.db_config.get('database', 'nyc_taxi_db')}\n")
            file.write(f"Loading date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            file.write("LOADING STATISTICS:\n")
            file.write("-" * 30 + "\n")
            file.write(f"Records loaded: {self.stats['records_loaded']:,}\n")
            file.write(f"Records failed: {self.stats['records_failed']:,}\n")
            file.write(f"Batch size: {self.stats['batch_size']:,}\n")
            file.write(f"Total batches: {self.stats['total_batches']:,}\n")
            
            file.write("\nDATABASE STATISTICS:\n")
            file.write("-" * 30 + "\n")
            file.write(f"Total trips in database: {total_trips:,}\n")
            file.write(f"Valid trips: {valid_trips:,}\n")
            file.write(f"Days covered: {total_days:,}\n")
            file.write(f"Statistical records: {stat_records:,}\n")
            
            if total_trips > 0:
                success_rate = (self.stats['records_loaded'] / 
                              (self.stats['records_loaded'] + self.stats['records_failed'])) * 100
                file.write(f"Loading success rate: {success_rate:.2f}%\n")
        
        print(f"Loading report saved to {report_file}")
    
    def _close_connection(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Database connection closed")


def main():
    """Main execution function"""
    csv_file = "enhanced_taxi_data.csv"
    
    # Database configuration from environment variables
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'nyc_taxi_db'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': int(os.environ.get('DB_PORT', 5432))
    }
    
    # Validate required environment variables
    if not db_config['password']:
        print("Error: DB_PASSWORD environment variable is required")
        print("Please create a .env file with your database credentials")
        return
    
    # Check if input file exists
    if not os.path.exists(csv_file):
        print(f"Error: Input file {csv_file} not found")
        print("Please run feature_engineering.py first")
        return
    
    # Create loader and load data
    loader = TaxiDataLoader(csv_file, db_config)
    stats = loader.load_data()
    
    print("\n" + "=" * 50)
    print("DATABASE LOADING COMPLETED")
    print("=" * 50)
    print(f"Records loaded: {stats['records_loaded']:,}")
    print(f"Records failed: {stats['records_failed']:,}")
    
    if stats['records_loaded'] > 0:
        success_rate = (stats['records_loaded'] / 
                       (stats['records_loaded'] + stats['records_failed'])) * 100
        print(f"Success rate: {success_rate:.2f}%")


if __name__ == "__main__":
    main()
