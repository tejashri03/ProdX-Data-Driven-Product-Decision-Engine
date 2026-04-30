"""
Bayesian Statistical Methods for A/B Testing
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

@dataclass
class BayesianResult:
    """Results from Bayesian A/B test analysis"""
    metric: str
    control_posterior_mean: float
    treatment_posterior_mean: float
    control_posterior_std: float
    treatment_posterior_std: float
    probability_treatment_better: float
    expected_loss: float
    credible_interval_control: Tuple[float, float]
    credible_interval_treatment: Tuple[float, float]
    relative_lift: float
    sample_size_control: int
    sample_size_treatment: int

class BayesianABTest:
    """
    Bayesian A/B testing using conjugate priors
    """
    
    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0, 
                 credible_interval: float = 0.95):
        """
        Initialize Bayesian A/B test
        
        Args:
            prior_alpha: Alpha parameter for Beta prior (default: 1.0 for uniform prior)
            prior_beta: Beta parameter for Beta prior (default: 1.0 for uniform prior)
            credible_interval: Credible interval level (default: 0.95)
        """
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.credible_interval = credible_interval
        
    def beta_binomial_test(self, control_successes: int, control_trials: int,
                           treatment_successes: int, treatment_trials: int) -> BayesianResult:
        """
        Perform Bayesian A/B test using Beta-Binomial conjugate prior
        
        Args:
            control_successes: Number of successes in control group
            control_trials: Number of trials in control group
            treatment_successes: Number of successes in treatment group
            treatment_trials: Number of trials in treatment group
            
        Returns:
            BayesianResult object with analysis results
        """
        # Update prior with data to get posterior
        control_alpha = self.prior_alpha + control_successes
        control_beta = self.prior_beta + control_trials - control_successes
        treatment_alpha = self.prior_alpha + treatment_successes
        treatment_beta = self.prior_beta + treatment_trials - treatment_successes
        
        # Calculate posterior statistics
        control_mean = control_alpha / (control_alpha + control_beta)
        treatment_mean = treatment_alpha / (treatment_alpha + treatment_beta)
        
        control_var = (control_alpha * control_beta) / (
            (control_alpha + control_beta)**2 * (control_alpha + control_beta + 1)
        )
        treatment_var = (treatment_alpha * treatment_beta) / (
            (treatment_alpha + treatment_beta)**2 * (treatment_alpha + treatment_beta + 1)
        )
        
        control_std = np.sqrt(control_var)
        treatment_std = np.sqrt(treatment_var)
        
        # Calculate probability that treatment is better than control
        # P(T > C) = ∫∫ I(t > c) * Beta(t|α_T, β_T) * Beta(c|α_C, β_C) dt dc
        # This can be calculated analytically for Beta distributions
        prob_treatment_better = self._calculate_probability_treatment_better(
            treatment_alpha, treatment_beta, control_alpha, control_beta
        )
        
        # Calculate expected loss if we choose treatment
        expected_loss = self._calculate_expected_loss(
            treatment_mean, treatment_alpha, treatment_beta,
            control_mean, control_alpha, control_beta
        )
        
        # Calculate credible intervals
        ci_lower = (1 - self.credible_interval) / 2
        ci_upper = 1 - ci_lower
        
        control_ci = (
            stats.beta.ppf(ci_lower, control_alpha, control_beta),
            stats.beta.ppf(ci_upper, control_alpha, control_beta)
        )
        
        treatment_ci = (
            stats.beta.ppf(ci_lower, treatment_alpha, treatment_beta),
            stats.beta.ppf(ci_upper, treatment_alpha, treatment_beta)
        )
        
        # Calculate relative lift
        relative_lift = (treatment_mean - control_mean) / control_mean if control_mean > 0 else 0
        
        return BayesianResult(
            metric="Conversion Rate",
            control_posterior_mean=control_mean,
            treatment_posterior_mean=treatment_mean,
            control_posterior_std=control_std,
            treatment_posterior_std=treatment_std,
            probability_treatment_better=prob_treatment_better,
            expected_loss=expected_loss,
            credible_interval_control=control_ci,
            credible_interval_treatment=treatment_ci,
            relative_lift=relative_lift,
            sample_size_control=control_trials,
            sample_size_treatment=treatment_trials
        )
    
    def _calculate_probability_treatment_better(self, t_alpha: float, t_beta: float,
                                               c_alpha: float, c_beta: float) -> float:
        """
        Calculate P(T > C) for Beta distributions using Monte Carlo integration
        """
        n_samples = 100000
        
        # Sample from posterior distributions
        treatment_samples = np.random.beta(t_alpha, t_beta, n_samples)
        control_samples = np.random.beta(c_alpha, c_beta, n_samples)
        
        # Calculate probability
        prob_treatment_better = np.mean(treatment_samples > control_samples)
        
        return prob_treatment_better
    
    def _calculate_expected_loss(self, t_mean: float, t_alpha: float, t_beta: float,
                                 c_mean: float, c_alpha: float, c_beta: float) -> float:
        """
        Calculate expected loss if we choose treatment
        Loss = max(0, control - treatment)
        """
        n_samples = 100000
        
        # Sample from posterior distributions
        treatment_samples = np.random.beta(t_alpha, t_beta, n_samples)
        control_samples = np.random.beta(c_alpha, c_beta, n_samples)
        
        # Calculate expected loss (only when control is better)
        losses = np.maximum(0, control_samples - treatment_samples)
        expected_loss = np.mean(losses)
        
        return expected_loss
    
    def normal_normal_test(self, control_mean: float, control_std: float, control_n: int,
                          treatment_mean: float, treatment_std: float, treatment_n: int) -> BayesianResult:
        """
        Perform Bayesian A/B test for continuous metrics using Normal-Normal conjugate prior
        
        Args:
            control_mean: Sample mean of control group
            control_std: Sample standard deviation of control group
            control_n: Sample size of control group
            treatment_mean: Sample mean of treatment group
            treatment_std: Sample standard deviation of treatment group
            treatment_n: Sample size of treatment group
            
        Returns:
            BayesianResult object with analysis results
        """
        # Prior parameters (non-informative prior)
        prior_mu = 0
        prior_precision = 1e-6  # Very small precision for non-informative prior
        
        # Posterior parameters for control
        control_posterior_precision = prior_precision + control_n / (control_std**2)
        control_posterior_mu = (prior_precision * prior_mu + 
                                control_n * control_mean / (control_std**2)) / control_posterior_precision
        control_posterior_var = 1 / control_posterior_precision
        
        # Posterior parameters for treatment
        treatment_posterior_precision = prior_precision + treatment_n / (treatment_std**2)
        treatment_posterior_mu = (prior_precision * prior_mu + 
                                 treatment_n * treatment_mean / (treatment_std**2)) / treatment_posterior_precision
        treatment_posterior_var = 1 / treatment_posterior_precision
        
        # Calculate probability that treatment is better than control
        # For normal distributions: T - C ~ N(μ_T - μ_C, σ_T² + σ_C²)
        diff_mean = treatment_posterior_mu - control_posterior_mu
        diff_var = treatment_posterior_var + control_posterior_var
        diff_std = np.sqrt(diff_var)
        
        prob_treatment_better = 1 - stats.norm.cdf(0, diff_mean, diff_std)
        
        # Calculate expected loss
        from scipy.integrate import quad
        
        def loss_function(x):
            """Loss function: max(0, control - treatment)"""
            return np.maximum(0, -x)
        
        # Expected loss = E[max(0, C - T)] = E[max(0, -(T - C))]
        # For normal distribution, this has a closed form
        if diff_std > 0:
            z = -diff_mean / diff_std
            expected_loss = diff_std * (z * stats.norm.cdf(z) + stats.norm.pdf(z))
        else:
            expected_loss = max(0, -diff_mean)
        
        # Calculate credible intervals
        ci_lower = (1 - self.credible_interval) / 2
        ci_upper = 1 - ci_lower
        
        control_ci = (
            stats.norm.ppf(ci_lower, control_posterior_mu, np.sqrt(control_posterior_var)),
            stats.norm.ppf(ci_upper, control_posterior_mu, np.sqrt(control_posterior_var))
        )
        
        treatment_ci = (
            stats.norm.ppf(ci_lower, treatment_posterior_mu, np.sqrt(treatment_posterior_var)),
            stats.norm.ppf(ci_upper, treatment_posterior_mu, np.sqrt(treatment_posterior_var))
        )
        
        # Calculate relative lift
        relative_lift = (treatment_posterior_mu - control_posterior_mu) / abs(control_posterior_mu) if control_posterior_mu != 0 else 0
        
        return BayesianResult(
            metric="Continuous Metric",
            control_posterior_mean=control_posterior_mu,
            treatment_posterior_mean=treatment_posterior_mu,
            control_posterior_std=np.sqrt(control_posterior_var),
            treatment_posterior_std=np.sqrt(treatment_posterior_var),
            probability_treatment_better=prob_treatment_better,
            expected_loss=expected_loss,
            credible_interval_control=control_ci,
            credible_interval_treatment=treatment_ci,
            relative_lift=relative_lift,
            sample_size_control=control_n,
            sample_size_treatment=treatment_n
        )
    
    def plot_posterior_distributions(self, result: BayesianResult, save_path: Optional[str] = None):
        """
        Plot posterior distributions for control and treatment groups
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Bayesian A/B Test Analysis - {result.metric}', 
                     fontsize=16, fontweight='bold')
        
        # Posterior distributions
        ax1 = axes[0, 0]
        x = np.linspace(0, max(result.control_posterior_mean, result.treatment_posterior_mean) * 2, 1000)
        
        # Plot control posterior
        control_dist = stats.beta(
            self.prior_alpha + result.sample_size_control * result.control_posterior_mean,
            self.prior_beta + result.sample_size_control * (1 - result.control_posterior_mean)
        )
        control_pdf = control_dist.pdf(x)
        ax1.plot(x, control_pdf, label='Control', linewidth=2, color='blue')
        
        # Plot treatment posterior
        treatment_dist = stats.beta(
            self.prior_alpha + result.sample_size_treatment * result.treatment_posterior_mean,
            self.prior_beta + result.sample_size_treatment * (1 - result.treatment_posterior_mean)
        )
        treatment_pdf = treatment_dist.pdf(x)
        ax1.plot(x, treatment_pdf, label='Treatment', linewidth=2, color='red')
        
        ax1.set_title('Posterior Distributions')
        ax1.set_xlabel('Conversion Rate')
        ax1.set_ylabel('Probability Density')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Credible intervals
        ax2 = axes[0, 1]
        methods = ['Control', 'Treatment']
        means = [result.control_posterior_mean, result.treatment_posterior_mean]
        cis = [result.credible_interval_control, result.credible_interval_treatment]
        colors = ['blue', 'red']
        
        for i, (method, mean, ci, color) in enumerate(zip(methods, means, cis, colors)):
            ax2.errorbar(i, mean, yerr=[[mean - ci[0]], [ci[1] - mean]], 
                        fmt='o', linewidth=2, markersize=8, color=color, label=method)
        
        ax2.set_title('Posterior Means with Credible Intervals')
        ax2.set_ylabel('Conversion Rate')
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(methods)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Probability and expected loss
        ax3 = axes[1, 0]
        metrics = ['P(Treatment > Control)', 'Expected Loss']
        values = [result.probability_treatment_better, result.expected_loss]
        colors = ['green' if result.probability_treatment_better > 0.95 else 'orange',
                 'red' if result.expected_loss > 0.01 else 'green']
        
        bars = ax3.bar(metrics, values, color=colors, alpha=0.7)
        ax3.set_title('Decision Metrics')
        ax3.set_ylabel('Value')
        ax3.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # Decision threshold line
        ax3.axhline(y=0.95, color='green', linestyle='--', alpha=0.5, label='Decision Threshold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Sample sizes and relative lift
        ax4 = axes[1, 1]
        info_text = f"""Sample Sizes:
Control: {result.sample_size_control:,}
Treatment: {result.sample_size_treatment:,}

Relative Lift: {result.relative_lift:.2%}

Decision: {'Launch Treatment' if result.probability_treatment_better > 0.95 else 'Continue Testing'}
Confidence: {result.probability_treatment_better:.1%}"""
        
        ax4.text(0.1, 0.5, info_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax4.set_title('Summary Statistics')
        ax4.axis('off')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def make_decision(self, result: BayesianResult, threshold: float = 0.95) -> Dict:
        """
        Make decision based on Bayesian analysis
        
        Args:
            result: BayesianResult from analysis
            threshold: Probability threshold for making decision
            
        Returns:
            Dictionary with decision and reasoning
        """
        if result.probability_treatment_better > threshold:
            decision = "Launch Treatment"
            confidence = result.probability_treatment_better
        elif result.probability_treatment_better < (1 - threshold):
            decision = "Keep Control"
            confidence = 1 - result.probability_treatment_better
        else:
            decision = "Continue Testing"
            confidence = result.probability_treatment_better
        
        reasoning = f"""
        Probability Treatment > Control: {result.probability_treatment_better:.3%}
        Expected Loss: {result.expected_loss:.6f}
        Relative Lift: {result.relative_lift:.2%}
        
        Decision Rule:
        - Launch if P(T > C) > {threshold:.1%}
        - Keep Control if P(T > C) < {(1-threshold):.1%}
        - Continue Testing otherwise
        """
        
        return {
            'decision': decision,
            'confidence': confidence,
            'probability_treatment_better': result.probability_treatment_better,
            'expected_loss': result.expected_loss,
            'relative_lift': result.relative_lift,
            'reasoning': reasoning.strip()
        }

class BayesianAnalyzer:
    """
    High-level Bayesian analysis for A/B testing experiments
    """
    
    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.bayesian_test = BayesianABTest(prior_alpha, prior_beta)
    
    def analyze_experiment(self, df: pd.DataFrame, group_col: str = 'group',
                          success_col: str = 'purchased', trial_col: str = 'user_id') -> Dict:
        """
        Analyze A/B test experiment using Bayesian methods
        
        Args:
            df: DataFrame with experiment data
            group_col: Column name for group assignment
            success_col: Column name for success indicator (0/1)
            trial_col: Column name for trial identifier
            
        Returns:
            Dictionary with analysis results
        """
        results = {}
        
        # Get unique groups
        groups = df[group_col].unique()
        if len(groups) != 2:
            raise ValueError("Experiment must have exactly 2 groups")
        
        # Assign control and treatment
        control_group = groups[0]
        treatment_group = groups[1]
        
        # Calculate successes and trials for each group
        control_data = df[df[group_col] == control_group]
        treatment_data = df[df[group_col] == treatment_group]
        
        control_successes = control_data[success_col].sum()
        control_trials = len(control_data)
        treatment_successes = treatment_data[success_col].sum()
        treatment_trials = len(treatment_data)
        
        # Perform Bayesian analysis
        result = self.bayesian_test.beta_binomial_test(
            control_successes, control_trials,
            treatment_successes, treatment_trials
        )
        
        # Make decision
        decision = self.bayesian_test.make_decision(result)
        
        return {
            'bayesian_result': result,
            'decision': decision,
            'control_stats': {
                'successes': control_successes,
                'trials': control_trials,
                'observed_rate': control_successes / control_trials
            },
            'treatment_stats': {
                'successes': treatment_successes,
                'trials': treatment_trials,
                'observed_rate': treatment_successes / treatment_trials
            }
        }
    
    def sequential_analysis(self, df: pd.DataFrame, group_col: str = 'group',
                          success_col: str = 'purchased', date_col: str = 'timestamp',
                          min_samples_per_group: int = 100) -> List[Dict]:
        """
        Perform sequential Bayesian analysis over time
        
        Args:
            df: DataFrame with experiment data
            group_col: Column name for group assignment
            success_col: Column name for success indicator
            date_col: Column name for timestamp
            min_samples_per_group: Minimum samples per group for analysis
            
        Returns:
            List of analysis results over time
        """
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col])
        
        # Sort by date
        df = df.sort_values(date_col)
        
        # Get unique dates
        dates = df[date_col].dt.date.unique()
        
        sequential_results = []
        
        for date in dates:
            # Get data up to this date
            date_data = df[df[date_col].dt.date <= date]
            
            # Check if we have enough data
            group_counts = date_data[group_col].value_counts()
            if len(group_counts) >= 2 and all(count >= min_samples_per_group for count in group_counts.values):
                # Perform analysis
                try:
                    result = self.analyze_experiment(date_data, group_col, success_col)
                    result['date'] = str(date)
                    result['cumulative_samples'] = len(date_data)
                    sequential_results.append(result)
                except Exception as e:
                    print(f"Error analyzing date {date}: {e}")
                    continue
        
        return sequential_results
    
    def plot_sequential_analysis(self, sequential_results: List[Dict], save_path: Optional[str] = None):
        """
        Plot sequential analysis results over time
        """
        if not sequential_results:
            print("No sequential results to plot")
            return
        
        dates = [pd.to_datetime(r['date']) for r in sequential_results]
        probabilities = [r['decision']['probability_treatment_better'] for r in sequential_results]
        lifts = [r['bayesian_result'].relative_lift for r in sequential_results]
        samples = [r['cumulative_samples'] for r in sequential_results]
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 12))
        fig.suptitle('Sequential Bayesian Analysis', fontsize=16, fontweight='bold')
        
        # Probability over time
        ax1 = axes[0]
        ax1.plot(dates, probabilities, linewidth=2, marker='o', markersize=4)
        ax1.axhline(y=0.95, color='green', linestyle='--', alpha=0.7, label='Launch Threshold')
        ax1.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='Stop Threshold')
        ax1.set_title('Probability Treatment > Control Over Time')
        ax1.set_ylabel('Probability')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Relative lift over time
        ax2 = axes[1]
        ax2.plot(dates, lifts, linewidth=2, marker='o', markersize=4, color='orange')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Relative Lift Over Time')
        ax2.set_ylabel('Relative Lift')
        ax2.grid(True, alpha=0.3)
        
        # Sample size over time
        ax3 = axes[2]
        ax3.plot(dates, samples, linewidth=2, marker='o', markersize=4, color='purple')
        ax3.set_title('Cumulative Sample Size Over Time')
        ax3.set_ylabel('Sample Size')
        ax3.set_xlabel('Date')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

