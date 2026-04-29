import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Tuple, Dict, List
import json

class ABTestDataGenerator:
    """
    Generate synthetic A/B testing data for e-commerce experiment
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        
        # Experiment parameters
        self.n_users = 100000  # Total users
        self.split_ratio = 0.5  # 50/50 split
        
        # Baseline metrics (Control Group)
        self.baseline_view_rate = 0.85  # 85% of users view PDP
        self.baseline_ctr = 0.12  # 12% CTR on Add to Cart
        self.baseline_conversion = 0.032  # 3.2% conversion rate
        self.baseline_time_spent = 120  # seconds
        
        # Treatment effect (Group B improvements)
        self.treatment_view_lift = 0.02  # 2% lift in view rate
        self.treatment_ctr_lift = 0.15  # 15% lift in CTR
        self.treatment_conversion_lift = 0.08  # 8% lift in conversion
        self.treatment_time_lift = 0.10  # 10% lift in time spent
        
        # Device distribution
        self.device_probs = {'mobile': 0.65, 'desktop': 0.25, 'tablet': 0.10}
        
        # Geographic distribution
        self.regions = ['North America', 'Europe', 'Asia', 'South America', 'Africa']
        self.region_probs = [0.35, 0.30, 0.20, 0.10, 0.05]
        
    def generate_user_ids(self, n: int) -> List[str]:
        """Generate unique user IDs"""
        return [f"user_{i:06d}" for i in range(1, n + 1)]
    
    def assign_groups(self, user_ids: List[str]) -> List[str]:
        """Assign users to control (A) or treatment (B) groups"""
        n = len(user_ids)
        n_control = int(n * self.split_ratio)
        
        groups = ['A'] * n_control + ['B'] * (n - n_control)
        random.shuffle(groups)
        return groups
    
    def assign_devices(self, n: int) -> List[str]:
        """Assign device types based on real distribution"""
        devices = np.random.choice(
            list(self.device_probs.keys()),
            size=n,
            p=list(self.device_probs.values())
        )
        return devices.tolist()
    
    def assign_regions(self, n: int) -> List[str]:
        """Assign geographic regions"""
        regions = np.random.choice(self.regions, size=n, p=self.region_probs)
        return regions.tolist()
    
    def assign_new_user_flag(self, n: int) -> List[bool]:
        """Assign new vs returning user status (30% new users)"""
        return np.random.choice([True, False], size=n, p=[0.3, 0.7])
    
    def simulate_user_behavior(self, group: str, device: str, is_new_user: bool) -> Tuple[bool, bool, bool, float]:
        """
        Simulate user behavior based on group and characteristics
        Returns: (viewed, clicked, purchased, time_spent)
        """
        # Adjust base rates based on user characteristics
        view_rate = self.baseline_view_rate
        ctr = self.baseline_ctr
        conversion = self.baseline_conversion
        time_spent = self.baseline_time_spent
        
        # Apply treatment effects for Group B
        if group == 'B':
            view_rate *= (1 + self.treatment_view_lift)
            ctr *= (1 + self.treatment_ctr_lift)
            conversion *= (1 + self.treatment_conversion_lift)
            time_spent *= (1 + self.treatment_time_lift)
        
        # Device-specific adjustments
        if device == 'mobile':
            view_rate *= 0.95
            ctr *= 1.1
            time_spent *= 0.8
        elif device == 'tablet':
            view_rate *= 1.05
            ctr *= 0.9
            time_spent *= 1.2
        
        # New user adjustments
        if is_new_user:
            view_rate *= 0.9
            ctr *= 0.8
            conversion *= 0.7
            time_spent *= 1.3
        
        # Simulate behavior with some randomness
        viewed = np.random.random() < view_rate
        clicked = viewed and (np.random.random() < ctr)
        purchased = clicked and (np.random.random() < conversion)
        
        # Time spent only if viewed
        if viewed:
            # Add some variance to time spent
            time_spent = max(10, np.random.normal(time_spent, time_spent * 0.3))
        else:
            time_spent = 0
        
        return viewed, clicked, purchased, time_spent
    
    def generate_dataset(self) -> pd.DataFrame:
        """Generate complete A/B testing dataset"""
        print("Generating A/B testing dataset...")
        
        # Generate user characteristics
        user_ids = self.generate_user_ids(self.n_users)
        groups = self.assign_groups(user_ids)
        devices = self.assign_devices(self.n_users)
        regions = self.assign_regions(self.n_users)
        new_users = self.assign_new_user_flag(self.n_users)
        
        # Simulate behavior for each user
        data = []
        for i in range(self.n_users):
            viewed, clicked, purchased, time_spent = self.simulate_user_behavior(
                groups[i], devices[i], new_users[i]
            )
            
            data.append({
                'user_id': user_ids[i],
                'group': groups[i],
                'device': devices[i],
                'region': regions[i],
                'new_user': new_users[i],
                'viewed': int(viewed),
                'clicked': int(clicked),
                'purchased': int(purchased),
                'time_spent': round(time_spent, 2),
                'timestamp': datetime.now() - timedelta(
                    days=random.randint(0, 13),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            })
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} user records")
        return df
    
    def generate_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the dataset"""
        stats = {}
        
        for group in ['A', 'B']:
            group_data = df[df['group'] == group]
            stats[group] = {
                'total_users': len(group_data),
                'view_rate': group_data['viewed'].mean(),
                'ctr': group_data['clicked'].mean() / group_data['viewed'].mean() if group_data['viewed'].mean() > 0 else 0,
                'conversion_rate': group_data['purchased'].mean(),
                'avg_time_spent': group_data[group_data['viewed'] == 1]['time_spent'].mean(),
                'total_purchases': group_data['purchased'].sum()
            }
        
        # Calculate lifts
        stats['lifts'] = {
            'view_rate_lift': (stats['B']['view_rate'] / stats['A']['view_rate'] - 1) * 100,
            'ctr_lift': (stats['B']['ctr'] / stats['A']['ctr'] - 1) * 100,
            'conversion_lift': (stats['B']['conversion_rate'] / stats['A']['conversion_rate'] - 1) * 100,
            'time_spent_lift': (stats['B']['avg_time_spent'] / stats['A']['avg_time_spent'] - 1) * 100
        }
        
        return stats

def main():
    """Main function to generate and save data"""
    generator = ABTestDataGenerator(seed=42)
    
    # Generate dataset
    df = generator.generate_dataset()
    
    # Generate summary statistics
    stats = generator.generate_summary_stats(df)
    
    # Save data
    df.to_csv('ab_test_data.csv', index=False)
    
    # Save summary statistics
    with open('summary_stats.json', 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    print("\nDataset saved as 'ab_test_data.csv'")
    print("Summary statistics saved as 'summary_stats.json'")
    
    # Print summary
    print("\n=== EXPERIMENT SUMMARY ===")
    print(f"Control Group (A): {stats['A']['total_users']:,} users")
    print(f"Treatment Group (B): {stats['B']['total_users']:,} users")
    print(f"\nConversion Rate:")
    print(f"  Control: {stats['A']['conversion_rate']:.3%}")
    print(f"  Treatment: {stats['B']['conversion_rate']:.3%}")
    print(f"  Lift: {stats['lifts']['conversion_lift']:.2f}%")
    
    print(f"\nClick-Through Rate:")
    print(f"  Control: {stats['A']['ctr']:.3%}")
    print(f"  Treatment: {stats['B']['ctr']:.3%}")
    print(f"  Lift: {stats['lifts']['ctr_lift']:.2f}%")

if __name__ == "__main__":
    main()
