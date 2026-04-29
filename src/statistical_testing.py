import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional, List
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TestResult:
    """Data class for storing test results"""
    metric: str
    control_rate: float
    treatment_rate: float
    absolute_difference: float
    relative_difference: float
    p_value: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    test_statistic: float
    sample_size_control: int
    sample_size_treatment: int

class ABTestStatisticalAnalyzer:
    """
    Statistical analysis for A/B testing experiments
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.alpha = significance_level
        self.results = {}
    
    def calculate_conversion_rate(self, df: pd.DataFrame, group: str) -> float:
        """Calculate conversion rate for a specific group"""
        group_data = df[df['group'] == group]
        if len(group_data) == 0:
            return 0.0
        return group_data['purchased'].mean()
    
    def calculate_ctr(self, df: pd.DataFrame, group: str) -> float:
        """Calculate click-through rate for a specific group"""
        group_data = df[df['group'] == group]
        if len(group_data) == 0 or group_data['viewed'].sum() == 0:
            return 0.0
        return group_data['clicked'].sum() / group_data['viewed'].sum()
    
    def calculate_view_rate(self, df: pd.DataFrame, group: str) -> float:
        """Calculate view rate for a specific group"""
        group_data = df[df['group'] == group]
        if len(group_data) == 0:
            return 0.0
        return group_data['viewed'].mean()
    
    def two_proportion_z_test(self, 
                            control_successes: int, 
                            control_n: int,
                            treatment_successes: int, 
                            treatment_n: int) -> Tuple[float, float, Tuple[float, float]]:
        """
        Perform two-proportion Z-test
        Returns: (z_statistic, p_value, confidence_interval)
        """
        if control_n == 0 or treatment_n == 0:
            return 0.0, 1.0, (0.0, 0.0)
        
        # Calculate proportions
        p1 = control_successes / control_n
        p2 = treatment_successes / treatment_n
        
        # Calculate pooled proportion
        p_pooled = (control_successes + treatment_successes) / (control_n + treatment_n)
        
        # Calculate standard error
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_n + 1/treatment_n))
        
        if se == 0:
            return 0.0, 1.0, (0.0, 0.0)
        
        # Calculate Z-statistic
        z_stat = (p2 - p1) / se
        
        # Calculate two-tailed p-value
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Calculate confidence interval for difference
        diff = p2 - p1
        margin_error = stats.norm.ppf(1 - self.alpha/2) * se
        ci_lower = diff - margin_error
        ci_upper = diff + margin_error
        
        return z_stat, p_value, (ci_lower, ci_upper)
    
    def test_conversion_rate(self, df: pd.DataFrame) -> TestResult:
        """Test conversion rate difference between groups"""
        control_data = df[df['group'] == 'A']
        treatment_data = df[df['group'] == 'B']
        
        control_successes = control_data['purchased'].sum()
        control_n = len(control_data)
        treatment_successes = treatment_data['purchased'].sum()
        treatment_n = len(treatment_data)
        
        control_rate = control_successes / control_n if control_n > 0 else 0
        treatment_rate = treatment_successes / treatment_n if treatment_n > 0 else 0
        
        z_stat, p_value, ci = self.two_proportion_z_test(
            control_successes, control_n, treatment_successes, treatment_n
        )
        
        absolute_diff = treatment_rate - control_rate
        relative_diff = (absolute_diff / control_rate * 100) if control_rate > 0 else 0
        
        return TestResult(
            metric="Conversion Rate",
            control_rate=control_rate,
            treatment_rate=treatment_rate,
            absolute_difference=absolute_diff,
            relative_difference=relative_diff,
            p_value=p_value,
            confidence_interval=ci,
            is_significant=p_value < self.alpha,
            test_statistic=z_stat,
            sample_size_control=control_n,
            sample_size_treatment=treatment_n
        )
    
    def test_ctr(self, df: pd.DataFrame) -> TestResult:
        """Test click-through rate difference between groups"""
        control_data = df[df['group'] == 'A']
        treatment_data = df[df['group'] == 'B']
        
        control_views = control_data['viewed'].sum()
        control_clicks = control_data['clicked'].sum()
        treatment_views = treatment_data['viewed'].sum()
        treatment_clicks = treatment_data['clicked'].sum()
        
        control_rate = control_clicks / control_views if control_views > 0 else 0
        treatment_rate = treatment_clicks / treatment_views if treatment_views > 0 else 0
        
        z_stat, p_value, ci = self.two_proportion_z_test(
            control_clicks, control_views, treatment_clicks, treatment_views
        )
        
        absolute_diff = treatment_rate - control_rate
        relative_diff = (absolute_diff / control_rate * 100) if control_rate > 0 else 0
        
        return TestResult(
            metric="Click-Through Rate",
            control_rate=control_rate,
            treatment_rate=treatment_rate,
            absolute_difference=absolute_diff,
            relative_difference=relative_diff,
            p_value=p_value,
            confidence_interval=ci,
            is_significant=p_value < self.alpha,
            test_statistic=z_stat,
            sample_size_control=control_views,
            sample_size_treatment=treatment_views
        )
    
    def test_view_rate(self, df: pd.DataFrame) -> TestResult:
        """Test view rate difference between groups"""
        control_data = df[df['group'] == 'A']
        treatment_data = df[df['group'] == 'B']
        
        control_successes = control_data['viewed'].sum()
        control_n = len(control_data)
        treatment_successes = treatment_data['viewed'].sum()
        treatment_n = len(treatment_data)
        
        control_rate = control_successes / control_n if control_n > 0 else 0
        treatment_rate = treatment_successes / treatment_n if treatment_n > 0 else 0
        
        z_stat, p_value, ci = self.two_proportion_z_test(
            control_successes, control_n, treatment_successes, treatment_n
        )
        
        absolute_diff = treatment_rate - control_rate
        relative_diff = (absolute_diff / control_rate * 100) if control_rate > 0 else 0
        
        return TestResult(
            metric="View Rate",
            control_rate=control_rate,
            treatment_rate=treatment_rate,
            absolute_difference=absolute_diff,
            relative_difference=relative_diff,
            p_value=p_value,
            confidence_interval=ci,
            is_significant=p_value < self.alpha,
            test_statistic=z_stat,
            sample_size_control=control_n,
            sample_size_treatment=treatment_n
        )
    
    def test_time_spent(self, df: pd.DataFrame) -> Dict:
        """Test time spent difference using t-test"""
        control_times = df[(df['group'] == 'A') & (df['viewed'] == 1)]['time_spent']
        treatment_times = df[(df['group'] == 'B') & (df['viewed'] == 1)]['time_spent']
        
        if len(control_times) == 0 or len(treatment_times) == 0:
            return {
                'metric': 'Time Spent',
                'control_mean': 0,
                'treatment_mean': 0,
                'absolute_difference': 0,
                'relative_difference': 0,
                'p_value': 1.0,
                'is_significant': False,
                'sample_size_control': 0,
                'sample_size_treatment': 0
            }
        
        # Perform two-sample t-test
        t_stat, p_value = stats.ttest_ind(treatment_times, control_times)
        
        control_mean = control_times.mean()
        treatment_mean = treatment_times.mean()
        absolute_diff = treatment_mean - control_mean
        relative_diff = (absolute_diff / control_mean * 100) if control_mean > 0 else 0
        
        return {
            'metric': 'Time Spent',
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'absolute_difference': absolute_diff,
            'relative_difference': relative_diff,
            'p_value': p_value,
            'is_significant': p_value < self.alpha,
            'sample_size_control': len(control_times),
            'sample_size_treatment': len(treatment_times)
        }
    
    def segment_analysis(self, df: pd.DataFrame, segment_column: str) -> Dict:
        """Perform statistical analysis by segments"""
        segments = df[segment_column].unique()
        segment_results = {}
        
        for segment in segments:
            segment_data = df[df[segment_column] == segment]
            
            if len(segment_data[segment_data['group'] == 'A']) == 0 or \
               len(segment_data[segment_data['group'] == 'B']) == 0:
                continue
            
            # Test conversion rate for this segment
            conversion_result = self.test_conversion_rate(segment_data)
            ctr_result = self.test_ctr(segment_data)
            
            segment_results[segment] = {
                'conversion': conversion_result,
                'ctr': ctr_result,
                'sample_size': len(segment_data)
            }
        
        return segment_results
    
    def calculate_sample_size(self, 
                            baseline_rate: float, 
                            minimum_detectable_effect: float,
                            power: float = 0.8) -> int:
        """
        Calculate required sample size for A/B test
        """
        # Convert relative effect to absolute
        absolute_effect = baseline_rate * minimum_detectable_effect
        
        # Z-scores
        z_alpha = stats.norm.ppf(1 - self.alpha/2)
        z_beta = stats.norm.ppf(power)
        
        # Pooled proportion under alternative hypothesis
        p1 = baseline_rate
        p2 = baseline_rate + absolute_effect
        p_pooled = (p1 + p2) / 2
        
        # Sample size formula
        n_per_group = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta)**2) / absolute_effect**2
        
        return int(np.ceil(n_per_group))
    
    def power_analysis(self, 
                      df: pd.DataFrame, 
                      metric: str = 'conversion') -> Dict:
        """Calculate statistical power for the test"""
        if metric == 'conversion':
            control_rate = self.calculate_conversion_rate(df, 'A')
            treatment_rate = self.calculate_conversion_rate(df, 'B')
            control_n = len(df[df['group'] == 'A'])
            treatment_n = len(df[df['group'] == 'B'])
        elif metric == 'ctr':
            control_rate = self.calculate_ctr(df, 'A')
            treatment_rate = self.calculate_ctr(df, 'B')
            control_n = df[df['group'] == 'A']['viewed'].sum()
            treatment_n = df[df['group'] == 'B']['viewed'].sum()
        else:
            return {'error': 'Unsupported metric'}
        
        # Calculate effect size
        effect_size = treatment_rate - control_rate
        
        # Calculate power
        if control_n > 0 and treatment_n > 0:
            pooled_rate = (control_rate * control_n + treatment_rate * treatment_n) / (control_n + treatment_n)
            se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_n + 1/treatment_n))
            
            if se > 0:
                z_stat = effect_size / se
                power = 1 - stats.norm.cdf(stats.norm.ppf(1 - self.alpha/2) - z_stat)
            else:
                power = 0
        else:
            power = 0
        
        return {
            'metric': metric,
            'effect_size': effect_size,
            'power': power,
            'sample_size_control': control_n,
            'sample_size_treatment': treatment_n
        }
    
    def run_full_analysis(self, df: pd.DataFrame) -> Dict:
        """Run complete statistical analysis"""
        results = {}
        
        # Main metrics tests
        results['conversion'] = self.test_conversion_rate(df)
        results['ctr'] = self.test_ctr(df)
        results['view_rate'] = self.test_view_rate(df)
        results['time_spent'] = self.test_time_spent(df)
        
        # Segment analyses
        results['device_segments'] = self.segment_analysis(df, 'device')
        results['new_user_segments'] = self.segment_analysis(df, 'new_user')
        results['region_segments'] = self.segment_analysis(df, 'region')
        
        # Power analysis
        results['power_conversion'] = self.power_analysis(df, 'conversion')
        results['power_ctr'] = self.power_analysis(df, 'ctr')
        
        # Sample size calculation for future tests
        baseline_conversion = self.calculate_conversion_rate(df, 'A')
        results['required_sample_size'] = self.calculate_sample_size(
            baseline_conversion, 0.05  # 5% MDE
        )
        
        self.results = results
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive statistical report"""
        report = []
        report.append("=" * 60)
        report.append("A/B TEST STATISTICAL ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Main results
        report.append("\nPRIMARY METRICS:")
        report.append("-" * 30)
        
        for metric_name, result in results.items():
            if metric_name in ['conversion', 'ctr', 'view_rate']:
                if hasattr(result, 'metric'):
                    report.append(f"\n{result.metric}:")
                    report.append(f"  Control Rate: {result.control_rate:.3%}")
                    report.append(f"  Treatment Rate: {result.treatment_rate:.3%}")
                    report.append(f"  Absolute Difference: {result.absolute_difference:.4f}")
                    report.append(f"  Relative Lift: {result.relative_difference:.2f}%")
                    report.append(f"  P-value: {result.p_value:.4f}")
                    report.append(f"  95% CI: [{result.confidence_interval[0]:.4f}, {result.confidence_interval[1]:.4f}]")
                    report.append(f"  Significant: {'Yes' if result.is_significant else 'No'}")
        
        # Time spent
        if 'time_spent' in results:
            ts_result = results['time_spent']
            report.append(f"\nTime Spent:")
            report.append(f"  Control Mean: {ts_result['control_mean']:.2f} seconds")
            report.append(f"  Treatment Mean: {ts_result['treatment_mean']:.2f} seconds")
            report.append(f"  Absolute Difference: {ts_result['absolute_difference']:.2f} seconds")
            report.append(f"  Relative Lift: {ts_result['relative_difference']:.2f}%")
            report.append(f"  P-value: {ts_result['p_value']:.4f}")
            report.append(f"  Significant: {'Yes' if ts_result['is_significant'] else 'No'}")
        
        # Power analysis
        report.append("\nPOWER ANALYSIS:")
        report.append("-" * 30)
        if 'power_conversion' in results:
            power_conv = results['power_conversion']
            report.append(f"Conversion Power: {power_conv['power']:.3f}")
        if 'power_ctr' in results:
            power_ctr = results['power_ctr']
            report.append(f"CTR Power: {power_ctr['power']:.3f}")
        
        # Sample size
        if 'required_sample_size' in results:
            report.append(f"\nRequired Sample Size (per group): {results['required_sample_size']:,}")
        
        # Segment insights
        report.append("\nSEGMENT INSIGHTS:")
        report.append("-" * 30)
        
        if 'device_segments' in results:
            report.append("\nDevice Segments:")
            for device, segment_result in results['device_segments'].items():
                conv_result = segment_result['conversion']
                report.append(f"  {device}: {conv_result.relative_difference:.2f}% lift (p={conv_result.p_value:.3f})")
        
        return "\n".join(report)
    
    def visualize_results(self, results: Dict, save_path: Optional[str] = None):
        """Create visualization of test results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('A/B Test Results', fontsize=16, fontweight='bold')
        
        # Conversion Rate
        if 'conversion' in results:
            conv = results['conversion']
            ax1 = axes[0, 0]
            bars = ax1.bar(['Control', 'Treatment'], [conv.control_rate, conv.treatment_rate], 
                          color=['lightcoral', 'lightblue'])
            ax1.set_title('Conversion Rate')
            ax1.set_ylabel('Rate')
            ax1.set_ylim(0, max(conv.control_rate, conv.treatment_rate) * 1.2)
            
            # Add value labels on bars
            for bar, value in zip(bars, [conv.control_rate, conv.treatment_rate]):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.3%}', ha='center', va='bottom')
            
            # Add significance indicator
            if conv.is_significant:
                ax1.text(0.5, max(conv.control_rate, conv.treatment_rate) * 1.15, 
                        f'Significant (p={conv.p_value:.3f})', 
                        ha='center', fontsize=10, color='green')
        
        # CTR
        if 'ctr' in results:
            ctr = results['ctr']
            ax2 = axes[0, 1]
            bars = ax2.bar(['Control', 'Treatment'], [ctr.control_rate, ctr.treatment_rate], 
                          color=['lightcoral', 'lightblue'])
            ax2.set_title('Click-Through Rate')
            ax2.set_ylabel('Rate')
            ax2.set_ylim(0, max(ctr.control_rate, ctr.treatment_rate) * 1.2)
            
            for bar, value in zip(bars, [ctr.control_rate, ctr.treatment_rate]):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.3%}', ha='center', va='bottom')
            
            if ctr.is_significant:
                ax2.text(0.5, max(ctr.control_rate, ctr.treatment_rate) * 1.15, 
                        f'Significant (p={ctr.p_value:.3f})', 
                        ha='center', fontsize=10, color='green')
        
        # View Rate
        if 'view_rate' in results:
            view = results['view_rate']
            ax3 = axes[1, 0]
            bars = ax3.bar(['Control', 'Treatment'], [view.control_rate, view.treatment_rate], 
                          color=['lightcoral', 'lightblue'])
            ax3.set_title('View Rate')
            ax3.set_ylabel('Rate')
            ax3.set_ylim(0, max(view.control_rate, view.treatment_rate) * 1.2)
            
            for bar, value in zip(bars, [view.control_rate, view.treatment_rate]):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.3%}', ha='center', va='bottom')
            
            if view.is_significant:
                ax3.text(0.5, max(view.control_rate, view.treatment_rate) * 1.15, 
                        f'Significant (p={view.p_value:.3f})', 
                        ha='center', fontsize=10, color='green')
        
        # Time Spent
        if 'time_spent' in results:
            ts = results['time_spent']
            ax4 = axes[1, 1]
            bars = ax4.bar(['Control', 'Treatment'], [ts['control_mean'], ts['treatment_mean']], 
                          color=['lightcoral', 'lightblue'])
            ax4.set_title('Average Time Spent')
            ax4.set_ylabel('Seconds')
            ax4.set_ylim(0, max(ts['control_mean'], ts['treatment_mean']) * 1.2)
            
            for bar, value in zip(bars, [ts['control_mean'], ts['treatment_mean']]):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}s', ha='center', va='bottom')
            
            if ts['is_significant']:
                ax4.text(0.5, max(ts['control_mean'], ts['treatment_mean']) * 1.15, 
                        f'Significant (p={ts["p_value"]:.3f})', 
                        ha='center', fontsize=10, color='green')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

def main():
    """Example usage of statistical analyzer"""
    # Load cleaned data
    try:
        df = pd.read_csv('ab_test_data_cleaned.csv')
        analyzer = ABTestStatisticalAnalyzer()
        
        # Run analysis
        results = analyzer.run_full_analysis(df)
        
        # Generate report
        report = analyzer.generate_report(results)
        print(report)
        
        # Create visualizations
        analyzer.visualize_results(results, 'ab_test_results.png')
        
    except FileNotFoundError:
        print("Cleaned data file not found. Please run data cleaning first.")
    except Exception as e:
        print(f"Error in statistical analysis: {e}")

if __name__ == "__main__":
    main()
