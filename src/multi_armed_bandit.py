"""
Multi-Armed Bandit Algorithms for Adaptive A/B Testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable
from abc import ABC, abstractmethod
import random
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class BanditArm:
    """Represents an arm in the multi-armed bandit problem"""
    arm_id: str
    name: str
    pulls: int = 0
    rewards: float = 0.0
    mean_reward: float = 0.0
    variance: float = 0.0
    
    def update(self, reward: float):
        """Update arm statistics with new reward"""
        self.pulls += 1
        self.rewards += reward
        
        # Update running mean and variance
        old_mean = self.mean_reward
        self.mean_reward = self.rewards / self.pulls
        
        if self.pulls > 1:
            # Update running variance
            self.variance = ((self.pulls - 1) * self.variance + 
                           (reward - old_mean) * (reward - self.mean_reward)) / self.pulls

class BanditAlgorithm(ABC):
    """Abstract base class for bandit algorithms"""
    
    def __init__(self, arms: List[str], arm_names: Optional[List[str]] = None):
        self.arms = arms
        self.arm_names = arm_names or [f"Arm_{i}" for i in range(len(arms))]
        self.bandit_arms = {
            arm_id: BanditArm(arm_id, name) 
            for arm_id, name in zip(arms, self.arm_names)
        }
        self.history = []
        self.round = 0
    
    @abstractmethod
    def select_arm(self) -> str:
        """Select which arm to pull next"""
        pass
    
    @abstractmethod
    def update(self, arm_id: str, reward: float):
        """Update algorithm with observed reward"""
        pass
    
    def get_arm_statistics(self) -> Dict[str, Dict]:
        """Get current statistics for all arms"""
        return {
            arm_id: {
                'name': arm.name,
                'pulls': arm.pulls,
                'rewards': arm.rewards,
                'mean_reward': arm.mean_reward,
                'variance': arm.variance,
                'pull_percentage': arm.pulls / max(1, sum(a.pulls for a in self.bandit_arms.values()))
            }
            for arm_id, arm in self.bandit_arms.items()
        }
    
    def get_total_pulls(self) -> int:
        """Get total number of pulls across all arms"""
        return sum(arm.pulls for arm in self.bandit_arms.values())
    
    def get_best_arm(self) -> Tuple[str, float]:
        """Get the arm with highest mean reward"""
        best_arm_id = max(self.bandit_arms.keys(), 
                        key=lambda x: self.bandit_arms[x].mean_reward)
        return best_arm_id, self.bandit_arms[best_arm_id].mean_reward
    
    def save_state(self, filepath: str):
        """Save algorithm state to file"""
        state = {
            'algorithm': self.__class__.__name__,
            'arms': self.arms,
            'arm_names': self.arm_names,
            'bandit_arms': {
                arm_id: {
                    'arm_id': arm.arm_id,
                    'name': arm.name,
                    'pulls': arm.pulls,
                    'rewards': arm.rewards,
                    'mean_reward': arm.mean_reward,
                    'variance': arm.variance
                }
                for arm_id, arm in self.bandit_arms.items()
            },
            'history': self.history,
            'round': self.round
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load algorithm state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.round = state['round']
        self.history = state['history']
        
        for arm_id, arm_data in state['bandit_arms'].items():
            arm = self.bandit_arms[arm_id]
            arm.pulls = arm_data['pulls']
            arm.rewards = arm_data['rewards']
            arm.mean_reward = arm_data['mean_reward']
            arm.variance = arm_data['variance']

class EpsilonGreedy(BanditAlgorithm):
    """Epsilon-Greedy algorithm with exploration/exploitation trade-off"""
    
    def __init__(self, arms: List[str], arm_names: Optional[List[str]] = None, 
                 epsilon: float = 0.1, epsilon_decay: float = 1.0):
        super().__init__(arms, arm_names)
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.initial_epsilon = epsilon
    
    def select_arm(self) -> str:
        """Select arm using epsilon-greedy strategy"""
        if random.random() < self.epsilon:
            # Exploration: random arm
            return random.choice(self.arms)
        else:
            # Exploitation: best arm so far
            best_arm_id, _ = self.get_best_arm()
            return best_arm_id
    
    def update(self, arm_id: str, reward: float):
        """Update algorithm with observed reward"""
        self.bandit_arms[arm_id].update(reward)
        self.history.append({
            'round': self.round,
            'arm_id': arm_id,
            'reward': reward,
            'epsilon': self.epsilon
        })
        self.round += 1
        
        # Decay epsilon
        self.epsilon *= self.epsilon_decay

class UCB1(BanditAlgorithm):
    """Upper Confidence Bound algorithm"""
    
    def __init__(self, arms: List[str], arm_names: Optional[List[str]] = None, 
                 c: float = 2.0):
        super().__init__(arms, arm_names)
        self.c = c
    
    def select_arm(self) -> str:
        """Select arm using UCB1 strategy"""
        total_pulls = self.get_total_pulls()
        
        if total_pulls == 0:
            # First round: play each arm once
            unplayed_arms = [arm_id for arm_id, arm in self.bandit_arms.items() if arm.pulls == 0]
            if unplayed_arms:
                return random.choice(unplayed_arms)
        
        # Calculate UCB values
        ucb_values = {}
        for arm_id, arm in self.bandit_arms.items():
            if arm.pulls == 0:
                ucb_values[arm_id] = float('inf')
            else:
                exploration_bonus = self.c * np.sqrt(np.log(total_pulls) / arm.pulls)
                ucb_values[arm_id] = arm.mean_reward + exploration_bonus
        
        # Select arm with highest UCB value
        return max(ucb_values.keys(), key=lambda x: ucb_values[x])
    
    def update(self, arm_id: str, reward: float):
        """Update algorithm with observed reward"""
        self.bandit_arms[arm_id].update(reward)
        self.history.append({
            'round': self.round,
            'arm_id': arm_id,
            'reward': reward,
            'ucb_values': self._calculate_ucb_values()
        })
        self.round += 1
    
    def _calculate_ucb_values(self) -> Dict[str, float]:
        """Calculate current UCB values for all arms"""
        total_pulls = self.get_total_pulls()
        ucb_values = {}
        
        for arm_id, arm in self.bandit_arms.items():
            if arm.pulls == 0:
                ucb_values[arm_id] = float('inf')
            else:
                exploration_bonus = self.c * np.sqrt(np.log(total_pulls) / arm.pulls)
                ucb_values[arm_id] = arm.mean_reward + exploration_bonus
        
        return ucb_values

class ThompsonSampling(BanditAlgorithm):
    """Thompson Sampling algorithm using Beta distribution"""
    
    def __init__(self, arms: List[str], arm_names: Optional[List[str]] = None):
        super().__init__(arms, arm_names)
        # Beta distribution parameters for each arm (alpha, beta)
        self.alpha_params = {arm_id: 1.0 for arm_id in arms}
        self.beta_params = {arm_id: 1.0 for arm_id in arms}
    
    def select_arm(self) -> str:
        """Select arm using Thompson Sampling"""
        samples = {}
        
        for arm_id in self.arms:
            # Sample from Beta distribution
            sample = np.random.beta(self.alpha_params[arm_id], self.beta_params[arm_id])
            samples[arm_id] = sample
        
        # Select arm with highest sample
        return max(samples.keys(), key=lambda x: samples[x])
    
    def update(self, arm_id: str, reward: float):
        """Update algorithm with observed reward"""
        # Update Beta distribution parameters
        self.alpha_params[arm_id] += reward
        self.beta_params[arm_id] += (1 - reward)
        
        # Update bandit arm statistics
        self.bandit_arms[arm_id].update(reward)
        
        self.history.append({
            'round': self.round,
            'arm_id': arm_id,
            'reward': reward,
            'alpha': self.alpha_params[arm_id],
            'beta': self.beta_params[arm_id]
        })
        self.round += 1

class ABTestBandit:
    """Multi-armed bandit for A/B testing with multiple variants"""
    
    def __init__(self, algorithm: str = 'thompson_sampling', variants: List[str] = None,
                 **algorithm_params):
        self.variants = variants or ['control', 'treatment_a', 'treatment_b']
        self.algorithm_name = algorithm
        
        # Initialize algorithm
        if algorithm == 'epsilon_greedy':
            self.algorithm = EpsilonGreedy(self.variants, **algorithm_params)
        elif algorithm == 'ucb1':
            self.algorithm = UCB1(self.variants, **algorithm_params)
        elif algorithm == 'thompson_sampling':
            self.algorithm = ThompsonSampling(self.variants, **algorithm_params)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.conversion_data = []
        self.traffic_allocations = {variant: 0 for variant in self.variants}
    
    def assign_user_to_variant(self) -> str:
        """Assign user to variant using bandit algorithm"""
        variant = self.algorithm.select_arm()
        self.traffic_allocations[variant] += 1
        return variant
    
    def record_conversion(self, user_id: str, variant: str, converted: bool):
        """Record conversion event for bandit learning"""
        reward = 1.0 if converted else 0.0
        self.algorithm.update(variant, reward)
        
        self.conversion_data.append({
            'user_id': user_id,
            'variant': variant,
            'converted': converted,
            'reward': reward,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary of all variants"""
        stats = self.algorithm.get_arm_statistics()
        
        summary = {
            'algorithm': self.algorithm_name,
            'total_rounds': self.algorithm.round,
            'total_conversions': len([c for c in self.conversion_data if c['converted']]),
            'variants': {}
        }
        
        for variant, stat in stats.items():
            conversion_rate = stat['mean_reward']
            total_conversions = int(stat['rewards'])
            
            summary['variants'][variant] = {
                'name': stat['name'],
                'conversion_rate': conversion_rate,
                'total_conversions': total_conversions,
                'total_users': stat['pulls'],
                'pull_percentage': stat['pull_percentage'] * 100,
                'variance': stat['variance']
            }
        
        return summary
    
    def get_best_variant(self) -> Tuple[str, float]:
        """Get the best performing variant"""
        return self.algorithm.get_best_arm()
    
    def simulate_ab_test(self, true_conversion_rates: Dict[str, float], 
                        n_users: int = 10000) -> Dict:
        """Simulate A/B test with known true conversion rates"""
        results = {
            'algorithm': self.algorithm_name,
            'true_rates': true_conversion_rates,
            'simulation_results': []
        }
        
        for user_id in range(n_users):
            # Assign user to variant
            variant = self.assign_user_to_variant()
            
            # Simulate conversion based on true rate
            true_rate = true_conversion_rates[variant]
            converted = np.random.random() < true_rate
            
            # Record conversion
            self.record_conversion(f"user_{user_id}", variant, converted)
            
            # Store intermediate results
            if (user_id + 1) % 1000 == 0:
                summary = self.get_performance_summary()
                results['simulation_results'].append({
                    'users': user_id + 1,
                    'best_variant': self.get_best_variant()[0],
                    'summary': summary
                })
        
        return results
    
    def plot_performance(self, save_path: Optional[str] = None):
        """Plot performance of all variants"""
        stats = self.algorithm.get_arm_statistics()
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Bandit Performance - {self.algorithm_name.replace("_", " ").title()}', 
                     fontsize=16, fontweight='bold')
        
        # Conversion rates
        variants = list(stats.keys())
        rates = [stats[v]['mean_reward'] for v in variants]
        
        ax1 = axes[0, 0]
        bars = ax1.bar(variants, rates, color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(variants)])
        ax1.set_title('Conversion Rates by Variant')
        ax1.set_ylabel('Conversion Rate')
        ax1.set_ylim(0, max(rates) * 1.2 if rates else 1)
        
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.3%}', ha='center', va='bottom')
        
        # Traffic allocation
        allocations = [stats[v]['pulls'] for v in variants]
        
        ax2 = axes[0, 1]
        ax2.pie(allocations, labels=variants, autopct='%1.1f%%', 
                colors=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(variants)])
        ax2.set_title('Traffic Allocation')
        
        # Cumulative rewards over time
        if self.algorithm.history:
            rounds = [h['round'] for h in self.algorithm.history]
            cumulative_rewards = []
            running_total = 0
            
            for h in self.algorithm.history:
                running_total += h['reward']
                cumulative_rewards.append(running_total)
            
            ax3 = axes[1, 0]
            ax3.plot(rounds, cumulative_rewards, linewidth=2)
            ax3.set_title('Cumulative Conversions Over Time')
            ax3.set_xlabel('Round')
            ax3.set_ylabel('Cumulative Conversions')
            ax3.grid(True, alpha=0.3)
        
        # Performance over time (if available)
        if len(self.algorithm.history) > 100:
            # Calculate moving average of rewards
            window_size = min(100, len(self.algorithm.history) // 10)
            moving_avg = []
            
            for i in range(len(self.algorithm.history)):
                start_idx = max(0, i - window_size + 1)
                recent_rewards = [h['reward'] for h in self.algorithm.history[start_idx:i+1]]
                moving_avg.append(np.mean(recent_rewards) if recent_rewards else 0)
            
            ax4 = axes[1, 1]
            ax4.plot(range(len(moving_avg)), moving_avg, linewidth=2, color='red')
            ax4.set_title(f'Moving Average Reward (Window={window_size})')
            ax4.set_xlabel('Round')
            ax4.set_ylabel('Average Reward')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def export_results(self, filepath: str):
        """Export results to CSV"""
        if not self.conversion_data:
            return
        
        df = pd.DataFrame(self.conversion_data)
        df.to_csv(filepath, index=False)
        
        # Also export summary statistics
        summary_path = filepath.replace('.csv', '_summary.json')
        summary = self.get_performance_summary()
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

# Example usage and testing
def test_bandit_algorithms():
    """Test different bandit algorithms"""
    
    # True conversion rates for simulation
    true_rates = {
        'control': 0.03,      # 3% conversion
        'treatment_a': 0.045,  # 4.5% conversion (50% improvement)
        'treatment_b': 0.025   # 2.5% conversion (worse)
    }
    
    algorithms = [
        ('epsilon_greedy', {'epsilon': 0.1}),
        ('ucb1', {'c': 2.0}),
        ('thompson_sampling', {})
    ]
    
    results = {}
    
    for alg_name, params in algorithms:
        print(f"\nTesting {alg_name.replace('_', ' ').title()}...")
        
        bandit = ABTestBandit(algorithm=alg_name, variants=list(true_rates.keys()), **params)
        result = bandit.simulate_ab_test(true_rates, n_users=5000)
        
        results[alg_name] = result
        
        # Print final results
        final_summary = result['simulation_results'][-1]['summary']
        best_variant, best_rate = bandit.get_best_variant()
        
        print(f"Best variant: {best_variant} ({best_rate:.3%})")
        print(f"Total conversions: {final_summary['total_conversions']}")
        
        for variant, stats in final_summary['variants'].items():
            print(f"  {variant}: {stats['conversion_rate']:.3%} ({stats['total_users']} users)")
    
    return results

if __name__ == "__main__":
    # Test the bandit algorithms
    results = test_bandit_algorithms()
    
    # Create a Thompson Sampling bandit for A/B testing
    bandit = ABTestBandit(algorithm='thompson_sampling', 
                         variants=['control', 'treatment_a', 'treatment_b'])
    
    # Simulate with different true rates
    true_rates = {'control': 0.03, 'treatment_a': 0.045, 'treatment_b': 0.025}
    simulation_result = bandit.simulate_ab_test(true_rates, n_users=10000)
    
    # Plot results
    bandit.plot_performance('bandit_performance.png')
    
    # Export results
    bandit.export_results('bandit_results.csv')
    
    print("\nBandit simulation completed!")
    print(f"Best variant: {bandit.get_best_variant()[0]}")
    print(f"Performance summary saved to 'bandit_performance.png'")
    print(f"Raw data saved to 'bandit_results.csv'")
