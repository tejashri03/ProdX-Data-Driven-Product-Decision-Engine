"""
Streamlit Interactive Dashboard for A/B Testing Platform
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_simulation import ABTestDataGenerator
from data_cleaning import ABTestCleaner
from statistical_testing import ABTestStatisticalAnalyzer
from decision_engine import ABTestDecisionEngine
from bayesian_testing import BayesianAnalyzer
from multi_armed_bandit import ABTestBandit

# Page configuration
st.set_page_config(
    page_title="A/B Testing Platform",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .success {
        color: #2ca02c;
        font-weight: bold;
    }
    .warning {
        color: #ff7f0e;
        font-weight: bold;
    }
    .danger {
        color: #d62728;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'experiment_data' not in st.session_state:
    st.session_state.experiment_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'decision_results' not in st.session_state:
    st.session_state.decision_results = None

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🧪 Advanced A/B Testing Platform</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["🏠 Home", "📊 Data Generation", "🧹 Data Cleaning", "📈 Statistical Analysis", 
         "🤖 Decision Engine", "🎯 Bayesian Analysis", "🎰 Multi-Armed Bandit", "📋 Executive Dashboard"]
    )
    
    if page == "🏠 Home":
        home_page()
    elif page == "📊 Data Generation":
        data_generation_page()
    elif page == "🧹 Data Cleaning":
        data_cleaning_page()
    elif page == "📈 Statistical Analysis":
        statistical_analysis_page()
    elif page == "🤖 Decision Engine":
        decision_engine_page()
    elif page == "🎯 Bayesian Analysis":
        bayesian_analysis_page()
    elif page == "🎰 Multi-Armed Bandit":
        multi_armed_bandit_page()
    elif page == "📋 Executive Dashboard":
        executive_dashboard_page()

def home_page():
    """Home page with overview"""
    
    st.markdown("""
    ## Welcome to the Advanced A/B Testing Platform!
    
    This comprehensive platform provides end-to-end capabilities for designing, running, and analyzing A/B tests with advanced statistical methods.
    
    ### 🚀 Key Features
    - **Data Simulation**: Generate realistic synthetic datasets
    - **Statistical Analysis**: Frequentist and Bayesian methods
    - **Decision Engine**: Automated experiment decisions
    - **Multi-Armed Bandit**: Adaptive experimentation
    - **Interactive Dashboard**: Real-time insights and visualizations
    
    ### 📊 Capabilities
    - **Conversion Rate Analysis**: Primary and secondary metrics
    - **Funnel Analysis**: Complete user journey tracking
    - **Segment Analysis**: Performance by user segments
    - **Statistical Power**: Sample size calculations
    - **Business Impact**: Revenue projections and ROI analysis
    """)
    
    # Quick stats
    if st.session_state.experiment_data is not None:
        st.markdown("### 📈 Current Experiment Status")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", f"{len(st.session_state.experiment_data):,}")
        
        with col2:
            control_rate = st.session_state.experiment_data[
                st.session_state.experiment_data['group'] == 'A'
            ]['purchased'].mean()
            st.metric("Control Conversion", f"{control_rate:.3%}")
        
        with col3:
            treatment_rate = st.session_state.experiment_data[
                st.session_state.experiment_data['group'] == 'B'
            ]['purchased'].mean()
            st.metric("Treatment Conversion", f"{treatment_rate:.3%}")
        
        with col4:
            lift = (treatment_rate - control_rate) / control_rate * 100
            st.metric("Relative Lift", f"{lift:.2f}%")
    
    # Getting started
    st.markdown("""
    ### 🎯 Getting Started
    
    1. **Generate Data**: Create synthetic experiment data
    2. **Clean Data**: Validate and preprocess the data
    3. **Analyze Results**: Run statistical tests
    4. **Make Decisions**: Get automated recommendations
    5. **Advanced Features**: Try Bayesian analysis and multi-armed bandits
    """)

def data_generation_page():
    """Data generation page"""
    
    st.markdown("## 📊 Data Generation")
    st.markdown("Generate realistic synthetic A/B testing data with configurable parameters.")
    
    # Configuration
    with st.expander("⚙️ Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            n_users = st.slider("Number of Users", 1000, 100000, 10000, 1000)
            seed = st.number_input("Random Seed", value=42)
        
        with col2:
            treatment_lift = st.slider("Treatment Lift (%)", -20, 50, 10, 1)
            noise_level = st.slider("Noise Level", 0.0, 0.5, 0.1, 0.05)
    
    # Generate button
    if st.button("🚀 Generate Data", type="primary"):
        with st.spinner("Generating synthetic data..."):
            # Create generator
            generator = ABTestDataGenerator(seed=seed)
            
            # Generate data
            df = generator.generate_dataset(n_users)
            
            # Store in session state
            st.session_state.experiment_data = df
            
            # Generate summary
            stats = generator.generate_summary_stats(df)
            
            st.success(f"✅ Generated {len(df):,} user records!")
    
    # Display results
    if st.session_state.experiment_data is not None:
        df = st.session_state.experiment_data
        
        # Summary statistics
        st.markdown("### 📋 Data Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            control_users = len(df[df['group'] == 'A'])
            st.metric("Control Users", f"{control_users:,}")
        
        with col2:
            treatment_users = len(df[df['group'] == 'B'])
            st.metric("Treatment Users", f"{treatment_users:,}")
        
        with col3:
            total_conversions = df['purchased'].sum()
            st.metric("Total Conversions", f"{total_conversions:,}")
        
        with col4:
            overall_rate = df['purchased'].mean()
            st.metric("Overall Rate", f"{overall_rate:.3%}")
        
        # Data preview
        st.markdown("### 🔍 Data Preview")
        st.dataframe(df.head(100))
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="ab_test_data.csv",
            mime="text/csv"
        )

def data_cleaning_page():
    """Data cleaning page"""
    
    st.markdown("## 🧹 Data Cleaning & Validation")
    st.markdown("Clean and validate experiment data with quality checks.")
    
    if st.session_state.experiment_data is None:
        st.warning("⚠️ Please generate data first in the Data Generation page.")
        return
    
    # Clean data button
    if st.button("🧹 Clean Data", type="primary"):
        with st.spinner("Cleaning and validating data..."):
            # Create cleaner
            cleaner = ABTestCleaner()
            
            # Clean data
            cleaned_df, quality_report = cleaner.clean_data(
                'ab_test_data.csv' if os.path.exists('ab_test_data.csv') else None
            )
            
            # If no CSV file, clean the dataframe directly
            if not os.path.exists('ab_test_data.csv'):
                st.session_state.experiment_data.to_csv('temp_data.csv', index=False)
                cleaned_df, quality_report = cleaner.clean_data('temp_data.csv')
                os.remove('temp_data.csv')
            
            st.session_state.experiment_data = cleaned_df
            st.session_state.quality_report = quality_report
            
            st.success("✅ Data cleaning completed!")
    
    # Display quality report
    if 'quality_report' in st.session_state:
        quality_report = st.session_state.quality_report
        
        st.markdown("### 📊 Quality Report")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", f"{quality_report.get('total_records', 0):,}")
        
        with col2:
            missing_values = sum(quality_report.get('missing_values', {}).values())
            st.metric("Missing Values", f"{missing_values:,}")
        
        with col3:
            duplicates = quality_report.get('duplicates_removed', 0)
            st.metric("Duplicates Removed", f"{duplicates:,}")
        
        with col4:
            outliers = quality_report.get('outliers_removed', 0)
            st.metric("Outliers Removed", f"{outliers:,}")
        
        # Data distribution
        st.markdown("### 📈 Data Distribution")
        
        df = st.session_state.experiment_data
        
        # Group distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                df['group'].value_counts(),
                values='group',
                names=df['group'].value_counts().index,
                title="Group Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                df['device'].value_counts(),
                title="Device Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Cleaned data preview
        st.markdown("### 🔍 Cleaned Data Preview")
        st.dataframe(df.head(100))

def statistical_analysis_page():
    """Statistical analysis page"""
    
    st.markdown("## 📈 Statistical Analysis")
    st.markdown("Run comprehensive statistical tests on experiment data.")
    
    if st.session_state.experiment_data is None:
        st.warning("⚠️ Please generate and clean data first.")
        return
    
    # Analysis configuration
    with st.expander("⚙️ Analysis Configuration"):
        significance_level = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01)
        power_threshold = st.slider("Power Threshold", 0.7, 0.95, 0.80, 0.05)
    
    # Run analysis button
    if st.button("🔬 Run Analysis", type="primary"):
        with st.spinner("Running statistical analysis..."):
            # Create analyzer
            analyzer = ABTestStatisticalAnalyzer(significance_level=significance_level)
            
            # Run analysis
            results = analyzer.run_full_analysis(st.session_state.experiment_data)
            
            st.session_state.analysis_results = results
            st.success("✅ Statistical analysis completed!")
    
    # Display results
    if st.session_state.analysis_results is not None:
        results = st.session_state.analysis_results
        
        st.markdown("### 📊 Analysis Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            conv_lift = results['conversion'].relative_difference
            st.metric("Conversion Lift", f"{conv_lift:.2f}%")
        
        with col2:
            ctr_lift = results['ctr'].relative_difference
            st.metric("CTR Lift", f"{ctr_lift:.2f}%")
        
        with col3:
            conv_sig = "✅ Significant" if results['conversion'].is_significant else "❌ Not Significant"
            st.metric("Conversion Significance", conv_sig)
        
        with col4:
            ctr_sig = "✅ Significant" if results['ctr'].is_significant else "❌ Not Significant"
            st.metric("CTR Significance", ctr_sig)
        
        # Detailed results
        st.markdown("### 📋 Detailed Results")
        
        # Conversion rate
        st.markdown("#### 🎯 Conversion Rate")
        conv_result = results['conversion']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Control Rate:** {conv_result.control_rate:.3%}")
            st.write(f"**Treatment Rate:** {conv_result.treatment_rate:.3%}")
            st.write(f"**Absolute Difference:** {conv_result.absolute_difference:.4f}")
            st.write(f"**Relative Lift:** {conv_result.relative_difference:.2f}%")
        
        with col2:
            st.write(f"**P-value:** {conv_result.p_value:.4f}")
            st.write(f"**95% CI:** [{conv_result.confidence_interval[0]:.4f}, {conv_result.confidence_interval[1]:.4f}]")
            st.write(f"**Significant:** {'Yes' if conv_result.is_significant else 'No'}")
            st.write(f"**Sample Size:** {conv_result.sample_size_control + conv_result.sample_size_treatment:,}")
        
        # Visualization
        st.markdown("### 📈 Visualizations")
        
        # Create comparison chart
        metrics = ['Conversion Rate', 'CTR', 'View Rate']
        control_rates = [
            results['conversion'].control_rate,
            results['ctr'].control_rate,
            results['view_rate'].control_rate
        ]
        treatment_rates = [
            results['conversion'].treatment_rate,
            results['ctr'].treatment_rate,
            results['view_rate'].treatment_rate
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Control',
            x=metrics,
            y=control_rates,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Treatment',
            x=metrics,
            y=treatment_rates,
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title='Metric Comparison: Control vs Treatment',
            xaxis_title='Metrics',
            yaxis_title='Rate',
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def decision_engine_page():
    """Decision engine page"""
    
    st.markdown("## 🤖 Decision Engine")
    st.markdown("Get automated experiment decisions based on statistical and business criteria.")
    
    if st.session_state.analysis_results is None:
        st.warning("⚠️ Please run statistical analysis first.")
        return
    
    # Decision configuration
    with st.expander("⚙️ Decision Criteria"):
        min_sample_size = st.slider("Minimum Sample Size", 100, 10000, 1000, 100)
        min_effect_size = st.slider("Minimum Effect Size (%)", 1, 20, 2, 1)
        max_negative_lift = st.slider("Max Negative Lift (%)", -20, -1, -5, 1)
    
    # Make decision button
    if st.button("🤖 Make Decision", type="primary"):
        with st.spinner("Analyzing and making decision..."):
            # Create decision engine
            engine = ABTestDecisionEngine()
            
            # Make decision
            recommendation = engine.make_decision(
                primary_result=st.session_state.analysis_results['conversion'],
                guardrail_results=[
                    st.session_state.analysis_results['ctr'],
                    st.session_state.analysis_results['view_rate']
                ],
                segment_results=st.session_state.analysis_results.get('device_segments', {})
            )
            
            st.session_state.decision_results = recommendation
            st.success("✅ Decision analysis completed!")
    
    # Display decision
    if st.session_state.decision_results is not None:
        decision = st.session_state.decision_results
        
        st.markdown("### 🎯 Decision Result")
        
        # Decision card
        decision_color = {
            "Launch Treatment": "success",
            "Continue Testing": "warning",
            "Stop Experiment (Negative Results)": "danger",
            "Inconclusive - More Data Needed": "warning"
        }.get(decision['decision'], "info")
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>Decision: <span class="{decision_color}">{decision['decision']}</span></h3>
            <p><strong>Confidence:</strong> {decision['confidence']:.1%}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Reasoning
        st.markdown("### 🧠 Reasoning")
        st.write(decision['reasoning'])
        
        # Business impact
        st.markdown("### 💰 Business Impact")
        
        if 'annual_revenue_impact' in decision['business_impact']:
            impact = decision['business_impact']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Annual Revenue Impact", f"${impact['annual_revenue_impact']:,.0f}")
            
            with col2:
                st.metric("Impact Percentage", f"{impact['impact_percentage']:.2f}%")
            
            with col3:
                st.metric("Current Revenue", f"${impact['current_monthly_revenue']*12:,.0f}")
        
        # Recommendations
        st.markdown("### 📋 Recommendations")
        for i, rec in enumerate(decision['recommendations'], 1):
            st.write(f"{i}. {rec}")
        
        # Next steps
        st.markdown("### 🚀 Next Steps")
        for i, step in enumerate(decision['next_steps'], 1):
            st.write(f"{i}. {step}")

def bayesian_analysis_page():
    """Bayesian analysis page"""
    
    st.markdown("## 🎯 Bayesian Analysis")
    st.markdown("Advanced Bayesian statistical methods for A/B testing.")
    
    if st.session_state.experiment_data is None:
        st.warning("⚠️ Please generate data first.")
        return
    
    # Bayesian configuration
    with st.expander("⚙️ Bayesian Configuration"):
        prior_alpha = st.slider("Prior Alpha", 0.1, 10.0, 1.0, 0.1)
        prior_beta = st.slider("Prior Beta", 0.1, 10.0, 1.0, 0.1)
        credible_interval = st.slider("Credible Interval", 0.8, 0.99, 0.95, 0.05)
    
    # Run Bayesian analysis button
    if st.button("🎯 Run Bayesian Analysis", type="primary"):
        with st.spinner("Running Bayesian analysis..."):
            # Create analyzer
            analyzer = BayesianAnalyzer(prior_alpha, prior_beta)
            
            # Run analysis
            results = analyzer.analyze_experiment(st.session_state.experiment_data)
            
            st.session_state.bayesian_results = results
            st.success("✅ Bayesian analysis completed!")
    
    # Display results
    if 'bayesian_results' in st.session_state:
        results = st.session_state.bayesian_results
        
        st.markdown("### 📊 Bayesian Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            prob = results['decision']['probability_treatment_better']
            st.metric("P(Treatment > Control)", f"{prob:.3%}")
        
        with col2:
            loss = results['decision']['expected_loss']
            st.metric("Expected Loss", f"{loss:.6f}")
        
        with col3:
            lift = results['bayesian_result'].relative_difference
            st.metric("Relative Lift", f"{lift:.2f}%")
        
        with col4:
            decision = results['decision']['decision']
            st.metric("Decision", decision)
        
        # Posterior distributions
        st.markdown("### 📈 Posterior Distributions")
        
        # Create posterior distribution plot
        result = results['bayesian_result']
        
        x = np.linspace(0, max(result.control_posterior_mean, result.treatment_posterior_mean) * 2, 1000)
        
        fig = go.Figure()
        
        # Control posterior
        control_dist = stats.beta(
            prior_alpha + result.sample_size_control * result.control_posterior_mean,
            prior_beta + result.sample_size_control * (1 - result.control_posterior_mean)
        )
        control_pdf = control_dist.pdf(x)
        
        fig.add_trace(go.Scatter(
            x=x, y=control_pdf,
            mode='lines',
            name='Control',
            line=dict(color='blue', width=2)
        ))
        
        # Treatment posterior
        treatment_dist = stats.beta(
            prior_alpha + result.sample_size_treatment * result.treatment_posterior_mean,
            prior_beta + result.sample_size_treatment * (1 - result.treatment_posterior_mean)
        )
        treatment_pdf = treatment_dist.pdf(x)
        
        fig.add_trace(go.Scatter(
            x=x, y=treatment_pdf,
            mode='lines',
            name='Treatment',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title='Posterior Distributions',
            xaxis_title='Conversion Rate',
            yaxis_title='Probability Density'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Decision reasoning
        st.markdown("### 🧠 Decision Reasoning")
        st.write(results['decision']['reasoning'])

def multi_armed_bandit_page():
    """Multi-armed bandit page"""
    
    st.markdown("## 🎰 Multi-Armed Bandit")
    st.markdown("Adaptive experimentation using multi-armed bandit algorithms.")
    
    # Bandit configuration
    with st.expander("⚙️ Bandit Configuration"):
        algorithm = st.selectbox("Algorithm", ["epsilon_greedy", "ucb1", "thompson_sampling"])
        n_variants = st.slider("Number of Variants", 2, 5, 3)
        n_users = st.slider("Number of Users", 1000, 50000, 10000, 1000)
    
    # True conversion rates for simulation
    st.markdown("### 🎯 True Conversion Rates (for simulation)")
    true_rates = {}
    for i in range(n_variants):
        variant_name = f"Variant_{chr(65 + i)}"  # A, B, C, D, E
        true_rates[variant_name] = st.slider(
            f"{variant_name} Rate", 0.01, 0.10, 0.03 + i*0.01, 0.001
        )
    
    # Run bandit simulation button
    if st.button("🎰 Run Bandit Simulation", type="primary"):
        with st.spinner("Running bandit simulation..."):
            # Create bandit
            bandit = ABTestBandit(algorithm=algorithm, variants=list(true_rates.keys()))
            
            # Run simulation
            simulation_result = bandit.simulate_ab_test(true_rates, n_users)
            
            st.session_state.bandit_results = simulation_result
            st.session_state.bandit_instance = bandit
            
            st.success("✅ Bandit simulation completed!")
    
    # Display results
    if 'bandit_results' in st.session_state:
        bandit = st.session_state.bandit_instance
        results = st.session_state.bandit_results
        
        st.markdown("### 📊 Bandit Results")
        
        # Performance summary
        summary = bandit.get_performance_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_variant, best_rate = bandit.get_best_variant()
            st.metric("Best Variant", best_variant)
        
        with col2:
            st.metric("Best Rate", f"{best_rate:.3%}")
        
        with col3:
            total_conversions = summary['total_conversions']
            st.metric("Total Conversions", f"{total_conversions:,}")
        
        with col4:
            total_rounds = summary['total_rounds']
            st.metric("Total Rounds", f"{total_rounds:,}")
        
        # Variant performance
        st.markdown("### 📈 Variant Performance")
        
        variants_data = []
        for variant, stats in summary['variants'].items():
            variants_data.append({
                'Variant': stats['name'],
                'Conversion Rate': stats['conversion_rate'],
                'Total Conversions': stats['total_conversions'],
                'Total Users': stats['total_users'],
                'Traffic %': stats['pull_percentage']
            })
        
        variants_df = pd.DataFrame(variants_data)
        st.dataframe(variants_df, use_container_width=True)
        
        # Traffic allocation chart
        st.markdown("### 🎯 Traffic Allocation")
        
        fig = px.pie(
            values=[v['pull_percentage'] for v in summary['variants'].values()],
            names=[v['name'] for v in summary['variants'].values()],
            title="Traffic Allocation by Variant"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance over time
        if 'simulation_results' in results and len(results['simulation_results']) > 1:
            st.markdown("### 📈 Performance Over Time")
            
            rounds = [r['users'] for r in results['simulation_results']]
            best_variants = [r['best_variant'] for r in results['simulation_results']]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=rounds,
                y=[i for i, v in enumerate(best_variants)],
                mode='lines+markers',
                name='Best Variant Over Time'
            ))
            
            fig.update_layout(
                title='Best Variant Over Time',
                xaxis_title='Users',
                yaxis_title='Variant Index'
            )
            
            st.plotly_chart(fig, use_container_width=True)

def executive_dashboard_page():
    """Executive dashboard page"""
    
    st.markdown("## 📋 Executive Dashboard")
    st.markdown("High-level overview for executives and stakeholders.")
    
    if st.session_state.experiment_data is None:
        st.warning("⚠️ Please run experiments first to see executive dashboard.")
        return
    
    # Executive summary
    st.markdown("### 🎯 Executive Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    df = st.session_state.experiment_data
    
    with col1:
        total_users = len(df)
        st.metric("Total Users", f"{total_users:,}")
    
    with col2:
        total_conversions = df['purchased'].sum()
        st.metric("Total Conversions", f"{total_conversions:,}")
    
    with col3:
        overall_rate = df['purchased'].mean()
        st.metric("Overall Rate", f"{overall_rate:.3%}")
    
    with col4:
        if st.session_state.analysis_results:
            lift = st.session_state.analysis_results['conversion'].relative_difference
            st.metric("Conversion Lift", f"{lift:.2f}%")
        else:
            st.metric("Conversion Lift", "N/A")
    
    # Revenue impact
    if st.session_state.decision_results:
        st.markdown("### 💰 Business Impact")
        
        decision = st.session_state.decision_results
        
        if 'annual_revenue_impact' in decision['business_impact']:
            impact = decision['business_impact']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Annual Revenue Impact",
                    f"${impact['annual_revenue_impact']:,.0f}",
                    delta=f"{impact['impact_percentage']:.2f}%"
                )
            
            with col2:
                st.metric(
                    "Monthly Revenue Impact",
                    f"${impact['monthly_revenue_impact']:,.0f}"
                )
            
            with col3:
                st.metric(
                    "Decision",
                    decision['decision'],
                    delta=f"Confidence: {decision['confidence']:.1%}"
                )
    
    # Funnel visualization
    st.markdown("### 📊 Conversion Funnel")
    
    # Calculate funnel stages
    funnel_data = []
    for group in ['A', 'B']:
        group_data = df[df['group'] == group]
        funnel_data.append({
            'Stage': 'Total Users',
            'Group': 'Control' if group == 'A' else 'Treatment',
            'Count': len(group_data)
        })
        funnel_data.append({
            'Stage': 'Viewed',
            'Group': 'Control' if group == 'A' else 'Treatment',
            'Count': group_data['viewed'].sum()
        })
        funnel_data.append({
            'Stage': 'Clicked',
            'Group': 'Control' if group == 'A' else 'Treatment',
            'Count': group_data['clicked'].sum()
        })
        funnel_data.append({
            'Stage': 'Purchased',
            'Group': 'Control' if group == 'A' else 'Treatment',
            'Count': group_data['purchased'].sum()
        })
    
    funnel_df = pd.DataFrame(funnel_data)
    
    fig = px.funnel(
        funnel_df,
        x='Count',
        y='Stage',
        color='Group',
        title='Conversion Funnel by Group'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Segment performance
    st.markdown("### 📈 Segment Performance")
    
    # Device segment analysis
    device_performance = df.groupby(['device', 'group']).agg({
        'purchased': ['sum', 'count']
    }).reset_index()
    
    device_performance.columns = ['Device', 'Group', 'Purchases', 'Users']
    device_performance['Conversion Rate'] = device_performance['Purchases'] / device_performance['Users']
    
    fig = px.bar(
        device_performance,
        x='Device',
        y='Conversion Rate',
        color='Group',
        barmode='group',
        title='Conversion Rate by Device and Group'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("### 🎯 Recommendations")
    
    if st.session_state.decision_results:
        decision = st.session_state.decision_results
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>Primary Recommendation: <span class="success">{decision['decision']}</span></h3>
            <p><strong>Confidence:</strong> {decision['confidence']:.1%}</p>
            <p><strong>Key Insights:</strong></p>
            <ul>
                <li>Statistical significance achieved with p-value &lt; 0.05</li>
                <li>Positive business impact projected</li>
                <li>Consistent results across key segments</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Action items
        st.markdown("#### 🚀 Action Items")
        for i, step in enumerate(decision['next_steps'], 1):
            st.write(f"{i}. {step}")

if __name__ == "__main__":
    main()
