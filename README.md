# Advanced A/B Testing Experimentation Platform

A comprehensive, production-ready A/B testing platform built with Python, featuring advanced statistical analysis, real-time decision making, and business intelligence capabilities.

## 🚀 Features

### Core Functionality
- **Data Simulation**: Generate realistic synthetic datasets with configurable user behavior patterns
- **Data Cleaning**: Automated validation and preprocessing with quality assurance
- **Statistical Testing**: Z-tests, confidence intervals, power analysis, and Bayesian methods
- **Decision Engine**: Automated experiment decisions based on statistical and business criteria
- **Segment Analysis**: Multi-dimensional performance analysis across user cohorts
- **Business Intelligence**: Power BI dashboard specifications and SQL analytics

### Advanced Analytics
- **Funnel Analysis**: Complete user journey tracking with drop-off analysis
- **Real-time Monitoring**: Live experiment performance tracking
- **Guardrail Metrics**: Automated detection of negative impacts
- **Power Analysis**: Sample size calculation and statistical power monitoring
- **Effect Size Measurement**: Quantifying business impact of experiments

### Enterprise Features
- **Scalable Architecture**: Microservices design for high-volume experiments
- **Data Quality Framework**: Comprehensive validation and anomaly detection
- **Security & Compliance**: GDPR/CCPA compliant data handling
- **API Integration**: RESTful APIs for seamless system integration
- **Monitoring & Alerting**: Real-time system health and business metrics

## 📊 Project Overview

This platform demonstrates end-to-end A/B testing capabilities for e-commerce product experiments, specifically testing redesigned Product Detail Pages (PDP) to improve conversion rates and user engagement.

### Experiment Design
- **Control Group**: Current PDP design with traditional layout
- **Treatment Group**: Enhanced PDP with larger images, prominent CTA, and simplified UI
- **Primary Metric**: Purchase Conversion Rate
- **Secondary Metrics**: Click-Through Rate, Time Spent, View Rate

### Statistical Parameters
- **Significance Level**: α = 0.05
- **Statistical Power**: 1-β = 0.80
- **Minimum Detectable Effect**: 5% relative improvement
- **Sample Size**: ~50,000 users per group

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (for production)
- Redis (for caching)
- Power BI Desktop (for dashboards)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ab-testing-platform.git
cd ab-testing-platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the complete pipeline**
```bash
python main.py
```

### Dependencies

```python
# Core libraries
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0

# Data visualization
matplotlib>=3.5.0
seaborn>=0.11.0
plotly>=5.0.0

# Database connections
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
redis>=4.0.0

# Statistical analysis
statsmodels>=0.13.0
scikit-learn>=1.1.0

# Utilities
python-dotenv>=0.19.0
tqdm>=4.64.0
```

## 📁 Project Structure

```
ab-testing-platform/
├── README.md                    # This file
├── requirements.txt              # Python dependencies
├── main.py                      # Main execution script
├── config/
│   ├── experiment_config.yaml   # Experiment configuration
│   └── database_config.yaml     # Database settings
├── src/
│   ├── data_simulation.py       # Synthetic data generation
│   ├── data_cleaning.py         # Data validation and preprocessing
│   ├── statistical_testing.py   # Statistical analysis engine
│   ├── decision_engine.py       # Automated decision making
│   └── database_connector.py    # Database interface
├── sql/
│   └── sql_queries.sql          # Analytics queries
├── dashboards/
│   └── power_bi_dashboard.md    # Dashboard specifications
├── docs/
│   ├── experiment_design.md     # Experiment methodology
│   ├── production_improvements.md # Scaling recommendations
│   └── api_documentation.md     # API reference
├── tests/
│   ├── test_data_simulation.py  # Unit tests
│   ├── test_statistical.py      # Statistical tests
│   └── test_integration.py     # Integration tests
└── examples/
    ├── sample_experiment.py     # Example usage
    └── custom_analysis.py       # Custom analysis examples
```

## 🚀 Quick Usage Guide

### 1. Generate Synthetic Data

