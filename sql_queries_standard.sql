-- Standard SQL Queries for A/B Testing Platform
-- Compatible with SQLite, MySQL, PostgreSQL, and other SQL databases

-- ============================================================================
-- TABLE CREATION
-- ============================================================================

-- Create experiments table
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hypothesis TEXT,
    primary_metric TEXT,
    secondary_metrics TEXT,
    status TEXT DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config TEXT,
    traffic_allocation TEXT,
    significance_level REAL DEFAULT 0.05,
    power REAL DEFAULT 0.80,
    min_effect_size REAL DEFAULT 0.05,
    sample_size INTEGER DEFAULT 1000
);

-- Create user_events table
CREATE TABLE IF NOT EXISTS user_events (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    device TEXT,
    region TEXT,
    new_user INTEGER DEFAULT 0,
    viewed INTEGER DEFAULT 0,
    clicked INTEGER DEFAULT 0,
    purchased INTEGER DEFAULT 0,
    time_spent REAL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id),
    UNIQUE(experiment_id, user_id)
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    analysis_type TEXT,
    results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

-- Create decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    decision TEXT,
    confidence REAL,
    reasoning TEXT,
    business_impact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_events_experiment_id ON user_events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_user_events_timestamp ON user_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_events_group_id ON user_events(group_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);

-- ============================================================================
-- BASIC QUERIES
-- ============================================================================

-- Insert new experiment
INSERT INTO experiments (
    id, name, hypothesis, primary_metric, secondary_metrics, 
    status, created_at, updated_at, config, traffic_allocation,
    significance_level, power, min_effect_size, sample_size
) VALUES (
    'exp_001', 'PDP Redesign Test', 'New design will increase conversion rate',
    'conversion_rate', '["ctr", "time_spent"]', 'created',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '{"seed": 42}',
    '{"control": 0.5, "treatment": 0.5}', 0.05, 0.80, 0.05, 10000
);

-- Insert user events
INSERT INTO user_events (
    id, experiment_id, user_id, group_id, device, region, new_user,
    viewed, clicked, purchased, time_spent, timestamp, metadata
) VALUES (
    'event_001', 'exp_001', 'user_12345', 'A', 'mobile', 'US', 1,
    1, 1, 0, 120.5, CURRENT_TIMESTAMP, '{"source": "organic"}'
);

-- ============================================================================
-- FUNNEL ANALYSIS QUERIES
-- ============================================================================

-- Basic funnel analysis
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as conversion_rate,
    ROUND(CAST(SUM(clicked) AS REAL) / SUM(viewed) * 100, 2) as click_through_rate,
    ROUND(CAST(SUM(viewed) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as view_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id
ORDER BY group_id;

-- Funnel with drop-off rates
SELECT 
    group_id,
    'Total Users' as stage,
    COUNT(DISTINCT user_id) as count,
    0 as drop_off_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id

UNION ALL

SELECT 
    group_id,
    'Viewed' as stage,
    SUM(viewed) as count,
    ROUND((COUNT(DISTINCT user_id) - SUM(viewed)) * 100.0 / COUNT(DISTINCT user_id), 2) as drop_off_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id

UNION ALL

SELECT 
    group_id,
    'Clicked' as stage,
    SUM(clicked) as count,
    ROUND((SUM(viewed) - SUM(clicked)) * 100.0 / SUM(viewed), 2) as drop_off_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id

UNION ALL

SELECT 
    group_id,
    'Purchased' as stage,
    SUM(purchased) as count,
    ROUND((SUM(clicked) - SUM(purchased)) * 100.0 / SUM(clicked), 2) as drop_off_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id

ORDER BY group_id, 
    CASE stage 
        WHEN 'Total Users' THEN 1
        WHEN 'Viewed' THEN 2
        WHEN 'Clicked' THEN 3
        WHEN 'Purchased' THEN 4
    END;

-- ============================================================================
-- SEGMENT ANALYSIS QUERIES
-- ============================================================================

-- Device segment analysis
SELECT 
    group_id,
    device,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as total_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as conversion_rate,
    ROUND(AVG(time_spent), 2) as avg_time_spent
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id, device
ORDER BY device, group_id;

-- New vs returning user analysis
SELECT 
    group_id,
    CASE 
        WHEN new_user = 1 THEN 'New User'
        ELSE 'Returning User'
    END as user_type,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as total_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as conversion_rate,
    ROUND(AVG(time_spent), 2) as avg_time_spent
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id, new_user
ORDER BY user_type, group_id;

-- Geographic region analysis
SELECT 
    group_id,
    region,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as total_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as conversion_rate,
    ROUND(AVG(time_spent), 2) as avg_time_spent
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id, region
ORDER BY region, group_id;

-- ============================================================================
-- KPI CALCULATION QUERIES
-- ============================================================================

-- Conversion rate calculation
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as total_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 4) as conversion_rate,
    ROUND(AVG(time_spent), 2) as avg_time_spent
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;

-- Click-through rate calculation
SELECT 
    group_id,
    SUM(viewed) as total_views,
    SUM(clicked) as total_clicks,
    ROUND(CAST(SUM(clicked) AS REAL) / SUM(viewed) * 100, 4) as click_through_rate
FROM user_events
WHERE experiment_id = 'exp_001' AND viewed > 0
GROUP BY group_id;

-- View rate calculation
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as total_views,
    ROUND(CAST(SUM(viewed) AS REAL) / COUNT(DISTINCT user_id) * 100, 4) as view_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;

-- Revenue per user calculation (assuming average order value of $75)
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as total_purchases,
    SUM(purchased) * 75 as total_revenue,
    ROUND(CAST(SUM(purchased) * 75 AS REAL) / COUNT(DISTINCT user_id), 2) as revenue_per_user
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;

-- ============================================================================
-- TIME SERIES ANALYSIS QUERIES
-- ============================================================================

-- Daily KPI trends
SELECT 
    DATE(timestamp) as date,
    group_id,
    COUNT(DISTINCT user_id) as daily_users,
    SUM(purchased) as daily_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 4) as daily_conversion_rate,
    ROUND(AVG(time_spent), 2) as daily_avg_time_spent
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY DATE(timestamp), group_id
ORDER BY date, group_id;

