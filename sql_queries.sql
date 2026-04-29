-- =====================================================
-- A/B Testing Platform - SQL Queries
-- =====================================================

-- =====================================================
-- 1. FUNNEL ANALYSIS QUERIES
-- =====================================================

-- Overall Conversion Funnel by Group
SELECT 
    group,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(viewed) * 100.0 / COUNT(DISTINCT user_id), 2) as view_rate_pct,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as click_through_rate_pct,
    ROUND(SUM(purchased) * 100.0 / SUM(clicked), 2) as click_to_purchase_rate_pct,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as overall_conversion_pct
FROM ab_test_data
GROUP BY group
ORDER BY group;

-- Funnel Drop-off Analysis
WITH funnel_stages AS (
    SELECT 
        group,
        COUNT(DISTINCT user_id) as stage_0_total_users,
        SUM(viewed) as stage_1_viewed,
        SUM(clicked) as stage_2_clicked,
        SUM(purchased) as stage_3_purchased
    FROM ab_test_data
    GROUP BY group
),
drop_off_analysis AS (
    SELECT 
        group,
        stage_0_total_users,
        stage_1_viewed,
        stage_2_clicked,
        stage_3_purchased,
        stage_0_total_users - stage_1_viewed as drop_off_view,
        stage_1_viewed - stage_2_clicked as drop_off_click,
        stage_2_clicked - stage_3_purchased as drop_off_purchase,
        ROUND((stage_0_total_users - stage_1_viewed) * 100.0 / stage_0_total_users, 2) as drop_off_view_pct,
        ROUND((stage_1_viewed - stage_2_clicked) * 100.0 / stage_1_viewed, 2) as drop_off_click_pct,
        ROUND((stage_2_clicked - stage_3_purchased) * 100.0 / stage_2_clicked, 2) as drop_off_purchase_pct
    FROM funnel_stages
)
SELECT * FROM drop_off_analysis;

-- Time-based Funnel Analysis (Hour of Day)
SELECT 
    group,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate
FROM ab_test_data
GROUP BY group, EXTRACT(HOUR FROM timestamp)
ORDER BY group, hour_of_day;

-- =====================================================
-- 2. SEGMENT ANALYSIS QUERIES
-- =====================================================

-- Device Type Performance Analysis
SELECT 
    group,
    device,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(viewed) * 100.0 / COUNT(DISTINCT user_id), 2) as view_rate_pct,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as ctr_pct,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate_pct,
    ROUND(AVG(CASE WHEN viewed = 1 THEN time_spent END), 2) as avg_time_spent_seconds
FROM ab_test_data
GROUP BY group, device
ORDER BY group, device;

-- New vs Returning User Analysis
SELECT 
    group,
    CASE WHEN new_user = 1 THEN 'New User' ELSE 'Returning User' END as user_type,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(viewed) * 100.0 / COUNT(DISTINCT user_id), 2) as view_rate_pct,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as ctr_pct,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate_pct,
    ROUND(AVG(CASE WHEN viewed = 1 THEN time_spent END), 2) as avg_time_spent_seconds
FROM ab_test_data
GROUP BY group, new_user
ORDER BY group, user_type;

-- Geographic Region Analysis
SELECT 
    group,
    region,
    COUNT(DISTINCT user_id) as total_users,
    SUM(viewed) as viewed_users,
    SUM(clicked) as clicked_users,
    SUM(purchased) as purchased_users,
    ROUND(SUM(viewed) * 100.0 / COUNT(DISTINCT user_id), 2) as view_rate_pct,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as ctr_pct,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate_pct,
    ROUND(AVG(CASE WHEN viewed = 1 THEN time_spent END), 2) as avg_time_spent_seconds
FROM ab_test_data
GROUP BY group, region
ORDER BY group, region;

-- Multi-dimensional Segment Analysis (Device + User Type)
SELECT 
    group,
    device,
    CASE WHEN new_user = 1 THEN 'New User' ELSE 'Returning User' END as user_type,
    COUNT(DISTINCT user_id) as total_users,
    SUM(purchased) as purchases,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate_pct,
    ROUND(AVG(CASE WHEN viewed = 1 THEN time_spent END), 2) as avg_time_spent_seconds
FROM ab_test_data
GROUP BY group, device, new_user
ORDER BY group, device, user_type;

-- =====================================================
-- 3. KPI CALCULATION QUERIES
-- =====================================================

-- Primary KPIs by Group
WITH kpi_metrics AS (
    SELECT 
        group,
        COUNT(DISTINCT user_id) as total_users,
        SUM(viewed) as total_views,
        SUM(clicked) as total_clicks,
        SUM(purchased) as total_purchases,
        SUM(CASE WHEN viewed = 1 THEN time_spent END) as total_time_spent
    FROM ab_test_data
    GROUP BY group
)
SELECT 
    group,
    total_users,
    total_views,
    total_clicks,
    total_purchases,
    ROUND(total_views * 100.0 / total_users, 2) as view_rate_kpi,
    ROUND(total_clicks * 100.0 / total_views, 2) as ctr_kpi,
    ROUND(total_purchases * 100.0 / total_users, 2) as conversion_rate_kpi,
    ROUND(total_purchases * 100.0 / total_clicks, 2) as click_to_conversion_kpi,
    ROUND(total_time_spent / NULLIF(total_views, 0), 2) as avg_time_per_view,
    ROUND(total_time_spent / NULLIF(total_users, 0), 2) as avg_time_per_user
