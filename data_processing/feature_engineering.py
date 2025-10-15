"""
Feature Engineering Pipeline
Creates derived features from cleaned taxi data
"""

import csv
import math
from datetime import datetime
from typing import Dict, List, Any
from custom_algorithms import CustomAlgorithms

class TaxiFeatureEngineer:
    """
    Feature engineering pipeline for taxi data analysis
    Creates meaningful derived features for analysis
    """
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.algorithms = CustomAlgorithms()
        
        # Feature engineering statistics
        self.stats = {
            'records_processed': 0,
            'features_created': 0,
            'distance_calculations': 0,
            'time_features': 0,
            'efficiency_metrics': 0
        }
        
        # NYC borough approximate centers for zone classification
        self.borough_centers = {
            'Manhattan': (40.7831, -73.9712),
            'Brooklyn': (40.6782, -73.9442),
            'Queens': (40.7282, -73.7949),
            'Bronx': (40.8448, -73.8648),
            'Staten Island': (40.5795, -74.1502)
        }
    
    def engineer_features(self) -> Dict[str, Any]:
        """
        Main feature engineering pipeline
        """
        print("Starting feature engineering...")
        
        # Load cleaned data
        data = self._load_cleaned_data()
        print(f"Loaded {len(data)} cleaned records")
        
        # Engineer features
        enhanced_data = self._calculate_trip_distance(data)
        enhanced_data = self._calculate_trip_speed(enhanced_data)
        enhanced_data = self._extract_temporal_features(enhanced_data)
        enhanced_data = self._calculate_efficiency_metrics(enhanced_data)
        enhanced_data = self._classify_trip_zones(enhanced_data)
        enhanced_data = self._detect_trip_patterns(enhanced_data)
        
        # Save enhanced data
        self._save_enhanced_data(enhanced_data)
        
        # Generate feature report
        self._generate_feature_report(enhanced_data)
        
        return self.stats
    
    def _load_cleaned_data(self) -> List[Dict[str, Any]]:
        """Load cleaned taxi data"""
        data = []
        
        with open(self.input_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
                self.stats['records_processed'] += 1
        
        return data
    
    def _calculate_trip_distance(self, data: List[Dict]) -> List[Dict]:
        """
        Calculate trip distance using Haversine formula
        DERIVED FEATURE 1: Trip Distance
        """
        print("Calculating trip distances...")
        
        for record in data:
            try:
                pickup_lat = float(record['pickup_latitude'])
                pickup_lon = float(record['pickup_longitude'])
                dropoff_lat = float(record['dropoff_latitude'])
                dropoff_lon = float(record['dropoff_longitude'])
                
                # Use custom distance calculation
                distance_km = self.algorithms.calculate_distance(
                    pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
                )
                
                record['trip_distance_km'] = f"{distance_km:.3f}"
                self.stats['distance_calculations'] += 1
                self.stats['features_created'] += 1
                
            except (ValueError, TypeError, KeyError):
                record['trip_distance_km'] = "0.000"
        
        print(f"Calculated distances for {self.stats['distance_calculations']} trips")
        return data
    
    def _calculate_trip_speed(self, data: List[Dict]) -> List[Dict]:
        """
        Calculate average trip speed
        DERIVED FEATURE 2: Trip Speed (km/h)
        """
        print("Calculating trip speeds...")
        
        for record in data:
            try:
                distance_km = float(record.get('trip_distance_km', 0))
                duration_seconds = float(record.get('trip_duration', 0))
                
                if duration_seconds > 0:
                    # Convert to hours and calculate speed
                    duration_hours = duration_seconds / 3600.0
                    speed_kmh = distance_km / duration_hours
                    
                    record['trip_speed_kmh'] = f"{speed_kmh:.2f}"
                else:
                    record['trip_speed_kmh'] = "0.00"
                
                self.stats['features_created'] += 1
                
            except (ValueError, TypeError, KeyError):
                record['trip_speed_kmh'] = "0.00"
        
        return data
    
    def _extract_temporal_features(self, data: List[Dict]) -> List[Dict]:
        """
        Extract time-based features
        DERIVED FEATURE 3: Temporal Analysis Features
        """
        print("Extracting temporal features...")
        
        for record in data:
            try:
                pickup_dt = datetime.strptime(record['pickup_datetime'], '%Y-%m-%d %H:%M:%S')
                
                # Hour of day
                hour = pickup_dt.hour
                record['pickup_hour'] = str(hour)
                
                # Time of day classification
                if 5 <= hour < 12:
                    time_period = "Morning"
                elif 12 <= hour < 17:
                    time_period = "Afternoon"
                elif 17 <= hour < 21:
                    time_period = "Evening"
                else:
                    time_period = "Night"
                
                record['time_of_day'] = time_period
                
                # Day of week
                day_of_week = pickup_dt.strftime('%A')
                record['day_of_week'] = day_of_week
                
                # Weekend indicator
                is_weekend = day_of_week in ['Saturday', 'Sunday']
                record['is_weekend'] = 'True' if is_weekend else 'False'
                
                # Month
                record['pickup_month'] = str(pickup_dt.month)
                
                # Rush hour indicator
                is_rush_hour = ((7 <= hour <= 9) or (17 <= hour <= 19)) and not is_weekend
                record['is_rush_hour'] = 'True' if is_rush_hour else 'False'
                
                self.stats['time_features'] += 6
                self.stats['features_created'] += 6
                
            except (ValueError, TypeError, KeyError):
                record['pickup_hour'] = "0"
                record['time_of_day'] = "Unknown"
                record['day_of_week'] = "Unknown"
                record['is_weekend'] = "False"
                record['pickup_month'] = "1"
                record['is_rush_hour'] = "False"
        
        return data
    
    def _calculate_efficiency_metrics(self, data: List[Dict]) -> List[Dict]:
        """
        Calculate trip efficiency metrics
        DERIVED FEATURE 4: Trip Efficiency and Performance Metrics
        """
        print("Calculating efficiency metrics...")
        
        for record in data:
            try:
                distance_km = float(record.get('trip_distance_km', 0))
                duration_seconds = float(record.get('trip_duration', 0))
                speed_kmh = float(record.get('trip_speed_kmh', 0))
                
                # Distance per minute
                duration_minutes = duration_seconds / 60.0
                if duration_minutes > 0:
                    distance_per_minute = distance_km / duration_minutes
                    record['distance_per_minute'] = f"{distance_per_minute:.4f}"
                else:
                    record['distance_per_minute'] = "0.0000"
                
                # Idle time estimation (time spent not moving)
                if speed_kmh > 0:
                    theoretical_time = (distance_km / speed_kmh) * 3600  # in seconds
                    idle_time = max(0, duration_seconds - theoretical_time)
                    record['estimated_idle_time'] = f"{idle_time:.0f}"
                else:
                    record['estimated_idle_time'] = str(duration_seconds)
                
                # Efficiency score (0-100, higher is better)
                max_reasonable_speed = 40  # km/h in city traffic
                if speed_kmh > 0:
                    efficiency = min(100, (speed_kmh / max_reasonable_speed) * 100)
                    record['efficiency_score'] = f"{efficiency:.1f}"
                else:
                    record['efficiency_score'] = "0.0"
                
                # Trip complexity (based on distance and duration relationship)
                if distance_km > 0 and duration_seconds > 0:
                    # Expected duration for distance at average city speed (20 km/h)
                    expected_duration = (distance_km / 20) * 3600
                    complexity_ratio = duration_seconds / expected_duration
                    record['trip_complexity'] = f"{complexity_ratio:.2f}"
                else:
                    record['trip_complexity'] = "1.00"
                
                self.stats['efficiency_metrics'] += 4
                self.stats['features_created'] += 4
                
            except (ValueError, TypeError, KeyError):
                record['distance_per_minute'] = "0.0000"
                record['estimated_idle_time'] = "0"
                record['efficiency_score'] = "0.0"
                record['trip_complexity'] = "1.00"
        
        return data
    
    def _classify_trip_zones(self, data: List[Dict]) -> List[Dict]:
        """
        Classify pickup and dropoff zones
        """
        print("Classifying trip zones...")
        
        for record in data:
            try:
                pickup_lat = float(record['pickup_latitude'])
                pickup_lon = float(record['pickup_longitude'])
                dropoff_lat = float(record['dropoff_latitude'])
                dropoff_lon = float(record['dropoff_longitude'])
                
                # Find closest borough for pickup
                pickup_borough = self._find_closest_borough(pickup_lat, pickup_lon)
                record['pickup_borough'] = pickup_borough
                
                # Find closest borough for dropoff
                dropoff_borough = self._find_closest_borough(dropoff_lat, dropoff_lon)
                record['dropoff_borough'] = dropoff_borough
                
                # Trip type classification
                if pickup_borough == dropoff_borough:
                    record['trip_type'] = "Intra-borough"
                else:
                    record['trip_type'] = "Inter-borough"
                
                self.stats['features_created'] += 3
                
            except (ValueError, TypeError, KeyError):
                record['pickup_borough'] = "Unknown"
                record['dropoff_borough'] = "Unknown"
                record['trip_type'] = "Unknown"
        
        return data
    
    def _find_closest_borough(self, lat: float, lon: float) -> str:
        """Find the closest borough based on distance to borough centers"""
        min_distance = float('inf')
        closest_borough = "Manhattan"  # Default
        
        for borough, (b_lat, b_lon) in self.borough_centers.items():
            distance = self.algorithms.calculate_distance(lat, lon, b_lat, b_lon)
            if distance < min_distance:
                min_distance = distance
                closest_borough = borough
        
        return closest_borough
    
    def _detect_trip_patterns(self, data: List[Dict]) -> List[Dict]:
        """
        Detect interesting trip patterns
        """
        print("Detecting trip patterns...")
        
        # Calculate some basic statistics for pattern detection
        speeds = []
        distances = []
        durations = []
        
        for record in data:
            try:
                speeds.append(float(record.get('trip_speed_kmh', 0)))
                distances.append(float(record.get('trip_distance_km', 0)))
                durations.append(float(record.get('trip_duration', 0)))
            except (ValueError, TypeError):
                continue
        
        # Calculate percentiles using custom algorithm
        speed_percentiles = self.algorithms.calculate_percentiles(speeds, [10, 90])
        distance_percentiles = self.algorithms.calculate_percentiles(distances, [10, 90])
        duration_percentiles = self.algorithms.calculate_percentiles(durations, [10, 90])
        
        # Classify trips based on patterns
        for record in data:
            try:
                speed = float(record.get('trip_speed_kmh', 0))
                distance = float(record.get('trip_distance_km', 0))
                duration = float(record.get('trip_duration', 0))
                
                patterns = []
                
                # Speed patterns
                if speed < speed_percentiles[10]:
                    patterns.append("Slow")
                elif speed > speed_percentiles[90]:
                    patterns.append("Fast")
                
                # Distance patterns
                if distance < distance_percentiles[10]:
                    patterns.append("Short")
                elif distance > distance_percentiles[90]:
                    patterns.append("Long")
                
                # Duration patterns
                if duration < duration_percentiles[10]:
                    patterns.append("Quick")
                elif duration > duration_percentiles[90]:
                    patterns.append("Extended")
                
                # Special patterns
                if speed < 5:
                    patterns.append("Traffic")
                if distance < 0.5:
                    patterns.append("Local")
                if duration > 1800:  # 30 minutes
                    patterns.append("Journey")
                
                record['trip_patterns'] = ";".join(patterns) if patterns else "Normal"
                self.stats['features_created'] += 1
                
            except (ValueError, TypeError, KeyError):
                record['trip_patterns'] = "Unknown"
        
        return data
    
    def _save_enhanced_data(self, data: List[Dict]):
        """Save data with engineered features"""
        print(f"Saving enhanced data to {self.output_file}...")
        
        if not data:
            print("No data to save")
            return
        
        # Define all columns including new features
        all_columns = list(data[0].keys()) if data else []
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=all_columns)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Enhanced data saved with {len(all_columns)} columns")
    
    def _generate_feature_report(self, data: List[Dict]):
        """Generate feature engineering report"""
        report_file = self.output_file.replace('.csv', '_features_report.txt')
        
        with open(report_file, 'w') as file:
            file.write("FEATURE ENGINEERING REPORT\n")
            file.write("=" * 50 + "\n\n")
            
            file.write(f"Input file: {self.input_file}\n")
            file.write(f"Output file: {self.output_file}\n")
            file.write(f"Processing date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            file.write("FEATURE STATISTICS:\n")
            file.write("-" * 30 + "\n")
            for key, value in self.stats.items():
                file.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
            
            file.write("\nDERIVED FEATURES CREATED:\n")
            file.write("-" * 30 + "\n")
            file.write("1. Trip Distance (km) - Haversine distance calculation\n")
            file.write("2. Trip Speed (km/h) - Average speed during trip\n")
            file.write("3. Temporal Features - Hour, day, weekend, rush hour\n")
            file.write("4. Efficiency Metrics - Distance per minute, idle time, efficiency score\n")
            file.write("5. Zone Classification - Borough identification\n")
            file.write("6. Trip Patterns - Speed, distance, and duration classifications\n")
            
            file.write("\nFEATURE DESCRIPTIONS:\n")
            file.write("-" * 30 + "\n")
            
            feature_descriptions = {
                'trip_distance_km': 'Great circle distance between pickup and dropoff',
                'trip_speed_kmh': 'Average speed calculated from distance and duration',
                'distance_per_minute': 'Distance covered per minute of travel',
                'estimated_idle_time': 'Estimated time spent not moving (traffic, stops)',
                'efficiency_score': 'Trip efficiency score (0-100, higher is better)',
                'trip_complexity': 'Ratio of actual to expected duration',
                'pickup_borough': 'Estimated NYC borough for pickup location',
                'trip_type': 'Intra-borough or inter-borough classification',
                'time_of_day': 'Morning, Afternoon, Evening, or Night',
                'is_rush_hour': 'Whether trip occurred during rush hours',
                'trip_patterns': 'Speed, distance, and duration pattern classification'
            }
            
            for feature, description in feature_descriptions.items():
                file.write(f"{feature}: {description}\n")
            
            # Sample statistics
            if data:
                file.write(f"\nSAMPLE STATISTICS:\n")
                file.write("-" * 30 + "\n")
                
                sample_record = data[0]
                file.write("Sample enhanced record:\n")
                for key, value in sample_record.items():
                    if key.startswith(('trip_', 'pickup_', 'dropoff_', 'is_', 'time_', 'efficiency', 'distance_per')):
                        file.write(f"  {key}: {value}\n")
        
        print(f"Feature engineering report saved to {report_file}")


def main():
    """Main execution function"""
    input_file = "cleaned_taxi_data.csv"
    output_file = "enhanced_taxi_data.csv"
    
    # Check if input file exists
    import os
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found")
        print("Please run data_cleaner.py first")
        return
    
    # Create feature engineer and run pipeline
    engineer = TaxiFeatureEngineer(input_file, output_file)
    stats = engineer.engineer_features()
    
    print("\n" + "=" * 50)
    print("FEATURE ENGINEERING COMPLETED")
    print("=" * 50)
    print(f"Records processed: {stats['records_processed']:,}")
    print(f"Features created: {stats['features_created']:,}")
    print(f"Enhanced data saved to: {output_file}")


if __name__ == "__main__":
    main()