-- Weekly performance summary
SELECT 
    strftime('%Y-%W', timestamp) as week,
    group_id,
    COUNT(DISTINCT user_id) as weekly_users,
    SUM(purchased) as weekly_purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 4) as weekly_conversion_rate
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY strftime('%Y-%W', timestamp), group_id
ORDER BY week, group_id;

-- ============================================================================
-- STATISTICAL TESTING SUPPORT QUERIES
-- ============================================================================

-- Data for statistical testing
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as sample_size,
    SUM(purchased) as successes,
    SUM(viewed) as views,
    SUM(clicked) as clicks,
    AVG(time_spent) as avg_time_spent,
    -- Calculate variance for time spent
    (SELECT 
        SUM((time_spent - sub.avg_time) * (time_spent - sub.avg_time)) / (COUNT(*) - 1)
     FROM user_events sub 
     WHERE sub.experiment_id = user_events.experiment_id 
     AND sub.group_id = user_events.group_id
    ) as time_spent_variance
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;

-- Sample size adequacy check
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as current_sample_size,
    CASE 
        WHEN COUNT(DISTINCT user_id) >= 1000 THEN 'Adequate'
        WHEN COUNT(DISTINCT user_id) >= 500 THEN 'Marginal'
        ELSE 'Insufficient'
    END as sample_size_status
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;

-- ============================================================================
-- EXPERIMENT SUMMARY QUERIES
-- ============================================================================

-- Complete experiment summary
SELECT 
    e.id as experiment_id,
    e.name as experiment_name,
    e.status,
    e.created_at,
    COUNT(DISTINCT ue.user_id) as total_users,
    SUM(ue.purchased) as total_purchases,
    ROUND(CAST(SUM(ue.purchased) AS REAL) / COUNT(DISTINCT ue.user_id) * 100, 4) as overall_conversion_rate,
    ROUND(AVG(ue.time_spent), 2) as avg_time_spent
FROM experiments e
LEFT JOIN user_events ue ON e.id = ue.experiment_id
WHERE e.id = 'exp_001'
GROUP BY e.id, e.name, e.status, e.created_at;

