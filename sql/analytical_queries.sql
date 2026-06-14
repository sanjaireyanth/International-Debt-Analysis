USE international_debt;

-- BASIC QUERIES

-- 1. Retrieve all distinct country names from the dataset.
SELECT DISTINCT country_name
FROM countries
ORDER BY country_name;

-- 2. Count the total number of countries available.
SELECT COUNT(*) AS total_countries
FROM countries;

-- 3. Find the total number of indicators present.
SELECT COUNT(*) AS total_indicators
FROM indicators;

-- 4. Display the first 10 records of the dataset.
SELECT
    d.debt_id,
    c.country_name,
    d.country_code,
    i.indicator_name,
    d.indicator_code,
    d.year,
    d.debt_value_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
JOIN indicators i ON d.indicator_code = i.indicator_code
ORDER BY d.debt_id
LIMIT 10;

-- 5. Calculate the total global debt for the main reporting year.
SELECT
    year,
    SUM(debt_value_usd) AS total_global_external_debt_usd,
    SUM(value_billions_usd) AS total_global_external_debt_billions_usd
FROM debt_data
WHERE indicator_code = 'DT.DOD.DECT.CD'
  AND year = 2022
GROUP BY year;

-- 6. List all unique indicator names.
SELECT DISTINCT indicator_name
FROM indicators
ORDER BY indicator_name;

-- 7. Find the number of records for each country.
SELECT
    c.country_name,
    COUNT(*) AS record_count
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY record_count DESC, c.country_name;

-- 8. Display all records where debt is greater than 1 billion USD.
SELECT
    c.country_name,
    i.indicator_name,
    d.year,
    d.debt_value_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
JOIN indicators i ON d.indicator_code = i.indicator_code
WHERE d.year = 2022
  AND d.debt_value_usd > 1000000000
ORDER BY d.debt_value_usd DESC;

-- 9. Find the minimum, maximum, and average debt values.
SELECT
    MIN(debt_value_usd) AS minimum_debt_usd,
    MAX(debt_value_usd) AS maximum_debt_usd,
    AVG(debt_value_usd) AS average_debt_usd
FROM debt_data
WHERE year = 2022;

-- 10. Count total number of records in the dataset.
SELECT COUNT(*) AS total_records
FROM debt_data;


-- INTERMEDIATE QUERIES

-- 1. Find the total debt for each country.
SELECT
    c.country_name,
    d.year,
    SUM(d.debt_value_usd) AS total_external_debt_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
GROUP BY c.country_name, d.year
ORDER BY total_external_debt_usd DESC;

-- 2. Display the top 10 countries with the highest total debt.
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY d.debt_value_usd DESC
LIMIT 10;

-- 3. Find the average debt per country across available years.
SELECT
    c.country_name,
    AVG(d.debt_value_usd) AS average_external_debt_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
GROUP BY c.country_name
ORDER BY average_external_debt_usd DESC;

-- 4. Calculate total debt for each indicator.
SELECT
    i.indicator_name,
    i.measure_type,
    SUM(d.debt_value_usd) AS total_value_usd
FROM debt_data d
JOIN indicators i ON d.indicator_code = i.indicator_code
WHERE d.year = 2022
GROUP BY i.indicator_name, i.measure_type
ORDER BY total_value_usd DESC;

-- 5. Identify the indicator contributing the highest total debt.
SELECT
    i.indicator_name,
    i.measure_type,
    SUM(d.debt_value_usd) AS total_value_usd
FROM debt_data d
JOIN indicators i ON d.indicator_code = i.indicator_code
WHERE d.year = 2022
GROUP BY i.indicator_name, i.measure_type
ORDER BY total_value_usd DESC
LIMIT 1;

-- 6. Find the country with the lowest total debt.
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY d.debt_value_usd ASC
LIMIT 1;

-- 7. Calculate total debt for each country and indicator combination.
SELECT
    c.country_name,
    i.indicator_name,
    SUM(d.debt_value_usd) AS total_value_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
JOIN indicators i ON d.indicator_code = i.indicator_code
WHERE d.year = 2022
GROUP BY c.country_name, i.indicator_name
ORDER BY c.country_name, total_value_usd DESC;

-- 8. Count how many indicators each country has.
SELECT
    c.country_name,
    COUNT(DISTINCT d.indicator_code) AS indicator_count
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.year = 2022
GROUP BY c.country_name
ORDER BY indicator_count DESC, c.country_name;

-- 9. Display countries whose total debt is above the global country average.
WITH country_totals AS (
    SELECT
        country_code,
        debt_value_usd AS total_external_debt_usd
    FROM debt_data
    WHERE indicator_code = 'DT.DOD.DECT.CD'
      AND year = 2022
),
average_total AS (
    SELECT AVG(total_external_debt_usd) AS average_country_debt_usd
    FROM country_totals
)
SELECT
    c.country_name,
    ct.total_external_debt_usd,
    at.average_country_debt_usd
FROM country_totals ct
JOIN countries c ON ct.country_code = c.country_code
CROSS JOIN average_total at
WHERE ct.total_external_debt_usd > at.average_country_debt_usd
ORDER BY ct.total_external_debt_usd DESC;

-- 10. Rank countries based on total debt from highest to lowest.
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd,
    RANK() OVER (ORDER BY d.debt_value_usd DESC) AS debt_rank
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY debt_rank;


-- ADVANCED QUERIES

