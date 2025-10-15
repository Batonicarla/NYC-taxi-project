"""
Data Cleaning Pipeline for NYC Taxi Dataset
Handles missing values, duplicates, invalid records, and outliers
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from custom_algorithms import CustomAlgorithms

class TaxiDataCleaner:
    """
    Comprehensive data cleaning pipeline for NYC taxi data
    """
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.algorithms = CustomAlgorithms()
        
        # Cleaning statistics
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_removed': 0,
            'missing_values_fixed': 0,
            'outliers_detected': 0,
            'coordinate_errors': 0,
            'datetime_errors': 0,
            'duration_errors': 0
        }
        
        # NYC approximate boundaries
        self.nyc_bounds = {
            'min_lat': 40.4774, 'max_lat': 40.9176,
            'min_lon': -74.2591, 'max_lon': -73.7004
        }
        
        # Reasonable trip constraints
        self.trip_constraints = {
            'min_duration': 60,      # 1 minute
            'max_duration': 3600,    # 1 hour
            'max_distance': 100,     # 100 km
            'max_passenger': 8
        }
    
    def clean_dataset(self) -> Dict[str, Any]:
        """
        Main cleaning pipeline
        Returns cleaning statistics and logs
        """
        print("Starting data cleaning pipeline...")
        
        # Read and parse data
        raw_data = self._read_csv_data()
        print(f"Loaded {len(raw_data)} records")
        
        # Clean data step by step
        cleaned_data = self._remove_duplicates(raw_data)
        cleaned_data = self._fix_missing_values(cleaned_data)
        cleaned_data = self._validate_coordinates(cleaned_data)
        cleaned_data = self._validate_datetime(cleaned_data)
        cleaned_data = self._validate_trip_duration(cleaned_data)
        cleaned_data = self._detect_outliers(cleaned_data)
        
        # Write cleaned data
        self._write_cleaned_data(cleaned_data)
        
        # Generate cleaning report
        self._generate_cleaning_report()
        
        return self.stats
    
    def _read_csv_data(self) -> List[Dict[str, Any]]:
        """Read CSV data with error handling"""
        data = []
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                # Read header
                reader = csv.reader(file)
                header = next(reader)
                
                # Clean header (remove any hidden characters)
                header = [col.strip() for col in header]
                
                # Read data rows
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(header):
                        continue  # Skip malformed rows
                    
                    # Create record dictionary
                    record = {}
                    for i, value in enumerate(row):
                        if i < len(header):
                            record[header[i]] = value.strip()
                    
                    record['row_number'] = row_num
                    data.append(record)
                    
                    self.stats['total_records'] += 1
                    
                    # Progress indicator
                    if row_num % 50000 == 0:
                        print(f"Processed {row_num} rows...")
        
        except FileNotFoundError:
            print(f"Error: File {self.input_file} not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
        
        return data
    
    def _remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """Remove duplicate records based on key fields"""
        print("Removing duplicates...")
        
        seen_records = {}
        unique_data = []
        
        for record in data:
            # Create unique key from critical fields
            key_fields = [
                record.get('pickup_datetime', ''),
                record.get('dropoff_datetime', ''),
                record.get('pickup_longitude', ''),
                record.get('pickup_latitude', ''),
                record.get('trip_duration', '')
            ]
            
            unique_key = '|'.join(key_fields)
            
            if unique_key not in seen_records:
                seen_records[unique_key] = True
                unique_data.append(record)
            else:
                self.stats['duplicates_removed'] += 1
        
        print(f"Removed {self.stats['duplicates_removed']} duplicates")
        return unique_data
    
    def _fix_missing_values(self, data: List[Dict]) -> List[Dict]:
        """Handle missing values with appropriate strategies"""
        print("Fixing missing values...")
        
        for record in data:
            fixed = False
            
            # Fix missing passenger count (default to 1)
            if not record.get('passenger_count') or record['passenger_count'] == '':
                record['passenger_count'] = '1'
                fixed = True
            
            # Fix missing store_and_fwd_flag (default to 'N')
            if not record.get('store_and_fwd_flag') or record['store_and_fwd_flag'] == '':
                record['store_and_fwd_flag'] = 'N'
                fixed = True
            
            # Fix missing vendor_id (default to 1)
            if not record.get('vendor_id') or record['vendor_id'] == '':
                record['vendor_id'] = '1'
                fixed = True
            
            if fixed:
                self.stats['missing_values_fixed'] += 1
        
        print(f"Fixed {self.stats['missing_values_fixed']} missing values")
        return data
    
    def _validate_coordinates(self, data: List[Dict]) -> List[Dict]:
        """Validate geographic coordinates"""
        print("Validating coordinates...")
        
        valid_data = []
        
        for record in data:
            try:
                pickup_lon = float(record.get('pickup_longitude', 0))
                pickup_lat = float(record.get('pickup_latitude', 0))
                dropoff_lon = float(record.get('dropoff_longitude', 0))
                dropoff_lat = float(record.get('dropoff_latitude', 0))
                
                # Check if coordinates are within NYC bounds
                valid_pickup = (self.nyc_bounds['min_lat'] <= pickup_lat <= self.nyc_bounds['max_lat'] and
                               self.nyc_bounds['min_lon'] <= pickup_lon <= self.nyc_bounds['max_lon'])
                
                valid_dropoff = (self.nyc_bounds['min_lat'] <= dropoff_lat <= self.nyc_bounds['max_lat'] and
                                self.nyc_bounds['min_lon'] <= dropoff_lon <= self.nyc_bounds['max_lon'])
                
                if valid_pickup and valid_dropoff:
                    valid_data.append(record)
                else:
                    self.stats['coordinate_errors'] += 1
                    record['validity_flag'] = 'INVALID_COORDINATES'
            
            except (ValueError, TypeError):
                self.stats['coordinate_errors'] += 1
                record['validity_flag'] = 'INVALID_COORDINATES'
        
        print(f"Removed {self.stats['coordinate_errors']} records with invalid coordinates")
        return valid_data
    
    def _validate_datetime(self, data: List[Dict]) -> List[Dict]:
        """Validate datetime fields"""
        print("Validating datetime fields...")
        
        valid_data = []
        
        for record in data:
            try:
                pickup_dt = datetime.strptime(record['pickup_datetime'], '%Y-%m-%d %H:%M:%S')
                dropoff_dt = datetime.strptime(record['dropoff_datetime'], '%Y-%m-%d %H:%M:%S')
                
                # Check if dropoff is after pickup
                if dropoff_dt > pickup_dt:
                    # Calculate actual duration
                    actual_duration = int((dropoff_dt - pickup_dt).total_seconds())
                    record['calculated_duration'] = str(actual_duration)
                    valid_data.append(record)
                else:
                    self.stats['datetime_errors'] += 1
                    record['validity_flag'] = 'INVALID_DATETIME'
            
            except (ValueError, TypeError):
                self.stats['datetime_errors'] += 1
                record['validity_flag'] = 'INVALID_DATETIME'
        
        print(f"Removed {self.stats['datetime_errors']} records with invalid datetime")
        return valid_data
    
    def _validate_trip_duration(self, data: List[Dict]) -> List[Dict]:
        """Validate trip duration constraints"""
        print("Validating trip duration...")
        
        valid_data = []
        
        for record in data:
            try:
                trip_duration = int(record.get('trip_duration', 0))
                passenger_count = int(record.get('passenger_count', 1))
                
                # Check duration bounds
                valid_duration = (self.trip_constraints['min_duration'] <= 
                                trip_duration <= self.trip_constraints['max_duration'])
                
                # Check passenger count
                valid_passengers = (1 <= passenger_count <= self.trip_constraints['max_passenger'])
                
                if valid_duration and valid_passengers:
                    valid_data.append(record)
                else:
                    self.stats['duration_errors'] += 1
                    record['validity_flag'] = 'INVALID_DURATION_OR_PASSENGERS'
            
            except (ValueError, TypeError):
                self.stats['duration_errors'] += 1
                record['validity_flag'] = 'INVALID_DURATION_OR_PASSENGERS'
        
        print(f"Removed {self.stats['duration_errors']} records with invalid duration/passengers")
        return valid_data
    
    def _detect_outliers(self, data: List[Dict]) -> List[Dict]:
        """Detect outliers using custom algorithm with sampling for large datasets"""
        print("Detecting outliers...")
        
        # Extract trip durations for outlier analysis
        durations = []
        for record in data:
            try:
                duration = float(record.get('trip_duration', 0))
                durations.append(duration)
            except (ValueError, TypeError):
                durations.append(0)
        
        # For large datasets, use sampling to calculate thresholds faster
        if len(durations) > 100000:
            print(f"Large dataset detected ({len(durations)} records). Using sampling for outlier detection...")
            import random
            sample_size = min(50000, len(durations))
            sample_durations = random.sample(durations, sample_size)
            _, outlier_stats = self.algorithms.detect_outliers_iqr(sample_durations, multiplier=2.0)
            
            # Apply thresholds to full dataset
            q1, q3 = outlier_stats['q1'], outlier_stats['q3']
            iqr = q3 - q1
            lower_bound = q1 - 2.0 * iqr
            upper_bound = q3 + 2.0 * iqr
            
            outlier_indices = set()
            for i, duration in enumerate(durations):
                if duration < lower_bound or duration > upper_bound:
                    outlier_indices.add(i)
        else:
            # Use full outlier detection for smaller datasets
            outlier_indices, outlier_stats = self.algorithms.detect_outliers_iqr(durations, multiplier=2.0)
            outlier_indices = set(outlier_indices)
        
        # Mark outliers but keep them with flag
        for i, record in enumerate(data):
            if i in outlier_indices:
                record['outlier_flag'] = 'DURATION_OUTLIER'
                self.stats['outliers_detected'] += 1
            else:
                record['outlier_flag'] = 'NORMAL'
        
        print(f"Detected {self.stats['outliers_detected']} outliers")
        if 'outlier_stats' in locals():
            print(f"Outlier statistics: {outlier_stats}")
        
        return data
    
    def _write_cleaned_data(self, data: List[Dict]):
        """Write cleaned data to output file"""
        print(f"Writing cleaned data to {self.output_file}...")
        
        if not data:
            print("No valid data to write")
            return
        
        # Define output columns
        output_columns = [
            'id', 'vendor_id', 'pickup_datetime', 'dropoff_datetime',
            'passenger_count', 'pickup_longitude', 'pickup_latitude',
            'dropoff_longitude', 'dropoff_latitude', 'store_and_fwd_flag',
            'trip_duration', 'calculated_duration', 'outlier_flag'
        ]
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write header
                writer.writerow(output_columns)
                
                # Write data rows
                for record in data:
                    row = []
                    for col in output_columns:
                        row.append(record.get(col, ''))
                    writer.writerow(row)
                
                self.stats['valid_records'] = len(data)
                self.stats['invalid_records'] = (self.stats['total_records'] - 
                                               self.stats['valid_records'])
        
        except Exception as e:
            print(f"Error writing cleaned data: {e}")
            sys.exit(1)
    
    def _generate_cleaning_report(self):
        """Generate detailed cleaning report"""
        report_file = self.output_file.replace('.csv', '_cleaning_report.txt')
        
        with open(report_file, 'w') as file:
            file.write("NYC TAXI DATA CLEANING REPORT\n")
            file.write("=" * 50 + "\n\n")
            
            file.write(f"Input file: {self.input_file}\n")
            file.write(f"Output file: {self.output_file}\n")
            file.write(f"Cleaning date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            file.write("CLEANING STATISTICS:\n")
            file.write("-" * 30 + "\n")
            for key, value in self.stats.items():
                file.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
            
            # Calculate percentages
            if self.stats['total_records'] > 0:
                valid_pct = (self.stats['valid_records'] / self.stats['total_records']) * 100
                file.write(f"\nData Quality: {valid_pct:.2f}% valid records\n")
            
            file.write("\nCLEANING ASSUMPTIONS:\n")
            file.write("-" * 30 + "\n")
            file.write("• Missing passenger_count defaulted to 1\n")
            file.write("• Missing store_and_fwd_flag defaulted to 'N'\n")
            file.write("• Missing vendor_id defaulted to 1\n")
            file.write("• Trip duration must be between 1 minute and 1 hour\n")
            file.write("• Coordinates must be within NYC boundaries\n")
            file.write("• Outliers detected using IQR method (2.0 multiplier)\n")
            
            file.write(f"\nNYC COORDINATE BOUNDS USED:\n")
            file.write("-" * 30 + "\n")
            for key, value in self.nyc_bounds.items():
                file.write(f"{key}: {value}\n")
        
        print(f"Cleaning report saved to {report_file}")


def main():
    """Main execution function"""
    input_file = "../train.csv"
    output_file = "cleaned_taxi_data.csv"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        print("Please ensure train.csv is in the parent directory")
        return
    
    # Create cleaner and run pipeline
    cleaner = TaxiDataCleaner(input_file, output_file)
    stats = cleaner.clean_dataset()
    
    print("\n" + "=" * 50)
    print("DATA CLEANING COMPLETED")
    print("=" * 50)
    print(f"Total records processed: {stats['total_records']:,}")
    print(f"Valid records: {stats['valid_records']:,}")
    print(f"Invalid records: {stats['invalid_records']:,}")
    print(f"Data quality: {(stats['valid_records']/stats['total_records']*100):.2f}%")
    print(f"Cleaned data saved to: {output_file}")


if __name__ == "__main__":
    main()