```python
from src.data_simulation import ABTestDataGenerator

# Create data generator
generator = ABTestDataGenerator(seed=42)

# Generate dataset
df = generator.generate_dataset()

# Save to CSV
df.to_csv('experiment_data.csv', index=False)
```

### 2. Clean and Validate Data

```python
from src.data_cleaning import ABTestCleaner

# Initialize cleaner
cleaner = ABTestCleaner()

# Clean data
cleaned_df, quality_report = cleaner.clean_data('experiment_data.csv')

print(f"Cleaned {len(cleaned_df)} records")
print(f"Data quality score: {quality_report['quality_score']:.2%}")
```

### 3. Statistical Analysis

```python
from src.statistical_testing import ABTestStatisticalAnalyzer

# Create analyzer
analyzer = ABTestStatisticalAnalyzer(significance_level=0.05)

# Run full analysis
results = analyzer.run_full_analysis(cleaned_df)

# Generate report
report = analyzer.generate_report(results)
print(report)

# Create visualizations
analyzer.visualize_results(results, 'experiment_results.png')
```

### 4. Automated Decision Making

```python
from src.decision_engine import ABTestDecisionEngine

# Create decision engine
engine = ABTestDecisionEngine()

# Make decision
recommendation = engine.make_decision(
    primary_result=results['conversion'],
    guardrail_results=[results['ctr'], results['view_rate']],
    segment_results=results['device_segments']
)

# Print recommendation
print(engine.generate_decision_report(recommendation))
```

### 5. SQL Analytics

```sql
-- Funnel Analysis
SELECT 
    group,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate
FROM ab_test_data
GROUP BY group;

-- Segment Analysis
SELECT 
    group,
    device,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate
FROM ab_test_data
GROUP BY group, device
ORDER BY conversion_rate DESC;
```

## 📊 Key Metrics & KPIs

### Primary Metrics
- **Conversion Rate**: Purchases / Total Users
- **Click-Through Rate**: Clicks / Views
- **View Rate**: Views / Total Users
- **Time Spent**: Average engagement time

### Business Impact Metrics
- **Revenue Per User (RPU)**: Total revenue / Total users
- **Average Order Value (AOV)**: Total revenue / Total purchases
- **Customer Lifetime Value (CLV)**: Long-term customer value

### Statistical Metrics
- **P-value**: Statistical significance threshold
- **Confidence Interval**: Range of plausible effect sizes
- **Statistical Power**: Probability of detecting true effects
- **Effect Size**: Magnitude of treatment effect

## 🎯 Experiment Results

### Sample Output
```
=== EXPERIMENT SUMMARY ===
Control Group (A): 50,000 users
Treatment Group (B): 50,000 users

Conversion Rate:
  Control: 3.20%
  Treatment: 3.60%
  Lift: 12.50%

Click-Through Rate:
  Control: 12.00%
  Treatment: 13.80%
  Lift: 15.00%

Statistical Significance:
  Conversion: p = 0.023 (Significant)
  CTR: p = 0.045 (Significant)

Decision: LAUNCH TREATMENT
Confidence: 92.3%
```

## 🔧 Configuration

### Experiment Configuration
```yaml
experiment:
  name: "PDP Redesign Test"
  hypothesis: "New PDP design will increase conversion rate"
  primary_metric: "conversion_rate"
  secondary_metrics: ["ctr", "time_spent", "view_rate"]
  
traffic_allocation:
  control: 0.5
  treatment: 0.5
  
statistical_parameters:
  significance_level: 0.05
  power: 0.80
  minimum_detectable_effect: 0.05
  
duration:
  start_date: "2024-01-01"
  end_date: "2024-01-14"
```

### Database Configuration
```yaml
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  database: "ab_testing"
  username: "analyst"
  password: "${DB_PASSWORD}"
  
redis:
  host: "localhost"
  port: 6379
  db: 0
```

## 📈 Power BI Dashboard