-- 1. Find the top 5 indicators contributing most to global debt.
SELECT
    i.indicator_name,
    i.measure_type,
    SUM(d.debt_value_usd) AS total_value_usd
FROM debt_data d
JOIN indicators i ON d.indicator_code = i.indicator_code
WHERE d.year = 2022
GROUP BY i.indicator_name, i.measure_type
ORDER BY total_value_usd DESC
LIMIT 5;

-- 2. Calculate percentage contribution of each country to total global debt.
WITH global_total AS (
    SELECT SUM(debt_value_usd) AS total_global_debt_usd
    FROM debt_data
    WHERE indicator_code = 'DT.DOD.DECT.CD'
      AND year = 2022
)
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd,
    ROUND((d.debt_value_usd / gt.total_global_debt_usd) * 100, 4) AS percentage_contribution
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
CROSS JOIN global_total gt
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY percentage_contribution DESC;

-- 3. Identify the top 3 countries for each indicator based on debt.
WITH ranked AS (
    SELECT
        i.indicator_name,
        c.country_name,
        d.debt_value_usd,
        RANK() OVER (
            PARTITION BY d.indicator_code
            ORDER BY d.debt_value_usd DESC
        ) AS indicator_rank
    FROM debt_data d
    JOIN countries c ON d.country_code = c.country_code
    JOIN indicators i ON d.indicator_code = i.indicator_code
    WHERE d.year = 2022
)
SELECT indicator_name, country_name, debt_value_usd, indicator_rank
FROM ranked
WHERE indicator_rank <= 3
ORDER BY indicator_name, indicator_rank;

-- 4. Find the difference between maximum and minimum debt for each country.
SELECT
    c.country_name,
    MAX(d.debt_value_usd) AS maximum_external_debt_usd,
    MIN(d.debt_value_usd) AS minimum_external_debt_usd,
    MAX(d.debt_value_usd) - MIN(d.debt_value_usd) AS debt_range_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
GROUP BY c.country_name
ORDER BY debt_range_usd DESC;

-- 5. Create a view for the top 10 countries with highest debt.
CREATE OR REPLACE VIEW v_top_10_countries_external_debt_2022 AS
SELECT
    c.country_name,
    c.region,
    d.debt_value_usd AS total_external_debt_usd,
    d.value_billions_usd AS total_external_debt_billions_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY d.debt_value_usd DESC
LIMIT 10;

SELECT *
FROM v_top_10_countries_external_debt_2022;

-- 6. Categorize countries into High, Medium, and Low Debt.
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd,
    CASE
        WHEN d.debt_value_usd >= 100000000000 THEN 'High Debt'
        WHEN d.debt_value_usd >= 10000000000 THEN 'Medium Debt'
        ELSE 'Low Debt'
    END AS debt_category
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
ORDER BY d.debt_value_usd DESC;

-- 7. Use window functions to calculate cumulative debt per country.
SELECT
    c.country_name,
    d.year,
    d.debt_value_usd,
    SUM(d.debt_value_usd) OVER (
        PARTITION BY d.country_code
        ORDER BY d.year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_external_debt_usd
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
ORDER BY c.country_name, d.year;

-- 8. Find indicators where average debt is higher than the overall average debt.
WITH overall_average AS (
    SELECT AVG(debt_value_usd) AS overall_average_usd
    FROM debt_data
    WHERE year = 2022
),
indicator_average AS (
    SELECT
        indicator_code,
        AVG(debt_value_usd) AS indicator_average_usd
    FROM debt_data
    WHERE year = 2022
    GROUP BY indicator_code
)
SELECT
    i.indicator_name,
    ia.indicator_average_usd,
    oa.overall_average_usd
FROM indicator_average ia
JOIN indicators i ON ia.indicator_code = i.indicator_code
CROSS JOIN overall_average oa
WHERE ia.indicator_average_usd > oa.overall_average_usd
ORDER BY ia.indicator_average_usd DESC;

-- 9. Identify countries contributing more than 5% of global debt.
WITH global_total AS (
    SELECT SUM(debt_value_usd) AS total_global_debt_usd
    FROM debt_data
    WHERE indicator_code = 'DT.DOD.DECT.CD'
      AND year = 2022
)
SELECT
    c.country_name,
    d.debt_value_usd AS total_external_debt_usd,
    ROUND((d.debt_value_usd / gt.total_global_debt_usd) * 100, 4) AS percentage_contribution
FROM debt_data d
JOIN countries c ON d.country_code = c.country_code
CROSS JOIN global_total gt
WHERE d.indicator_code = 'DT.DOD.DECT.CD'
  AND d.year = 2022
  AND (d.debt_value_usd / gt.total_global_debt_usd) > 0.05
ORDER BY percentage_contribution DESC;

-- 10. Find the most dominant indicator for each country.
WITH ranked_indicators AS (
    SELECT
        c.country_name,
        i.indicator_name,
        d.debt_value_usd,
        ROW_NUMBER() OVER (
            PARTITION BY d.country_code
            ORDER BY d.debt_value_usd DESC
        ) AS indicator_position
    FROM debt_data d
    JOIN countries c ON d.country_code = c.country_code
    JOIN indicators i ON d.indicator_code = i.indicator_code
    WHERE d.year = 2022
)
SELECT
    country_name,
    indicator_name AS dominant_indicator,
    debt_value_usd AS dominant_indicator_value_usd
FROM ranked_indicators
WHERE indicator_position = 1
ORDER BY dominant_indicator_value_usd DESC;
