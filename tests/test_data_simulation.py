"""
Unit tests for data simulation module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_simulation import ABTestDataGenerator

class TestDataSimulation(unittest.TestCase):
    """Test cases for ABTestDataGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = ABTestDataGenerator(seed=42)
        self.n_users = 1000
    
    def test_generate_user_ids(self):
        """Test user ID generation"""
        user_ids = self.generator.generate_user_ids(self.n_users)
        
        # Check length
        self.assertEqual(len(user_ids), self.n_users)
        
        # Check uniqueness
        self.assertEqual(len(set(user_ids)), len(user_ids))
        
        # Check format
        self.assertTrue(all(user_id.startswith('user_') for user_id in user_ids))
    
    def test_assign_groups(self):
        """Test group assignment"""
        user_ids = self.generator.generate_user_ids(self.n_users)
        groups = self.generator.assign_groups(user_ids)
        
        # Check length
        self.assertEqual(len(groups), len(user_ids))
        
        # Check valid groups
        valid_groups = set(groups)
        self.assertEqual(valid_groups, {'A', 'B'})
        
        # Check roughly equal split (within 5%)
        group_counts = pd.Series(groups).value_counts()
        ratio = min(group_counts) / max(group_counts)
        self.assertGreaterEqual(ratio, 0.45)
    
    def test_assign_devices(self):
        """Test device assignment"""
        devices = self.generator.assign_devices(self.n_users)
        
        # Check length
        self.assertEqual(len(devices), self.n_users)
        
        # Check valid devices
        valid_devices = set(devices)
        expected_devices = {'mobile', 'desktop', 'tablet'}
        self.assertEqual(valid_devices, expected_devices)
        
        # Check distribution roughly matches expected
        device_counts = pd.Series(devices).value_counts()
        mobile_ratio = device_counts['mobile'] / self.n_users
        self.assertGreater(mobile_ratio, 0.5)  # Should be around 65%
    
    def test_simulate_user_behavior(self):
        """Test user behavior simulation"""
        # Test control group
        viewed, clicked, purchased, time_spent = self.generator.simulate_user_behavior(
            group='A', device='mobile', is_new_user=False
        )
        
        # Check logical constraints
        if not viewed:
            self.assertEqual(clicked, 0)
            self.assertEqual(purchased, 0)
            self.assertEqual(time_spent, 0)
        
        if not clicked:
            self.assertEqual(purchased, 0)
        
        # Check reasonable ranges
        self.assertIn(viewed, [0, 1])
        self.assertIn(clicked, [0, 1])
        self.assertIn(purchased, [0, 1])
        self.assertGreaterEqual(time_spent, 0)
        
        # Test treatment group
        viewed_t, clicked_t, purchased_t, time_spent_t = self.generator.simulate_user_behavior(
            group='B', device='mobile', is_new_user=False
        )
        
        # Treatment should generally perform better
        # (This is probabilistic, so we run multiple times)
        treatment_better = 0
        for _ in range(100):
            v, c, p, t = self.generator.simulate_user_behavior('A', 'mobile', False)
            v_t, c_t, p_t, t_t = self.generator.simulate_user_behavior('B', 'mobile', False)
            if p_t > p:
                treatment_better += 1
        
        # Treatment should be better in majority of cases
        self.assertGreater(treatment_better, 50)
    
    def test_generate_dataset(self):
        """Test complete dataset generation"""
        df = self.generator.generate_dataset()
        
        # Check shape
        self.assertEqual(len(df), self.n_users)
        expected_columns = [
            'user_id', 'group', 'device', 'region', 'new_user',
            'viewed', 'clicked', 'purchased', 'time_spent', 'timestamp'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Check data types
        self.assertTrue(df['user_id'].dtype == 'object')
        self.assertTrue(df['group'].dtype == 'object')
        self.assertTrue(df['device'].dtype == 'object')
        self.assertTrue(df['viewed'].dtype in ['int64', 'int32'])
        self.assertTrue(df['clicked'].dtype in ['int64', 'int32'])
        self.assertTrue(df['purchased'].dtype in ['int64', 'int32'])
        self.assertTrue(df['time_spent'].dtype in ['float64', 'float32'])
        
        # Check logical constraints
        self.assertTrue((df['clicked'] <= df['viewed']).all())
        self.assertTrue((df['purchased'] <= df['clicked']).all())
        self.assertTrue((df['time_spent'] >= 0).all())
        
        # Check timestamp
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['timestamp']))
    
    def test_generate_summary_stats(self):
        """Test summary statistics generation"""
        df = self.generator.generate_dataset()
        stats = self.generator.generate_summary_stats(df)
        
        # Check structure
        self.assertIn('A', stats)
        self.assertIn('B', stats)
        self.assertIn('lifts', stats)
        
        # Check group stats
        for group in ['A', 'B']:
            group_stats = stats[group]
            self.assertIn('total_users', group_stats)
            self.assertIn('view_rate', group_stats)
            self.assertIn('ctr', group_stats)
            self.assertIn('conversion_rate', group_stats)
            self.assertIn('avg_time_spent', group_stats)
            self.assertIn('total_purchases', group_stats)
        
        # Check lifts
        lifts = stats['lifts']
        self.assertIn('conversion_lift', lifts)
        self.assertIn('ctr_lift', lifts)
        self.assertIn('time_spent_lift', lifts)
        
        # Check reasonable values
        self.assertGreater(stats['A']['conversion_rate'], 0)
        self.assertLess(stats['A']['conversion_rate'], 1)
        self.assertGreater(stats['B']['conversion_rate'], 0)
        self.assertLess(stats['B']['conversion_rate'], 1)
    
    def test_reproducibility(self):
        """Test that results are reproducible with same seed"""
        generator1 = ABTestDataGenerator(seed=42)
        df1 = generator1.generate_dataset()
        
        generator2 = ABTestDataGenerator(seed=42)
        df2 = generator2.generate_dataset()
        
        # Should be identical
        pd.testing.assert_frame_equal(df1, df2)
        
        # Different seed should produce different results
        generator3 = ABTestDataGenerator(seed=123)
        df3 = generator3.generate_dataset()
        
        # Should be different
        self.assertFalse(df1.equals(df3))

if __name__ == '__main__':
    unittest.main()
