import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta

class ABTestCleaner:
    """
    Data cleaning and preprocessing for A/B testing data
    """
    
    def __init__(self, log_level: str = 'INFO'):
        logging.basicConfig(level=getattr(logging, log_level))
        self.logger = logging.getLogger(__name__)
        
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load and validate raw data"""
        try:
            df = pd.read_csv(filepath)
            self.logger.info(f"Loaded {len(df)} records from {filepath}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validate data schema and required columns"""
        required_columns = [
            'user_id', 'group', 'device', 'region', 'new_user',
            'viewed', 'clicked', 'purchased', 'time_spent', 'timestamp'
        ]
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return False
        
        # Check data types
        expected_types = {
            'user_id': 'object',
            'group': 'object',
            'device': 'object',
            'region': 'object',
            'new_user': 'bool',
            'viewed': 'int64',
            'clicked': 'int64',
            'purchased': 'int64',
            'time_spent': 'float64',
            'timestamp': 'object'
        }
        
        for col, expected_type in expected_types.items():
            if col in df.columns and str(df[col].dtype) != expected_type:
                self.logger.warning(f"Column {col} has type {df[col].dtype}, expected {expected_type}")
        
        self.logger.info("Schema validation passed")
        return True
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate user records"""
        initial_count = len(df)
        
        # Check for duplicate user_ids
        duplicate_users = df[df.duplicated(subset=['user_id'], keep=False)]
        if len(duplicate_users) > 0:
            self.logger.warning(f"Found {len(duplicate_users)} duplicate user records")
            
            # Keep the most recent record for each user
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').drop_duplicates(subset=['user_id'], keep='last')
        
        final_count = len(df)
        self.logger.info(f"Removed {initial_count - final_count} duplicate records")
        return df
    
    def validate_group_assignment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean group assignments"""
        # Check for invalid group values
        valid_groups = ['A', 'B']
        invalid_groups = df[~df['group'].isin(valid_groups)]
        
        if len(invalid_groups) > 0:
            self.logger.warning(f"Found {len(invalid_groups)} records with invalid group values")
            df = df[df['group'].isin(valid_groups)]
        
        # Check group balance
        group_counts = df['group'].value_counts()
        balance_ratio = min(group_counts) / max(group_counts)
        
        if balance_ratio < 0.4:  # More than 60/40 split
            self.logger.warning(f"Unbalanced groups: {group_counts.to_dict()}")
        
        self.logger.info(f"Group distribution: {group_counts.to_dict()}")
        return df
    
    def clean_device_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize device data"""
        # Standardize device names
        device_mapping = {
            'Mobile': 'mobile',
            'mobile ': 'mobile',
            'Desktop': 'desktop',
            'desktop ': 'desktop',
            'Tablet': 'tablet',
            'tablet ': 'tablet'
        }
        
        df['device'] = df['device'].str.lower().str.strip()
        
        # Handle unknown devices
        valid_devices = ['mobile', 'desktop', 'tablet']
        unknown_devices = df[~df['device'].isin(valid_devices)]
        
        if len(unknown_devices) > 0:
            self.logger.warning(f"Found {len(unknown_devices)} records with unknown devices")
            # Assign unknown devices to 'mobile' as default
            df.loc[~df['device'].isin(valid_devices), 'device'] = 'mobile'
        
        return df
    
    def validate_behavior_sequence(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate logical sequence of user behavior"""
        initial_count = len(df)
        
        # Ensure logical sequence: viewed >= clicked >= purchased
        # Clicked should only be 1 if viewed is 1
        invalid_clicks = df[(df['clicked'] == 1) & (df['viewed'] == 0)]
        if len(invalid_clicks) > 0:
            self.logger.warning(f"Found {len(invalid_clicks)} records with clicks but no views")
            df.loc[(df['clicked'] == 1) & (df['viewed'] == 0), 'clicked'] = 0
        
        # Purchased should only be 1 if clicked is 1
        invalid_purchases = df[(df['purchased'] == 1) & (df['clicked'] == 0)]
        if len(invalid_purchases) > 0:
            self.logger.warning(f"Found {len(invalid_purchases)} records with purchases but no clicks")
            df.loc[(df['purchased'] == 1) & (df['clicked'] == 0), 'purchased'] = 0
        
        final_count = len(df)
        self.logger.info(f"Behavior sequence validation: {initial_count} -> {final_count} records")
        return df
    
    def clean_time_spent(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate time_spent data"""
        # Time spent should be 0 if not viewed
        df.loc[df['viewed'] == 0, 'time_spent'] = 0
        
        # Remove outliers (more than 3 standard deviations from mean)
        viewed_data = df[df['viewed'] == 1]['time_spent']
        if len(viewed_data) > 0:
            mean_time = viewed_data.mean()
            std_time = viewed_data.std()
            
            # Cap extreme values
            upper_bound = mean_time + 3 * std_time
            lower_bound = max(0, mean_time - 3 * std_time)
            
            outliers = df[(df['viewed'] == 1) & 
                         ((df['time_spent'] > upper_bound) | (df['time_spent'] < lower_bound))]
            
            if len(outliers) > 0:
                self.logger.warning(f"Found {len(outliers)} time_spent outliers")
                # Cap outliers at bounds
                df.loc[df['time_spent'] > upper_bound, 'time_spent'] = upper_bound
                df.loc[df['time_spent'] < lower_bound, 'time_spent'] = lower_bound
        
        return df
    
    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for analysis"""
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Add time-based features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Add engagement level based on time spent
        def categorize_engagement(time_spent, viewed):
            if viewed == 0:
                return 'no_engagement'
            elif time_spent < 30:
                return 'low'
            elif time_spent < 120:
                return 'medium'
            else:
                return 'high'
        
        df['engagement_level'] = df.apply(
            lambda row: categorize_engagement(row['time_spent'], row['viewed']), 
            axis=1
        )
        
        # Add conversion funnel stage
        def get_funnel_stage(viewed, clicked, purchased):
            if purchased == 1:
                return 'purchase'
            elif clicked == 1:
                return 'click'
            elif viewed == 1:
                return 'view'
            else:
                return 'no_view'
        
        df['funnel_stage'] = df.apply(
            lambda row: get_funnel_stage(row['viewed'], row['clicked'], row['purchased']), 
            axis=1
        )
        
        self.logger.info("Added derived features")
        return df
    
    def remove_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """Remove outliers using specified method"""
        if method == 'iqr':
            # Remove outliers based on IQR for time_spent
            viewed_data = df[df['viewed'] == 1]['time_spent']
            if len(viewed_data) > 0:
                Q1 = viewed_data.quantile(0.25)
                Q3 = viewed_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (df['viewed'] == 1) & \
                              ((df['time_spent'] < lower_bound) | (df['time_spent'] > upper_bound))
                
                outliers_count = outlier_mask.sum()
                if outliers_count > 0:
                    self.logger.info(f"Removed {outliers_count} outliers using IQR method")
                    df = df[~outlier_mask]
        
        return df
    
    def generate_data_quality_report(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive data quality report"""
        report = {
            'total_records': len(df),
            'missing_values': df.isnull().sum().to_dict(),
            'data_types': df.dtypes.to_dict(),
            'group_distribution': df['group'].value_counts().to_dict(),
            'device_distribution': df['device'].value_counts().to_dict(),
            'behavior_summary': {
                'viewed_users': df['viewed'].sum(),
                'clicked_users': df['clicked'].sum(),
                'purchased_users': df['purchased'].sum(),
                'view_rate': df['viewed'].mean(),
                'ctr': df['clicked'].mean() / df['viewed'].mean() if df['viewed'].mean() > 0 else 0,
                'conversion_rate': df['purchased'].mean()
            }
        }
        
        return report
    
    def clean_data(self, filepath: str, save_cleaned: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """Complete data cleaning pipeline"""
        self.logger.info("Starting data cleaning pipeline")
        
        # Load and validate
        df = self.load_data(filepath)
        if not self.validate_schema(df):
            raise ValueError("Data schema validation failed")
        
        # Apply cleaning steps
        df = self.remove_duplicates(df)
        df = self.validate_group_assignment(df)
        df = self.clean_device_data(df)
        df = self.validate_behavior_sequence(df)
        df = self.clean_time_spent(df)
        df = self.remove_outliers(df)
        df = self.add_derived_features(df)
        
        # Generate quality report
        quality_report = self.generate_data_quality_report(df)
        
        # Save cleaned data
        if save_cleaned:
            cleaned_filepath = filepath.replace('.csv', '_cleaned.csv')
            df.to_csv(cleaned_filepath, index=False)
            self.logger.info(f"Cleaned data saved to {cleaned_filepath}")
        
        self.logger.info("Data cleaning pipeline completed")
        return df, quality_report

def main():
    """Example usage of the data cleaner"""
    cleaner = ABTestCleaner()
    
    try:
        # Clean the data
        df, report = cleaner.clean_data('ab_test_data.csv')
        
        # Print summary
        print("\n=== DATA CLEANING SUMMARY ===")
        print(f"Total records after cleaning: {report['total_records']:,}")
        print(f"View rate: {report['behavior_summary']['view_rate']:.3%}")
        print(f"CTR: {report['behavior_summary']['ctr']:.3%}")
        print(f"Conversion rate: {report['behavior_summary']['conversion_rate']:.3%}")
        
        print("\nGroup distribution:")
        for group, count in report['group_distribution'].items():
            print(f"  Group {group}: {count:,} users")
            
    except Exception as e:
        print(f"Error in data cleaning: {e}")

if __name__ == "__main__":
    main()