### Dashboard Components
1. **Executive Summary**: Key metrics and decision status
2. **Funnel Visualization**: User journey analysis
3. **Statistical Analysis**: Significance testing and confidence intervals
4. **Segment Performance**: Device, user type, and geographic breakdown
5. **Time Series Analysis**: Daily trends and patterns

### Setup Instructions
1. Open Power BI Desktop
2. Connect to cleaned CSV data
3. Import DAX measures from `dashboards/dax_measures.txt`
4. Apply visualizations per specifications in `dashboards/power_bi_dashboard.md`

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/test_data_simulation.py -v
python -m pytest tests/test_statistical.py -v
python -m pytest tests/test_integration.py -v
```

### Run Integration Tests
```bash
python -m pytest tests/ -v --cov=src
```

### Test Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t ab-testing-platform .

# Run container
docker run -p 8000:8000 ab-testing-platform
```

### Kubernetes Deployment
```bash
# Apply configuration
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=ab-testing-platform
```

### Environment Variables
```bash
export DB_HOST="your-database-host"
export DB_PASSWORD="your-password"
export REDIS_HOST="your-redis-host"
export LOG_LEVEL="INFO"
```

## 📚 API Documentation

### Endpoints

#### GET /api/v1/experiments
List all experiments
```python
response = requests.get('http://localhost:8000/api/v1/experiments')
experiments = response.json()
```

#### POST /api/v1/experiments
Create new experiment
```python
experiment_config = {
    "name": "New Feature Test",
    "hypothesis": "Feature X will improve conversion",
    "primary_metric": "conversion_rate"
}
response = requests.post('http://localhost:8000/api/v1/experiments', json=experiment_config)
```

#### GET /api/v1/experiments/{id}/results
Get experiment results
```python
response = requests.get(f'http://localhost:8000/api/v1/experiments/{experiment_id}/results')
results = response.json()
```

## 🔍 Monitoring & Alerting

### System Health
- **API Response Time**: <100ms target
- **Data Processing Lag**: <5 minutes
- **Error Rate**: <1% threshold
- **Memory Usage**: <80% threshold

### Business Metrics
- **Experiment Velocity**: Experiments per week
- **Decision Accuracy**: Automated vs manual decisions
- **User Adoption**: Platform usage metrics
- **ROI Impact**: Revenue from successful experiments

### Alert Configuration
```python
alerts = {
    "high_error_rate": {"threshold": 0.05, "window": "5m"},
    "slow_processing": {"threshold": 300, "metric": "lag_seconds"},
    "low_power": {"threshold": 0.8, "metric": "statistical_power"}
}
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation
- Ensure test coverage >90%

### Code Review Process
- Automated tests must pass
- Code quality checks (linting, formatting)
- Manual review by maintainers
- Documentation review

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Statistical Methods**: Inspired by industry best practices from Netflix, Google, and Meta
- **Design Patterns**: Microservices architecture patterns from Martin Fowler
- **Data Science**: Statistical testing methodologies from "Trustworthy Online Controlled Experiments"

## 📞 Support & Contact

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ab-testing-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ab-testing-platform/discussions)
- **Email**: your.email@example.com

## 🗺️ Roadmap

### Version 2.0 (Q2 2024)
- [ ] Multi-armed bandit testing
- [ ] Bayesian statistical methods
- [ ] Real-time streaming analytics
- [ ] Advanced ML-powered insights

### Version 3.0 (Q3 2024)
- [ ] Mobile app integration
- [ ] Advanced segmentation
- [ ] Causal inference capabilities
- [ ] Enterprise SSO integration

### Long-term Vision
- [ ] AI-powered experiment design
- [ ] Cross-platform experimentation
- [ ] Global experimentation network
- [ ] Real-time personalization engine

---

**Built with ❤️ for data-driven decision making**

*Empowering teams to make better product decisions through rigorous experimentation and statistical analysis.*

# ProdX-Data-Driven-Product-Decision-Engine
ProdX is an end-to-end product analytics system designed to simulate A/B testing workflows and enable data-driven product decisions using user behavior insights and statistical validation.