-- Experiment performance comparison
WITH control_stats AS (
    SELECT 
        COUNT(DISTINCT user_id) as users,
        SUM(purchased) as purchases,
        AVG(time_spent) as avg_time
    FROM user_events
    WHERE experiment_id = 'exp_001' AND group_id = 'A'
),
treatment_stats AS (
    SELECT 
        COUNT(DISTINCT user_id) as users,
        SUM(purchased) as purchases,
        AVG(time_spent) as avg_time
    FROM user_events
    WHERE experiment_id = 'exp_001' AND group_id = 'B'
)
SELECT 
    'Conversion Rate' as metric,
    ROUND(CAST(control.purchases AS REAL) / control.users * 100, 4) as control_value,
    ROUND(CAST(treatment.purchases AS REAL) / treatment.users * 100, 4) as treatment_value,
    ROUND((CAST(treatment.purchases AS REAL) / treatment.users - CAST(control.purchases AS REAL) / control.users) * 100 / (CAST(control.purchases AS REAL) / control.users), 2) as relative_lift_percent
FROM control_stats, treatment_stats

UNION ALL

SELECT 
    'Average Time Spent' as metric,
    ROUND(control.avg_time, 2) as control_value,
    ROUND(treatment.avg_time, 2) as treatment_value,
    ROUND((treatment.avg_time - control.avg_time) * 100 / control.avg_time, 2) as relative_lift_percent
FROM control_stats, treatment_stats;

-- ============================================================================
-- DATA QUALITY QUERIES
-- ============================================================================

-- Check for data completeness
SELECT 
    'Total Records' as metric,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'Complete'
        ELSE 'Missing'
    END as status
FROM user_events
WHERE experiment_id = 'exp_001'

UNION ALL

SELECT 
    'Records with Views' as metric,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'Complete'
        ELSE 'Missing'
    END as status
FROM user_events
WHERE experiment_id = 'exp_001' AND viewed = 1

UNION ALL

SELECT 
    'Records with Clicks' as metric,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'Complete'
        ELSE 'Missing'
    END as status
FROM user_events
WHERE experiment_id = 'exp_001' AND clicked = 1

UNION ALL

SELECT 
    'Records with Purchases' as metric,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'Complete'
        ELSE 'Missing'
    END as status
FROM user_events
WHERE experiment_id = 'exp_001' AND purchased = 1;

-- Check for logical consistency
SELECT 
    'Invalid Clicks (No View)' as issue,
    COUNT(*) as count
FROM user_events
WHERE experiment_id = 'exp_001' AND clicked = 1 AND viewed = 0

UNION ALL

SELECT 
    'Invalid Purchases (No Click)' as issue,
    COUNT(*) as count
FROM user_events
WHERE experiment_id = 'exp_001' AND purchased = 1 AND clicked = 0

UNION ALL

SELECT 
    'Negative Time Spent' as issue,
    COUNT(*) as count
FROM user_events
WHERE experiment_id = 'exp_001' AND time_spent < 0;

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Clean up old data (older than 90 days)
DELETE FROM user_events 
WHERE timestamp < DATE('now', '-90 days');

DELETE FROM analysis_results 
WHERE created_at < DATE('now', '-90 days');

DELETE FROM decisions 
WHERE created_at < DATE('now', '-90 days');

-- Vacuum and optimize (SQLite specific)
VACUUM;

-- ============================================================================
-- REPORTING QUERIES
-- ============================================================================

-- Executive summary report
SELECT 
    e.name as experiment_name,
    e.status as current_status,
    e.created_at as start_date,
    COUNT(DISTINCT ue.user_id) as total_participants,
    ROUND(CAST(SUM(ue.purchased) AS REAL) / COUNT(DISTINCT ue.user_id) * 100, 2) as overall_conversion_rate,
    CASE 
        WHEN e.status = 'completed' THEN 'Experiment Complete'
        WHEN COUNT(DISTINCT ue.user_id) >= 1000 THEN 'Ready for Analysis'
        ELSE 'Gathering Data'
    END as recommendation
FROM experiments e
LEFT JOIN user_events ue ON e.id = ue.experiment_id
WHERE e.id = 'exp_001'
GROUP BY e.id, e.name, e.status, e.created_at;

-- Performance dashboard data
SELECT 
    group_id,
    COUNT(DISTINCT user_id) as users,
    SUM(viewed) as views,
    SUM(clicked) as clicks,
    SUM(purchased) as purchases,
    ROUND(CAST(SUM(purchased) AS REAL) / COUNT(DISTINCT user_id) * 100, 2) as conversion_rate,
    ROUND(CAST(SUM(clicked) AS REAL) / SUM(viewed) * 100, 2) as click_rate,
    ROUND(AVG(time_spent), 2) as avg_time,
    SUM(purchased) * 75 as estimated_revenue
FROM user_events
WHERE experiment_id = 'exp_001'
GROUP BY group_id;
