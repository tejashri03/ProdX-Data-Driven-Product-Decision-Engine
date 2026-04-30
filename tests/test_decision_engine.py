"""
Unit tests for decision engine module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.decision_engine import ABTestDecisionEngine, DecisionCriteria, Decision, ExperimentResult

class TestDecisionEngine(unittest.TestCase):
    """Test cases for ABTestDecisionEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.criteria = DecisionCriteria()
        self.engine = ABTestDecisionEngine(self.criteria)
        
        # Create sample experiment results
        self.positive_result = ExperimentResult(
            metric="Conversion Rate",
            control_rate=0.032,
            treatment_rate=0.036,
            relative_difference=0.125,  # 12.5% lift
            p_value=0.023,
            confidence_interval=(0.002, 0.006),
            test_statistic=2.28,
            sample_size_control=25000,
            sample_size_treatment=25000,
            is_significant=True
        )
        
        self.negative_result = ExperimentResult(
            metric="Conversion Rate",
            control_rate=0.032,
            treatment_rate=0.030,
            relative_difference=-0.0625,  # -6.25% lift
            p_value=0.023,
            confidence_interval=(-0.004, -0.001),
            test_statistic=-2.28,
            sample_size_control=25000,
            sample_size_treatment=25000,
            is_significant=True
        )
        
        self.insignificant_result = ExperimentResult(
            metric="Conversion Rate",
            control_rate=0.032,
            treatment_rate=0.033,
            relative_difference=0.03125,  # 3.125% lift
            p_value=0.15,  # Not significant
            confidence_interval=(-0.001, 0.003),
            test_statistic=1.04,
            sample_size_control=25000,
            sample_size_treatment=25000,
            is_significant=False
        )
    
    def test_decision_criteria_defaults(self):
        """Test default decision criteria"""
        self.assertEqual(self.criteria.min_sample_size, 1000)
        self.assertEqual(self.criteria.significance_threshold, 0.05)
        self.assertEqual(self.criteria.power_threshold, 0.80)
        self.assertEqual(self.criteria.min_effect_size, 0.02)
        self.assertEqual(self.criteria.max_negative_lift, -0.05)
        self.assertEqual(self.criteria.confidence_level, 0.95)
    
    def test_evaluate_primary_metric_positive(self):
        """Test evaluation of positive significant result"""
        evaluation = self.engine.evaluate_primary_metric(self.positive_result)
        
        # Check structure
        self.assertIsInstance(evaluation, dict)
        required_keys = [
            'metric', 'meets_sample_size', 'is_significant', 'has_sufficient_power',
            'positive_lift', 'meets_min_effect', 'unacceptable_negative',
            'confidence_interval_excludes_zero'
        ]
        
        for key in required_keys:
            self.assertIn(key, evaluation)
        
        # Check values for positive result
        self.assertEqual(evaluation['metric'], "Conversion Rate")
        self.assertTrue(evaluation['meets_sample_size'])
        self.assertTrue(evaluation['is_significant'])
        self.assertTrue(evaluation['positive_lift'])
        self.assertTrue(evaluation['meets_min_effect'])
        self.assertFalse(evaluation['unacceptable_negative'])
        self.assertTrue(evaluation['confidence_interval_excludes_zero'])
    
    def test_evaluate_primary_metric_negative(self):
        """Test evaluation of negative significant result"""
        evaluation = self.engine.evaluate_primary_metric(self.negative_result)
        
        # Check values for negative result
        self.assertFalse(evaluation['positive_lift'])
        self.assertTrue(evaluation['unacceptable_negative'])
        self.assertTrue(evaluation['confidence_interval_excludes_zero'])
    
    def test_evaluate_primary_metric_insignificant(self):
        """Test evaluation of insignificant result"""
        evaluation = self.engine.evaluate_primary_metric(self.insignificant_result)
        
        # Check values for insignificant result
        self.assertFalse(evaluation['is_significant'])
        self.assertTrue(evaluation['positive_lift'])  # Still positive but not significant
        self.assertFalse(evaluation['meets_min_effect'])  # Below threshold
        self.assertFalse(evaluation['confidence_interval_excludes_zero'])
    
    def test_calculate_business_impact_conversion(self):
        """Test business impact calculation for conversion rate"""
        impact = self.engine.calculate_business_impact(self.positive_result, monthly_users=100000)
        
        # Check structure
        self.assertIsInstance(impact, dict)
        required_keys = [
            'current_monthly_revenue', 'projected_monthly_revenue',
            'monthly_revenue_impact', 'annual_revenue_impact', 'impact_percentage'
        ]
        
        for key in required_keys:
            self.assertIn(key, impact)
        
        # Check reasonable values
        self.assertGreater(impact['projected_monthly_revenue'], impact['current_monthly_revenue'])
        self.assertGreater(impact['monthly_revenue_impact'], 0)
        self.assertGreater(impact['annual_revenue_impact'], 0)
        self.assertGreater(impact['impact_percentage'], 0)
    
    def test_calculate_business_impact_ctr(self):
        """Test business impact calculation for CTR"""
        ctr_result = ExperimentResult(
            metric="Click-Through Rate",
            control_rate=0.12,
            treatment_rate=0.14,
            relative_difference=0.167,
            p_value=0.045,
            confidence_interval=(0.001, 0.039),
            test_statistic=1.98,
            sample_size_control=20000,
            sample_size_treatment=20000,
            is_significant=True
        )
        
        impact = self.engine.calculate_business_impact(ctr_result)
        
        # Check structure
        self.assertIsInstance(impact, dict)
        self.assertIn('ctr_lift_percentage', impact)
        self.assertIn('engagement_impact', impact)
        
        # Check values
        self.assertEqual(impact['ctr_lift_percentage'], 0.167)
        self.assertEqual(impact['engagement_impact'], 'Positive')
    
    def test_check_guardrail_metrics_no_violations(self):
        """Test guardrail checking with no violations"""
        guardrail_results = [
            ExperimentResult(
                metric="Click-Through Rate",
                control_rate=0.12,
                treatment_rate=0.13,
                relative_difference=0.083,  # Small positive lift
                p_value=0.1,
                confidence_interval=(-0.01, 0.03),
                test_statistic=1.65,
                sample_size_control=20000,
                sample_size_treatment=20000,
                is_significant=False
            )
        ]
        
        check = self.engine.check_guardrail_metrics(guardrail_results)
        
        # Check structure
        self.assertIsInstance(check, dict)
        self.assertIn('has_violations', check)
        self.assertIn('violations', check)
        
        # Check values
        self.assertFalse(check['has_violations'])
        self.assertEqual(len(check['violations']), 0)
    
    def test_check_guardrail_metrics_with_violations(self):
        """Test guardrail checking with violations"""
        guardrail_results = [
            ExperimentResult(
                metric="Click-Through Rate",
                control_rate=0.12,
                treatment_rate=0.10,
                relative_difference=-0.167,  # Negative lift beyond threshold
                p_value=0.045,
                confidence_interval=(-0.039, -0.001),
                test_statistic=-1.98,
                sample_size_control=20000,
                sample_size_treatment=20000,
                is_significant=True
            )
        ]
        
        check = self.engine.check_guardrail_metrics(guardrail_results)
        
        # Check values
        self.assertTrue(check['has_violations'])
        self.assertEqual(len(check['violations']), 1)
        
        violation = check['violations'][0]
        self.assertEqual(violation['metric'], "Click-Through Rate")
        self.assertEqual(violation['lift'], -0.167)
        self.assertEqual(violation['threshold'], -0.05)
    
    def test_segment_consistency_check_consistent(self):
        """Test segment consistency check with consistent results"""
        segment_results = {
            'mobile': {
                'conversion': ExperimentResult(
                    metric="Conversion Rate",
                    control_rate=0.030,
                    treatment_rate=0.034,
                    relative_difference=0.133,
                    p_value=0.032,
                    confidence_interval=(0.001, 0.007),
                    test_statistic=2.15,
                    sample_size_control=15000,
                    sample_size_treatment=15000,
                    is_significant=True
                )
            },
            'desktop': {
                'conversion': ExperimentResult(
                    metric="Conversion Rate",
                    control_rate=0.035,
                    treatment_rate=0.039,
                    relative_difference=0.114,
                    p_value=0.041,
                    confidence_interval=(0.001, 0.007),
                    test_statistic=2.05,
                    sample_size_control=8000,
                    sample_size_treatment=8000,
                    is_significant=True
                )
            }
        }
        
        check = self.engine.segment_consistency_check(segment_results)
        
        # Check structure
        self.assertIsInstance(check, dict)
        required_keys = [
            'average_segment_lift', 'lift_coefficient_of_variation',
            'inconsistent_segments', 'is_consistent'
        ]
        
        for key in required_keys:
            self.assertIn(key, check)
        
        # Check values
        self.assertGreater(check['average_segment_lift'], 0)
        self.assertGreaterEqual(check['lift_coefficient_of_variation'], 0)
        self.assertEqual(len(check['inconsistent_segments']), 0)
        self.assertTrue(check['is_consistent'])
    
    def test_segment_consistency_check_inconsistent(self):
        """Test segment consistency check with inconsistent results"""
        segment_results = {
            'mobile': {
                'conversion': ExperimentResult(
                    metric="Conversion Rate",
                    control_rate=0.030,
                    treatment_rate=0.034,
                    relative_difference=0.133,
                    p_value=0.032,
                    confidence_interval=(0.001, 0.007),
                    test_statistic=2.15,
                    sample_size_control=15000,
                    sample_size_treatment=15000,
                    is_significant=True
                )
            },
            'desktop': {
                'conversion': ExperimentResult(
                    metric="Conversion Rate",
                    control_rate=0.035,
                    treatment_rate=0.032,
                    relative_difference=-0.086,  # Negative lift
                    p_value=0.041,
                    confidence_interval=(-0.007, -0.001),
                    test_statistic=-2.05,
                    sample_size_control=8000,
                    sample_size_treatment=8000,
                    is_significant=True
                )
            }
        }
        
        check = self.engine.segment_consistency_check(segment_results)
        
        # Check values
        self.assertEqual(len(check['inconsistent_segments']), 1)
        self.assertFalse(check['is_consistent'])
        
        inconsistent = check['inconsistent_segments'][0]
        self.assertEqual(inconsistent['segment'], 'desktop')
        self.assertEqual(inconsistent['lift'], -0.086)
    
    def test_make_decision_launch(self):
        """Test decision making for launch scenario"""
        guardrail_results = [
            ExperimentResult(
                metric="Click-Through Rate",
                control_rate=0.12,
                treatment_rate=0.14,
                relative_difference=0.167,
                p_value=0.045,
                confidence_interval=(0.001, 0.039),
                test_statistic=1.98,
                sample_size_control=20000,
                sample_size_treatment=20000,
                is_significant=True
            )
        ]
        
        segment_results = {
            'mobile': {
                'conversion': ExperimentResult(
                    metric="Conversion Rate",
                    control_rate=0.030,
                    treatment_rate=0.034,
                    relative_difference=0.133,
                    p_value=0.032,
                    confidence_interval=(0.001, 0.007),
                    test_statistic=2.15,
                    sample_size_control=15000,
                    sample_size_treatment=15000,
                    is_significant=True
                )
            }
        }
        
        recommendation = self.engine.make_decision(
            primary_result=self.positive_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        # Check structure
        self.assertIsInstance(recommendation, dict)
        required_keys = [
            'decision', 'confidence', 'reasoning', 'primary_metric_evaluation',
            'business_impact', 'guardrail_check', 'segment_consistency',
            'recommendations', 'next_steps', 'timestamp'
        ]
        
        for key in required_keys:
            self.assertIn(key, recommendation)
        
        # Check decision
        self.assertEqual(recommendation['decision'], Decision.LAUNCH.value)
        self.assertGreater(recommendation['confidence'], 0.8)
    
    def test_make_decision_stop(self):
        """Test decision making for stop scenario"""
        guardrail_results = []
        segment_results = {}
        
        recommendation = self.engine.make_decision(
            primary_result=self.negative_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        # Check decision
        self.assertEqual(recommendation['decision'], Decision.STOP.value)
    
    def test_make_decision_continue(self):
        """Test decision making for continue scenario"""
        guardrail_results = []
        segment_results = {}
        
        recommendation = self.engine.make_decision(
            primary_result=self.insignificant_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        # Check decision
        self.assertEqual(recommendation['decision'], Decision.CONTINUE.value)
    
    def test_generate_decision_report(self):
        """Test decision report generation"""
        guardrail_results = []
        segment_results = {}
        
        recommendation = self.engine.make_decision(
            primary_result=self.positive_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        report = self.engine.generate_decision_report(recommendation)
        
        # Check return type
        self.assertIsInstance(report, str)
        
        # Check content
        self.assertIn("A/B TEST DECISION REPORT", report)
        self.assertIn("Decision:", report)
        self.assertIn("Confidence:", report)
        self.assertIn("REASONING:", report)
        self.assertIn("RECOMMENDATIONS:", report)
        self.assertIn("NEXT STEPS:", report)
    
    def test_decision_history(self):
        """Test decision history tracking"""
        guardrail_results = []
        segment_results = {}
        
        # Make first decision
        recommendation1 = self.engine.make_decision(
            primary_result=self.positive_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        # Make second decision
        recommendation2 = self.engine.make_decision(
            primary_result=self.negative_result,
            guardrail_results=guardrail_results,
            segment_results=segment_results
        )
        
        # Check history
        self.assertEqual(len(self.engine.decision_history), 2)
        self.assertEqual(self.engine.decision_history[0]['decision'], Decision.LAUNCH.value)
        self.assertEqual(self.engine.decision_history[1]['decision'], Decision.STOP.value)

if __name__ == '__main__':
    unittest.main()
