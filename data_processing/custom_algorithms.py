"""
Custom Algorithms Implementation
Manual implementations without using built-in library functions
"""

import math
from typing import List, Tuple, Dict, Any

class CustomAlgorithms:
    """
    Custom implementations of common algorithms for data processing
    No use of built-in sorting, filtering, or statistical functions
    """
    
    def __init__(self):
        self.comparison_count = 0
        self.swap_count = 0
    
    def quick_sort(self, arr: List[Tuple], key_index: int = 0, reverse: bool = False) -> List[Tuple]:
        """
        Manual implementation of QuickSort algorithm
        Time Complexity: O(n log n) average, O(n²) worst case
        Space Complexity: O(log n) average
        
        Args:
            arr: List of tuples to sort
            key_index: Index of tuple element to sort by
            reverse: Sort in descending order if True
        """
        if len(arr) <= 1:
            return arr
        
        pivot = arr[len(arr) // 2]
        pivot_value = pivot[key_index]
        
        left = []
        middle = []
        right = []
        
        for item in arr:
            self.comparison_count += 1
            item_value = item[key_index]
            
            if (not reverse and item_value < pivot_value) or (reverse and item_value > pivot_value):
                left.append(item)
            elif item_value == pivot_value:
                middle.append(item)
            else:
                right.append(item)
        
        return (self.quick_sort(left, key_index, reverse) + 
                middle + 
                self.quick_sort(right, key_index, reverse))
    
    def custom_filter(self, data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """
        Custom filtering implementation without using built-in filter()
        Time Complexity: O(n * m) where m is number of filter conditions
        Space Complexity: O(k) where k is number of matching records
        """
        filtered_data = []
        
        for record in data:
            matches_all_filters = True
            
            for field, condition in filters.items():
                if field not in record:
                    matches_all_filters = False
                    break
                
                record_value = record[field]
                
                # Handle different condition types
                if isinstance(condition, dict):
                    if 'min' in condition and record_value < condition['min']:
                        matches_all_filters = False
                        break
                    if 'max' in condition and record_value > condition['max']:
                        matches_all_filters = False
                        break
                    if 'in' in condition and record_value not in condition['in']:
                        matches_all_filters = False
                        break
                elif isinstance(condition, (list, tuple)):
                    if record_value not in condition:
                        matches_all_filters = False
                        break
                else:
                    if record_value != condition:
                        matches_all_filters = False
                        break
            
            if matches_all_filters:
                filtered_data.append(record)
        
        return filtered_data
    
    def calculate_percentiles(self, values: List[float], percentiles: List[int]) -> Dict[int, float]:
        """
        Manual percentile calculation without using numpy.percentile
        Time Complexity: O(n log n) for sorting + O(p) for percentile calculation
        Space Complexity: O(n) for sorted copy
        """
        if not values:
            return {p: 0.0 for p in percentiles}
        
        # Sort values manually using our quick_sort
        sorted_tuples = self.quick_sort([(v, i) for i, v in enumerate(values)], key_index=0)
        sorted_values = [t[0] for t in sorted_tuples]
        
        n = len(sorted_values)
        result = {}
        
        for p in percentiles:
            if p < 0 or p > 100:
                continue
            
            if p == 0:
                result[p] = sorted_values[0]
            elif p == 100:
                result[p] = sorted_values[-1]
            else:
                # Calculate position
                position = (p / 100.0) * (n - 1)
                lower_index = int(position)
                upper_index = min(lower_index + 1, n - 1)
                
                # Linear interpolation
                weight = position - lower_index
                result[p] = (sorted_values[lower_index] * (1 - weight) + 
                           sorted_values[upper_index] * weight)
        
        return result
    
    def detect_outliers_iqr(self, values: List[float], multiplier: float = 1.5) -> Tuple[List[int], Dict[str, float]]:
        """
        Manual outlier detection using IQR method
        Time Complexity: O(n log n)
        Space Complexity: O(n)
        """
        if len(values) < 4:
            return [], {}
        
        percentiles = self.calculate_percentiles(values, [25, 75])
        q1 = percentiles[25]
        q3 = percentiles[75]
        
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        stats = {
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outlier_count': len(outlier_indices)
        }
        
        return outlier_indices, stats
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two points
        Manual implementation without using geopy
        Time Complexity: O(1)
        Space Complexity: O(1)
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
    
    def custom_group_by(self, data: List[Dict], group_key: str) -> Dict[str, List[Dict]]:
        """
        Manual group by implementation
        Time Complexity: O(n)
        Space Complexity: O(n)
        """
        groups = {}
        
        for record in data:
            if group_key in record:
                key_value = record[group_key]
                if key_value not in groups:
                    groups[key_value] = []
                groups[key_value].append(record)
        
        return groups
    
    def calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        Manual statistical calculations
        Time Complexity: O(n)
        Space Complexity: O(1)
        """
        if not values:
            return {}
        
        n = len(values)
        
        # Calculate mean
        total = 0.0
        for value in values:
            total += value
        mean = total / n
        
        # Calculate variance and standard deviation
        variance_sum = 0.0
        min_val = values[0]
        max_val = values[0]
        
        for value in values:
            variance_sum += (value - mean) ** 2
            if value < min_val:
                min_val = value
            if value > max_val:
                max_val = value
        
        variance = variance_sum / n
        std_dev = math.sqrt(variance)
        
        return {
            'count': n,
            'mean': mean,
            'variance': variance,
            'std_dev': std_dev,
            'min': min_val,
            'max': max_val,
            'range': max_val - min_val
        }
    
    def find_top_k(self, data: List[Tuple], k: int, key_index: int = 0) -> List[Tuple]:
        """
        Find top K elements using manual heap implementation
        Time Complexity: O(n log k)
        Space Complexity: O(k)
        """
        if k >= len(data):
            return self.quick_sort(data, key_index, reverse=True)
        
        # Min heap to maintain top k elements
        heap = []
        
        for item in data:
            if len(heap) < k:
                heap.append(item)
                self._heapify_up(heap, len(heap) - 1, key_index)
            elif item[key_index] > heap[0][key_index]:
                heap[0] = item
                self._heapify_down(heap, 0, key_index)
        
        # Sort the heap to get descending order
        return self.quick_sort(heap, key_index, reverse=True)
    
    def _heapify_up(self, heap: List[Tuple], index: int, key_index: int):
        """Helper method for heap operations"""
        parent_index = (index - 1) // 2
        
        if index > 0 and heap[index][key_index] < heap[parent_index][key_index]:
            heap[index], heap[parent_index] = heap[parent_index], heap[index]
            self.swap_count += 1
            self._heapify_up(heap, parent_index, key_index)
    
    def _heapify_down(self, heap: List[Tuple], index: int, key_index: int):
        """Helper method for heap operations"""
        left_child = 2 * index + 1
        right_child = 2 * index + 2
        smallest = index
        
        if (left_child < len(heap) and 
            heap[left_child][key_index] < heap[smallest][key_index]):
            smallest = left_child
        
        if (right_child < len(heap) and 
            heap[right_child][key_index] < heap[smallest][key_index]):
            smallest = right_child
        
        if smallest != index:
            heap[index], heap[smallest] = heap[smallest], heap[index]
            self.swap_count += 1
            self._heapify_down(heap, smallest, key_index)
    
    def reset_counters(self):
        """Reset performance counters"""
        self.comparison_count = 0
        self.swap_count = 0
    
    def get_performance_stats(self) -> Dict[str, int]:
        """Get algorithm performance statistics"""
        return {
            'comparisons': self.comparison_count,
            'swaps': self.swap_count
        }


# Example usage and testing
if __name__ == "__main__":
    algorithms = CustomAlgorithms()
    
    # Test data
    test_data = [
        (45.2, "trip1"), (23.8, "trip2"), (67.1, "trip3"), 
        (12.5, "trip4"), (89.3, "trip5"), (34.7, "trip6")
    ]
    
    print("Original data:", test_data)
    
    # Test sorting
    sorted_data = algorithms.quick_sort(test_data, key_index=0)
    print("Sorted data:", sorted_data)
    
    # Test statistics
    values = [t[0] for t in test_data]
    stats = algorithms.calculate_statistics(values)
    print("Statistics:", stats)
    
    # Test percentiles
    percentiles = algorithms.calculate_percentiles(values, [25, 50, 75, 95])
    print("Percentiles:", percentiles)
    
    # Test outlier detection
    outliers, outlier_stats = algorithms.detect_outliers_iqr(values)
    print("Outliers:", outliers, outlier_stats)
    
    print("Performance:", algorithms.get_performance_stats())
