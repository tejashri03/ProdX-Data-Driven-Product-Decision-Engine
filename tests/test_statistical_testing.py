"""
Unit tests for statistical testing module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.statistical_testing import ABTestStatisticalAnalyzer, TestResult

class TestStatisticalTesting(unittest.TestCase):
    """Test cases for ABTestStatisticalAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ABTestStatisticalAnalyzer(significance_level=0.05)
        
        # Create test data
        np.random.seed(42)
        n_users = 1000
        
        # Generate test data with known effects
        self.test_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(n_users)],
            'group': np.random.choice(['A', 'B'], n_users),
            'device': np.random.choice(['mobile', 'desktop'], n_users),
            'region': np.random.choice(['US', 'EU'], n_users),
            'new_user': np.random.choice([True, False], n_users),
            'viewed': np.random.choice([0, 1], n_users, p=[0.2, 0.8]),
            'clicked': np.random.choice([0, 1], n_users, p=[0.9, 0.1]),
            'purchased': np.random.choice([0, 1], n_users, p=[0.97, 0.03]),
            'time_spent': np.random.normal(120, 30, n_users),
            'timestamp': pd.date_range('2024-01-01', periods=n_users, freq='H')
        })
        
        # Ensure logical consistency
        self.test_data.loc[self.test_data['viewed'] == 0, 'clicked'] = 0
        self.test_data.loc[self.test_data['clicked'] == 0, 'purchased'] = 0
        self.test_data.loc[self.test_data['viewed'] == 0, 'time_spent'] = 0
    
    def test_calculate_conversion_rate(self):
        """Test conversion rate calculation"""
        rate_a = self.analyzer.calculate_conversion_rate(self.test_data, 'A')
        rate_b = self.analyzer.calculate_conversion_rate(self.test_data, 'B')
        
        # Check reasonable values
        self.assertGreaterEqual(rate_a, 0)
        self.assertLessEqual(rate_a, 1)
        self.assertGreaterEqual(rate_b, 0)
        self.assertLessEqual(rate_b, 1)
    
    def test_calculate_ctr(self):
        """Test click-through rate calculation"""
        ctr_a = self.analyzer.calculate_ctr(self.test_data, 'A')
        ctr_b = self.analyzer.calculate_ctr(self.test_data, 'B')
        
        # Check reasonable values
        self.assertGreaterEqual(ctr_a, 0)
        self.assertLessEqual(ctr_a, 1)
        self.assertGreaterEqual(ctr_b, 0)
        self.assertLessEqual(ctr_b, 1)
    
    def test_calculate_view_rate(self):
        """Test view rate calculation"""
        view_a = self.analyzer.calculate_view_rate(self.test_data, 'A')
        view_b = self.analyzer.calculate_view_rate(self.test_data, 'B')
        
        # Check reasonable values
        self.assertGreaterEqual(view_a, 0)
        self.assertLessEqual(view_a, 1)
        self.assertGreaterEqual(view_b, 0)
        self.assertLessEqual(view_b, 1)
    
    def test_two_proportion_z_test(self):
        """Test two-proportion Z-test"""
        # Test with known values
        z_stat, p_value, ci = self.analyzer.two_proportion_z_test(
            control_successes=100, control_n=1000,
            treatment_successes=150, treatment_n=1000
        )
        
        # Check return types
        self.assertIsInstance(z_stat, float)
        self.assertIsInstance(p_value, float)
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        
        # Check reasonable values
        self.assertGreater(abs(z_stat), 0)  # Should be non-zero for different proportions
        self.assertGreaterEqual(p_value, 0)
        self.assertLessEqual(p_value, 1)
        
        # Test with identical proportions (should have high p-value)
        z_stat_same, p_value_same, ci_same = self.analyzer.two_proportion_z_test(
            control_successes=100, control_n=1000,
            treatment_successes=100, treatment_n=1000
        )
        
        self.assertGreater(p_value_same, 0.5)  # Should be non-significant
    
    def test_test_conversion_rate(self):
        """Test conversion rate testing"""
        result = self.analyzer.test_conversion_rate(self.test_data)
        
        # Check return type
        self.assertIsInstance(result, TestResult)
        
        # Check required attributes
        required_attrs = [
            'metric', 'control_rate', 'treatment_rate', 'absolute_difference',
            'relative_difference', 'p_value', 'confidence_interval',
            'is_significant', 'test_statistic', 'sample_size_control', 'sample_size_treatment'
        ]
        
        for attr in required_attrs:
            self.assertTrue(hasattr(result, attr))
        
        # Check reasonable values
        self.assertEqual(result.metric, "Conversion Rate")
        self.assertGreaterEqual(result.control_rate, 0)
        self.assertLessEqual(result.control_rate, 1)
        self.assertGreaterEqual(result.treatment_rate, 0)
        self.assertLessEqual(result.treatment_rate, 1)
        self.assertGreaterEqual(result.p_value, 0)
        self.assertLessEqual(result.p_value, 1)
        self.assertEqual(len(result.confidence_interval), 2)
        self.assertIn(result.is_significant, [True, False])
    
    def test_test_ctr(self):
        """Test CTR testing"""
        result = self.analyzer.test_ctr(self.test_data)
        
        # Check return type and basic structure
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.metric, "Click-Through Rate")
        
        # Check reasonable values
        self.assertGreaterEqual(result.control_rate, 0)
        self.assertLessEqual(result.control_rate, 1)
        self.assertGreaterEqual(result.treatment_rate, 0)
        self.assertLessEqual(result.treatment_rate, 1)
    
    def test_test_view_rate(self):
        """Test view rate testing"""
        result = self.analyzer.test_view_rate(self.test_data)
        
        # Check return type and basic structure
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.metric, "View Rate")
        
        # Check reasonable values
        self.assertGreaterEqual(result.control_rate, 0)
        self.assertLessEqual(result.control_rate, 1)
        self.assertGreaterEqual(result.treatment_rate, 0)
        self.assertLessEqual(result.treatment_rate, 1)
    
    def test_test_time_spent(self):
        """Test time spent testing"""
        result = self.analyzer.test_time_spent(self.test_data)
        
        # Check return type
        self.assertIsInstance(result, dict)
        
        # Check required keys
        required_keys = [
            'metric', 'control_mean', 'treatment_mean', 'absolute_difference',
            'relative_difference', 'p_value', 'is_significant',
            'sample_size_control', 'sample_size_treatment'
        ]
        
        for key in required_keys:
            self.assertIn(key, result)
        
        # Check reasonable values
        self.assertEqual(result['metric'], "Time Spent")
        self.assertGreater(result['control_mean'], 0)
        self.assertGreater(result['treatment_mean'], 0)
        self.assertGreaterEqual(result['p_value'], 0)
        self.assertLessEqual(result['p_value'], 1)
    
    def test_segment_analysis(self):
        """Test segment analysis"""
        segments = self.analyzer.segment_analysis(self.test_data, 'device')
        
        # Check return type
        self.assertIsInstance(segments, dict)
        
        # Check segments
        for device in ['mobile', 'desktop']:
            if device in segments:
                segment_result = segments[device]
                self.assertIn('conversion', segment_result)
                self.assertIn('ctr', segment_result)
                self.assertIn('sample_size', segment_result)
                
                # Check conversion result structure
                conv_result = segment_result['conversion']
                self.assertIsInstance(conv_result, TestResult)
    
    def test_calculate_sample_size(self):
        """Test sample size calculation"""
        sample_size = self.analyzer.calculate_sample_size(
            baseline_rate=0.1, minimum_detectable_effect=0.05
        )
        
        # Check return type and reasonable value
        self.assertIsInstance(sample_size, int)
        self.assertGreater(sample_size, 0)
        self.assertLess(sample_size, 100000)  # Should be reasonable
        
        # Test with different parameters
        sample_size_small = self.analyzer.calculate_sample_size(
            baseline_rate=0.5, minimum_detectable_effect=0.01
        )
        sample_size_large = self.analyzer.calculate_sample_size(
            baseline_rate=0.01, minimum_detectable_effect=0.1
        )
        
        # Smaller effect should require larger sample size
        self.assertGreater(sample_size_small, sample_size_large)
    
    def test_power_analysis(self):
        """Test power analysis"""
        power_conv = self.analyzer.power_analysis(self.test_data, 'conversion')
        power_ctr = self.analyzer.power_analysis(self.test_data, 'ctr')
        
        # Check return types
        self.assertIsInstance(power_conv, dict)
        self.assertIsInstance(power_ctr, dict)
        
        # Check required keys
        required_keys = ['metric', 'effect_size', 'power', 'sample_size_control', 'sample_size_treatment']
        
        for key in required_keys:
            self.assertIn(key, power_conv)
            self.assertIn(key, power_ctr)
        
        # Check reasonable values
        self.assertGreaterEqual(power_conv['power'], 0)
        self.assertLessEqual(power_conv['power'], 1)
        self.assertGreaterEqual(power_ctr['power'], 0)
        self.assertLessEqual(power_ctr['power'], 1)
    
    def test_run_full_analysis(self):
        """Test full analysis pipeline"""
        results = self.analyzer.run_full_analysis(self.test_data)
        
        # Check return type
        self.assertIsInstance(results, dict)
        
        # Check main results
        main_results = ['conversion', 'ctr', 'view_rate', 'time_spent']
        for result in main_results:
            self.assertIn(result, results)
        
        # Check segment results
        segment_results = ['device_segments', 'new_user_segments', 'region_segments']
        for segment in segment_results:
            self.assertIn(segment, results)
        
        # Check power analysis
        self.assertIn('power_conversion', results)
        self.assertIn('power_ctr', results)
        
        # Check sample size calculation
        self.assertIn('required_sample_size', results)
    
    def test_generate_report(self):
        """Test report generation"""
        results = self.analyzer.run_full_analysis(self.test_data)
        report = self.analyzer.generate_report(results)
        
        # Check return type
        self.assertIsInstance(report, str)
        
        # Check content
        self.assertIn("A/B TEST STATISTICAL ANALYSIS REPORT", report)
        self.assertIn("PRIMARY METRICS", report)
        self.assertIn("Conversion Rate", report)
        self.assertIn("POWER ANALYSIS", report)
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty data
        empty_df = pd.DataFrame(columns=self.test_data.columns)
        
        # Should handle empty data gracefully
        rate_empty = self.analyzer.calculate_conversion_rate(empty_df, 'A')
        self.assertEqual(rate_empty, 0.0)
        
        # Data with no successes
        no_success_df = self.test_data.copy()
        no_success_df['purchased'] = 0
        
        rate_no_success = self.analyzer.calculate_conversion_rate(no_success_df, 'A')
        self.assertEqual(rate_no_success, 0.0)
        
        # Invalid group
        rate_invalid = self.analyzer.calculate_conversion_rate(self.test_data, 'C')
        self.assertEqual(rate_invalid, 0.0)

if __name__ == '__main__':
    unittest.main()