def test_bayesian_testing():
    """Test Bayesian A/B testing functionality"""
    
    # Create sample data
    np.random.seed(42)
    n_users = 10000
    
    # True conversion rates
    true_control_rate = 0.03
    true_treatment_rate = 0.045  # 50% improvement
    
    # Generate data
    control_conversions = np.random.binomial(1, true_control_rate, n_users // 2)
    treatment_conversions = np.random.binomial(1, true_treatment_rate, n_users // 2)
    
    control_successes = control_conversions.sum()
    control_trials = len(control_conversions)
    treatment_successes = treatment_conversions.sum()
    treatment_trials = len(treatment_conversions)
    
    print(f"Control: {control_successes}/{control_trials} ({control_successes/control_trials:.3%})")
    print(f"Treatment: {treatment_successes}/{treatment_trials} ({treatment_successes/treatment_trials:.3%})")
    
    # Perform Bayesian analysis
    bayesian_test = BayesianABTest()
    result = bayesian_test.beta_binomial_test(
        control_successes, control_trials,
        treatment_successes, treatment_trials
    )
    
    print(f"\nBayesian Results:")
    print(f"Probability Treatment > Control: {result.probability_treatment_better:.3%}")
    print(f"Expected Loss: {result.expected_loss:.6f}")
    print(f"Relative Lift: {result.relative_lift:.2%}")
    
    # Make decision
    decision = bayesian_test.make_decision(result)
    print(f"\nDecision: {decision['decision']}")
    print(f"Confidence: {decision['confidence']:.3%}")
    
    # Plot results
    bayesian_test.plot_posterior_distributions(result, 'bayesian_analysis.png')
    
    return result

if __name__ == "__main__":
    # Test Bayesian A/B testing
    result = test_bayesian_testing()
    
    print("\nBayesian A/B testing completed!")
    print("Visualization saved to 'bayesian_analysis.png'")
