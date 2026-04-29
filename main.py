#!/usr/bin/env python3
"""
Main execution script for A/B Testing Experimentation Platform
This script runs the complete pipeline from data generation to decision making
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from src.data_simulation import ABTestDataGenerator
from src.data_cleaning import ABTestCleaner
from src.statistical_testing import ABTestStatisticalAnalyzer
from src.decision_engine import ABTestDecisionEngine, ExperimentResult
import pandas as pd
import json
from datetime import datetime

def run_complete_pipeline():
    """Run the complete A/B testing pipeline"""
    print("=" * 80)
    print("A/B TESTING EXPERIMENTATION PLATFORM")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Generate synthetic data
    print("🚀 STEP 1: Generating Synthetic Data")
    print("-" * 40)
    generator = ABTestDataGenerator(seed=42)
    df = generator.generate_dataset()
    stats = generator.generate_summary_stats(df)
    
    # Save raw data and summary
    df.to_csv('ab_test_data.csv', index=False)
    with open('summary_stats.json', 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    print(f"✅ Generated {len(df):,} user records")
    print(f"✅ Control Group: {stats['A']['total_users']:,} users")
    print(f"✅ Treatment Group: {stats['B']['total_users']:,} users")
    print()
    
    # Step 2: Clean and validate data
    print("🧹 STEP 2: Data Cleaning & Validation")
    print("-" * 40)
    cleaner = ABTestCleaner()
    cleaned_df, quality_report = cleaner.clean_data('ab_test_data.csv')
    
    print(f"✅ Cleaned {len(cleaned_df):,} records")
    print(f"✅ Data quality score: {quality_report.get('quality_score', 'N/A')}")
    print(f"✅ Missing values handled: {sum(quality_report.get('missing_values', {}).values())}")
    print()
    
    # Step 3: Statistical analysis
    print("📊 STEP 3: Statistical Analysis")
    print("-" * 40)
    analyzer = ABTestStatisticalAnalyzer()
    results = analyzer.run_full_analysis(cleaned_df)
    
    # Generate and print report
    report = analyzer.generate_report(results)
    print(report)
    
    # Create visualizations
    try:
        analyzer.visualize_results(results, 'ab_test_results.png')
        print("✅ Visualizations saved to 'ab_test_results.png'")
    except Exception as e:
        print(f"⚠️  Visualization error: {e}")
    
    print()
    
    # Step 4: Decision making
    print("🤖 STEP 4: Automated Decision Making")
    print("-" * 40)
    engine = ABTestDecisionEngine()
    
    # Prepare guardrail results
    guardrail_results = []
    if 'ctr' in results:
        guardrail_results.append(results['ctr'])
    if 'view_rate' in results:
        guardrail_results.append(results['view_rate'])
    
    # Make decision
    recommendation = engine.make_decision(
        primary_result=results['conversion'],
        guardrail_results=guardrail_results,
        segment_results=results.get('device_segments', {})
    )
    
    # Print decision report
    decision_report = engine.generate_decision_report(recommendation)
    print(decision_report)
    
    # Save decision history
    engine.save_decision_history('decision_history.json')
    print("✅ Decision history saved to 'decision_history.json'")
    print()
    
    # Step 5: Summary
    print("📋 EXECUTION SUMMARY")
    print("-" * 40)
    print("Files Generated:")
    print("  📄 ab_test_data.csv - Raw experiment data")
    print("  📄 ab_test_data_cleaned.csv - Cleaned data")
    print("  📄 summary_stats.json - Data summary statistics")
    print("  📄 decision_history.json - Decision records")
    print("  📄 ab_test_results.png - Result visualizations")
    print()
    print("Key Results:")
    print(f"  🎯 Conversion Rate Lift: {results['conversion'].relative_difference:.2f}%")
    print(f"  📈 Statistical Significance: {'Yes' if results['conversion'].is_significant else 'No'}")
    print(f"  🤖 Final Decision: {recommendation['decision']}")
    print(f"  📊 Confidence: {recommendation['confidence']:.1%}")
    print()
    print("=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return results, recommendation

def run_individual_components():
    """Run individual components for testing"""
    print("🔧 Running Individual Components")
    print("=" * 50)
    
    # Test data generation
    print("\n1. Testing Data Generation...")
    generator = ABTestDataGenerator(seed=42)
    df = generator.generate_dataset()
    print(f"   Generated {len(df)} records")
    
    # Test data cleaning
    print("\n2. Testing Data Cleaning...")
    cleaner = ABTestCleaner()
    cleaned_df, quality_report = cleaner.clean_data('ab_test_data.csv')
    print(f"   Cleaned {len(cleaned_df)} records")
    
    # Test statistical analysis
    print("\n3. Testing Statistical Analysis...")
    analyzer = ABTestStatisticalAnalyzer()
    results = analyzer.run_full_analysis(cleaned_df)
    print(f"   Analyzed {len(results)} metrics")
    
    # Test decision engine
    print("\n4. Testing Decision Engine...")
    engine = ABTestDecisionEngine()
    guardrail_results = [results['ctr']] if 'ctr' in results else []
    recommendation = engine.make_decision(
        primary_result=results['conversion'],
        guardrail_results=guardrail_results,
        segment_results=results.get('device_segments', {})
    )
    print(f"   Decision: {recommendation['decision']}")
    
    print("\n✅ All components tested successfully!")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_individual_components()
    else:
        run_complete_pipeline()

if __name__ == "__main__":
    main()