FROM kpi_metrics
ORDER BY group;

-- Revenue-based KPIs (assuming average order value)
WITH revenue_metrics AS (
    SELECT 
        group,
        COUNT(DISTINCT user_id) as total_users,
        SUM(purchased) as total_purchases,
        -- Assuming average order value of $75
        SUM(purchased) * 75.0 as total_revenue,
        COUNT(DISTINCT CASE WHEN purchased = 1 THEN user_id END) as unique_purchasers
    FROM ab_test_data
    GROUP BY group
)
SELECT 
    group,
    total_users,
    total_purchases,
    total_revenue,
    unique_purchasers,
    ROUND(total_revenue / total_users, 2) as revenue_per_user,
    ROUND(total_revenue / NULLIF(unique_purchasers, 0), 2) as revenue_per_purchaser,
    ROUND(total_revenue / NULLIF(total_purchases, 0), 2) as avg_order_value
FROM revenue_metrics
ORDER BY group;

-- Daily KPI Trends
SELECT 
    group,
    DATE(timestamp) as experiment_date,
    COUNT(DISTINCT user_id) as daily_users,
    SUM(viewed) as daily_views,
    SUM(clicked) as daily_clicks,
    SUM(purchased) as daily_purchases,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as daily_conversion_rate,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as daily_ctr
FROM ab_test_data
GROUP BY group, DATE(timestamp)
ORDER BY group, experiment_date;

-- =====================================================
-- 4. STATISTICAL TESTING SUPPORT QUERIES
-- =====================================================

-- Data for Z-test Calculations
SELECT 
    group,
    COUNT(DISTINCT user_id) as sample_size,
    SUM(purchased) as successes,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 4) as conversion_rate,
    SQRT(SUM(purchased) * (COUNT(DISTINCT user_id) - SUM(purchased)) / 
         POWER(COUNT(DISTINCT user_id), 3)) as standard_error
FROM ab_test_data
GROUP BY group;

-- CTR Data for Z-test
SELECT 
    group,
    SUM(viewed) as views,
    SUM(clicked) as clicks,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 4) as ctr_rate,
    SQRT(SUM(clicked) * (SUM(viewed) - SUM(clicked)) / 
         POWER(SUM(viewed), 3)) as ctr_standard_error
FROM ab_test_data
WHERE viewed = 1
GROUP BY group;

-- Sample Size Validation
SELECT 
    group,
    COUNT(DISTINCT user_id) as actual_sample_size,
    -- Minimum required sample size for 5% MDE at 80% power
    CASE 
        WHEN COUNT(DISTINCT user_id) >= 38400 THEN 'Sufficient'
        ELSE 'Insufficient'
    END as sample_size_status,
    -- Power calculation approximation
    ROUND(1 - POWER(0.95, COUNT(DISTINCT user_id) / 38400.0), 3) as estimated_power
FROM ab_test_data
GROUP BY group;

-- =====================================================
-- 5. ADVANCED ANALYTICS QUERIES
-- =====================================================

-- Cohort Analysis (by signup date)
WITH user_cohorts AS (
    SELECT 
        user_id,
        group,
        DATE(MIN(timestamp)) as cohort_date,
        viewed,
        clicked,
        purchased,
        time_spent
    FROM ab_test_data
    GROUP BY user_id, group, viewed, clicked, purchased, time_spent
)
SELECT 
    group,
    cohort_date,
    COUNT(DISTINCT user_id) as cohort_size,
    SUM(purchased) as purchases,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate
FROM user_cohorts
GROUP BY group, cohort_date
ORDER BY group, cohort_date;

-- User Engagement Segments
WITH engagement_segments AS (
    SELECT 
        user_id,
        group,
        CASE 
            WHEN time_spent = 0 THEN 'No Engagement'
            WHEN time_spent < 30 THEN 'Low Engagement'
            WHEN time_spent < 120 THEN 'Medium Engagement'
            ELSE 'High Engagement'
        END as engagement_level,
        purchased
    FROM ab_test_data
    WHERE viewed = 1
)
SELECT 
    group,
    engagement_level,
    COUNT(DISTINCT user_id) as users,
    SUM(purchased) as purchases,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as conversion_rate
FROM engagement_segments
GROUP BY group, engagement_level
ORDER BY group, 
    CASE engagement_level 
        WHEN 'High Engagement' THEN 1
        WHEN 'Medium Engagement' THEN 2
        WHEN 'Low Engagement' THEN 3
        WHEN 'No Engagement' THEN 4
    END;

-- Statistical Summary for Dashboard
SELECT 
    'Conversion Rate' as metric,
    group,
    ROUND(SUM(purchased) * 100.0 / COUNT(DISTINCT user_id), 2) as value,
    'percentage' as unit
FROM ab_test_data
GROUP BY group

UNION ALL

SELECT 
    'Click-Through Rate' as metric,
    group,
    ROUND(SUM(clicked) * 100.0 / SUM(viewed), 2) as value,
    'percentage' as unit
FROM ab_test_data
GROUP BY group

UNION ALL

SELECT 
    'Average Time Spent' as metric,
    group,
    ROUND(AVG(CASE WHEN viewed = 1 THEN time_spent END), 2) as value,
    'seconds' as unit
FROM ab_test_data
GROUP BY group

UNION ALL

SELECT 
    'Total Users' as metric,
    group,
    COUNT(DISTINCT user_id) as value,
    'count' as unit
FROM ab_test_data
GROUP BY group

ORDER BY metric, group;
