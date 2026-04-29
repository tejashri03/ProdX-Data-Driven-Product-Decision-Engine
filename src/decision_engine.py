import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

class Decision(Enum):
    """Decision outcomes for A/B tests"""
    LAUNCH = "Launch Treatment"
    CONTINUE = "Continue Testing"
    STOP = "Stop Experiment (Negative Results)"
    INCONCLUSIVE = "Inconclusive - More Data Needed"

@dataclass
class DecisionCriteria:
    """Criteria for making A/B test decisions"""
    min_sample_size: int = 1000
    significance_threshold: float = 0.05
    power_threshold: float = 0.80
    min_effect_size: float = 0.02  # 2% minimum relative lift
    max_negative_lift: float = -0.05  # -5% maximum acceptable negative lift
    confidence_level: float = 0.95
    business_impact_threshold: float = 0.03  # 3% business impact threshold

@dataclass
class ExperimentResult:
    """Results from an A/B test"""
    metric: str
    control_rate: float
    treatment_rate: float
    relative_lift: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size_control: int
    sample_size_treatment: int
    power: float
    is_significant: bool

class ABTestDecisionEngine:
    """
    Decision engine for A/B testing experiments
    Makes automated decisions based on statistical and business criteria
    """
    
    def __init__(self, criteria: Optional[DecisionCriteria] = None):
        self.criteria = criteria or DecisionCriteria()
        self.decision_history = []
    
    def evaluate_primary_metric(self, result: ExperimentResult) -> Dict:
        """Evaluate a single metric against decision criteria"""
        # Handle missing power attribute for some metrics
        has_sufficient_power = True
        if hasattr(result, 'power'):
            has_sufficient_power = result.power >= self.criteria.power_threshold
        
        evaluation = {
            'metric': result.metric,
            'meets_sample_size': (result.sample_size_control + result.sample_size_treatment) >= self.criteria.min_sample_size,
            'is_significant': result.is_significant,
            'has_sufficient_power': has_sufficient_power,
            'positive_lift': result.relative_difference > 0,
            'meets_min_effect': abs(result.relative_difference) >= self.criteria.min_effect_size,
            'unacceptable_negative': result.relative_difference < self.criteria.max_negative_lift,
            'confidence_interval_excludes_zero': result.confidence_interval[0] > 0 or result.confidence_interval[1] < 0
        }
        
        return evaluation
    
    def calculate_business_impact(self, result: ExperimentResult, monthly_users: int = 100000) -> Dict:
        """Calculate business impact of the experiment"""
        if result.metric == "Conversion Rate":
            # Assuming average order value of $75
            avg_order_value = 75
            current_monthly_revenue = monthly_users * result.control_rate * avg_order_value
            projected_monthly_revenue = monthly_users * result.treatment_rate * avg_order_value
            revenue_impact = projected_monthly_revenue - current_monthly_revenue
            
            return {
                'current_monthly_revenue': current_monthly_revenue,
                'projected_monthly_revenue': projected_monthly_revenue,
                'monthly_revenue_impact': revenue_impact,
                'annual_revenue_impact': revenue_impact * 12,
                'impact_percentage': (revenue_impact / current_monthly_revenue * 100) if current_monthly_revenue > 0 else 0
            }
        
        elif result.metric == "Click-Through Rate":
            # Assuming CTR impacts ad revenue or engagement
            return {
                'ctr_lift_percentage': result.relative_difference,
                'engagement_impact': 'Positive' if result.relative_difference > 0 else 'Negative'
            }
        
        return {'impact': 'Cannot calculate business impact for this metric'}
    
    def check_guardrail_metrics(self, guardrail_results: List[ExperimentResult]) -> Dict:
        """Check guardrail metrics for negative impacts"""
        guardrail_violations = []
        
        for result in guardrail_results:
            if result.relative_difference < self.criteria.max_negative_lift:
                guardrail_violations.append({
                    'metric': result.metric,
                    'lift': result.relative_difference,
                    'threshold': self.criteria.max_negative_lift
                })
        
        return {
            'has_violations': len(guardrail_violations) > 0,
            'violations': guardrail_violations
        }
    
    def segment_consistency_check(self, segment_results: Dict) -> Dict:
        """Check for consistency across user segments"""
        segment_lifts = []
        inconsistent_segments = []
        
        for segment_name, results in segment_results.items():
            if 'conversion' in results:
                lift = results['conversion'].relative_difference
                segment_lifts.append(lift)
                
                # Check for segments with opposite direction
                if lift < 0:
                    inconsistent_segments.append({
                        'segment': segment_name,
                        'lift': lift
                    })
        
        if segment_lifts:
            avg_lift = np.mean(segment_lifts)
            lift_std = np.std(segment_lifts)
            cv = lift_std / abs(avg_lift) if avg_lift != 0 else float('inf')
        else:
            avg_lift = 0
            cv = 0
        
        return {
            'average_segment_lift': avg_lift,
            'lift_coefficient_of_variation': cv,
            'inconsistent_segments': inconsistent_segments,
            'is_consistent': cv < 0.5 and len(inconsistent_segments) == 0
        }
    
    def make_decision(self, 
                    primary_result: ExperimentResult,
                    guardrail_results: List[ExperimentResult],
                    segment_results: Dict,
                    business_context: Optional[Dict] = None) -> Dict:
        """
        Make final decision based on all criteria
        """
        # Evaluate primary metric
        primary_eval = self.evaluate_primary_metric(primary_result)
        
        # Calculate business impact
        business_impact = self.calculate_business_impact(primary_result)
        
        # Check guardrails
        guardrail_check = self.check_guardrail_metrics(guardrail_results)
        
        # Check segment consistency
        segment_check = self.segment_consistency_check(segment_results)
        
        # Decision logic
        decision = self._apply_decision_rules(
            primary_eval, guardrail_check, segment_check, business_impact
        )
        
        # Compile recommendation
        recommendation = {
            'decision': decision.value,
            'confidence': self._calculate_confidence(primary_eval, guardrail_check, segment_check),
            'reasoning': self._generate_reasoning(primary_eval, guardrail_check, segment_check, business_impact),
            'primary_metric_evaluation': primary_eval,
            'business_impact': business_impact,
            'guardrail_check': guardrail_check,
            'segment_consistency': segment_check,
            'recommendations': self._generate_recommendations(decision, primary_result),
            'next_steps': self._generate_next_steps(decision),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store decision in history
        self.decision_history.append(recommendation)
        
        return recommendation
    
    def _apply_decision_rules(self, 
                            primary_eval: Dict,
                            guardrail_check: Dict,
                            segment_check: Dict,
                            business_impact: Dict) -> Decision:
        """Apply decision rules to determine outcome"""
        
        # Rule 1: Insufficient sample size
        if not primary_eval['meets_sample_size']:
            return Decision.CONTINUE
        
        # Rule 2: Significant positive lift with guardrails intact
        if (primary_eval['is_significant'] and 
            primary_eval['positive_lift'] and
            primary_eval['meets_min_effect'] and
            not guardrail_check['has_violations'] and
            segment_check['is_consistent']):
            return Decision.LAUNCH
        
        # Rule 3: Significant negative impact
        if (primary_eval['is_significant'] and 
            primary_eval['unacceptable_negative']):
            return Decision.STOP
        
        # Rule 4: Inconclusive - continue testing
        if (not primary_eval['is_significant'] and
            primary_eval['meets_sample_size'] and
            not primary_eval['has_sufficient_power']):
            return Decision.CONTINUE
        
        # Rule 5: Significant but inconsistent segments
        if (primary_eval['is_significant'] and
            not segment_check['is_consistent']):
            return Decision.INCONCLUSIVE
        
        # Rule 6: Significant but guardrail violations
        if (primary_eval['is_significant'] and
            guardrail_check['has_violations']):
            return Decision.INCONCLUSIVE
        
        # Default: Continue testing
        return Decision.CONTINUE
    
    def _calculate_confidence(self, primary_eval: Dict, guardrail_check: Dict, segment_check: Dict) -> float:
        """Calculate confidence score for the decision"""
        confidence_factors = []
        
        # Sample size confidence
        if primary_eval['meets_sample_size']:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        
        # Statistical significance
        if primary_eval['is_significant']:
            confidence_factors.append(0.95)
        else:
            confidence_factors.append(0.4)
        
        # Power confidence
        if primary_eval['has_sufficient_power']:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)
        
        # Guardrail confidence
        if not guardrail_check['has_violations']:
            confidence_factors.append(0.95)
        else:
            confidence_factors.append(0.3)
        
        # Segment consistency confidence
        if segment_check['is_consistent']:
            confidence_factors.append(0.85)
        else:
            confidence_factors.append(0.6)
        
        return np.mean(confidence_factors)
    
    def _generate_reasoning(self, primary_eval: Dict, guardrail_check: Dict, segment_check: Dict, business_impact: Dict) -> str:
        """Generate human-readable reasoning for the decision"""
        reasoning_parts = []
        
        # Primary metric reasoning
        if primary_eval['is_significant']:
            if primary_eval['positive_lift']:
                reasoning_parts.append("Primary metric shows statistically significant positive lift")
            else:
                reasoning_parts.append("Primary metric shows statistically significant negative impact")
        else:
            reasoning_parts.append("Primary metric does not show statistically significant results")
        
        # Sample size reasoning
        if primary_eval['meets_sample_size']:
            reasoning_parts.append("Sample size requirements are met")
        else:
            reasoning_parts.append("Insufficient sample size for reliable conclusions")
        
        # Guardrail reasoning
        if guardrail_check['has_violations']:
            reasoning_parts.append(f"Guardrail violations detected: {len(guardrail_check['violations'])}")
        else:
            reasoning_parts.append("All guardrail metrics are within acceptable ranges")
        
        # Segment reasoning
        if segment_check['is_consistent']:
            reasoning_parts.append("Results are consistent across user segments")
        else:
            reasoning_parts.append("Inconsistent results across segments require further investigation")
        
        # Business impact reasoning
        if 'annual_revenue_impact' in business_impact:
            impact = business_impact['annual_revenue_impact']
            if impact > 0:
                reasoning_parts.append(f"Projected positive annual revenue impact of ${impact:,.0f}")
            else:
                reasoning_parts.append(f"Projected negative annual revenue impact of ${abs(impact):,.0f}")
        
        return "; ".join(reasoning_parts)
    
    def _generate_recommendations(self, decision: Decision, result: ExperimentResult) -> List[str]:
        """Generate actionable recommendations based on decision"""
        recommendations = []
        
        if decision == Decision.LAUNCH:
            recommendations.append("Launch the treatment to 100% of users")
            recommendations.append("Monitor key metrics for 2 weeks post-launch")
            recommendations.append("Prepare rollback plan if performance degrades")
            recommendations.append("Document learnings for future experiments")
        
        elif decision == Decision.CONTINUE:
            recommendations.append("Continue the experiment to collect more data")
            if result.sample_size_control + result.sample_size_treatment < self.criteria.min_sample_size:
                recommendations.append(f"Need {self.criteria.min_sample_size - (result.sample_size_control + result.sample_size_treatment):,} more users")
            if result.power < self.criteria.power_threshold:
                recommendations.append("Current power is below threshold - consider extending test duration")
        
        elif decision == Decision.STOP:
            recommendations.append("Immediately stop the experiment")
            recommendations.append("Analyze root cause of negative impact")
            recommendations.append("Consider alternative hypothesis for next experiment")
        
        elif decision == Decision.INCONCLUSIVE:
            recommendations.append("Conduct deeper analysis of segment inconsistencies")
            recommendations.append("Consider running follow-up experiment with modified design")
            recommendations.append("Investigate potential confounding variables")
        
        return recommendations
    
    def _generate_next_steps(self, decision: Decision) -> List[str]:
        """Generate next steps for the team"""
        next_steps = []
        
        if decision == Decision.LAUNCH:
            next_steps.append("Schedule deployment meeting with engineering team")
            next_steps.append("Prepare communication plan for stakeholders")
            next_steps.append("Set up post-launch monitoring dashboard")
            next_steps.append("Document experiment results in knowledge base")
        
        elif decision == Decision.CONTINUE:
            next_steps.append("Review experiment duration and traffic allocation")
            next_steps.append("Check data collection systems for issues")
            next_steps.append("Schedule decision review for next week")
        
        elif decision == Decision.STOP:
            next_steps.append("Execute experiment rollback procedures")
            next_steps.append("Schedule retrospective meeting with team")
            next_steps.append("Update experiment documentation with lessons learned")
        
        elif decision == Decision.INCONCLUSIVE:
            next_steps.append("Schedule deep-dive analysis session")
            next_steps.append("Review user behavior data for insights")
            next_steps.append("Plan follow-up experiment design")
        
        return next_steps
    
    def generate_decision_report(self, recommendation: Dict) -> str:
        """Generate comprehensive decision report"""
        report = []
        report.append("=" * 80)
        report.append("A/B TEST DECISION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {recommendation['timestamp']}")
        report.append(f"Decision: {recommendation['decision']}")
        report.append(f"Confidence: {recommendation['confidence']:.1%}")
        report.append("")
        
        report.append("REASONING:")
        report.append("-" * 40)
        report.append(recommendation['reasoning'])
        report.append("")
        
        report.append("BUSINESS IMPACT:")
        report.append("-" * 40)
        if 'annual_revenue_impact' in recommendation['business_impact']:
            impact = recommendation['business_impact']['annual_revenue_impact']
            report.append(f"Annual Revenue Impact: ${impact:,.0f}")
            report.append(f"Impact Percentage: {recommendation['business_impact'].get('impact_percentage', 0):.2f}%")
        report.append("")
        
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        for rec in recommendation['recommendations']:
            report.append(f"• {rec}")
        report.append("")
        
        report.append("NEXT STEPS:")
        report.append("-" * 40)
        for step in recommendation['next_steps']:
            report.append(f"• {step}")
        
        return "\n".join(report)
    
    def save_decision_history(self, filepath: str):
        """Save decision history to file"""
        with open(filepath, 'w') as f:
            json.dump(self.decision_history, f, indent=2, default=str)
    
    def load_decision_history(self, filepath: str):
        """Load decision history from file"""
        with open(filepath, 'r') as f:
            self.decision_history = json.load(f)

def main():
    """Example usage of the decision engine"""
    # Create sample experiment result
    primary_result = ExperimentResult(
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
    
    # Create sample guardrail results
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
    
    # Create sample segment results
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
    
    # Create decision engine and make decision
    engine = ABTestDecisionEngine()
    recommendation = engine.make_decision(
        primary_result=primary_result,
        guardrail_results=guardrail_results,
        segment_results=segment_results
    )
    
    # Generate and print report
    report = engine.generate_decision_report(recommendation)
    print(report)
    
    # Save decision history
    engine.save_decision_history('decision_history.json')

if __name__ == "__main__":
    main()
