CREATE DATABASE IF NOT EXISTS international_debt;
USE international_debt;

DROP TABLE IF EXISTS debt_data;
DROP TABLE IF EXISTS indicators;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country_code VARCHAR(3) NOT NULL,
    country_name VARCHAR(160) NOT NULL,
    short_name VARCHAR(160),
    region VARCHAR(120),
    income_group VARCHAR(80),
    lending_category VARCHAR(40),
    currency_unit VARCHAR(80),
    PRIMARY KEY (country_code)
);

CREATE TABLE indicators (
    indicator_code VARCHAR(50) NOT NULL,
    indicator_name VARCHAR(255) NOT NULL,
    measure_type VARCHAR(80),
    topic VARCHAR(255),
    source VARCHAR(255),
    short_definition TEXT,
    PRIMARY KEY (indicator_code)
);

CREATE TABLE debt_data (
    debt_id BIGINT NOT NULL,
    country_code VARCHAR(3) NOT NULL,
    indicator_code VARCHAR(50) NOT NULL,
    year SMALLINT NOT NULL,
    debt_value_usd DECIMAL(24, 4) NOT NULL,
    value_billions_usd DECIMAL(20, 8) NOT NULL,
    PRIMARY KEY (debt_id),
    CONSTRAINT fk_debt_country
        FOREIGN KEY (country_code) REFERENCES countries(country_code),
    CONSTRAINT fk_debt_indicator
        FOREIGN KEY (indicator_code) REFERENCES indicators(indicator_code)
);

CREATE INDEX idx_debt_year ON debt_data(year);
CREATE INDEX idx_debt_country_year ON debt_data(country_code, year);
CREATE INDEX idx_debt_indicator_year ON debt_data(indicator_code, year);
CREATE INDEX idx_indicators_measure_type ON indicators(measure_type);

-- Import order:
-- 1. countries.csv
-- 2. indicators.csv
-- 3. debt_data.csv
--
-- Example MySQL import command. Update the path to match your machine.
--
-- LOAD DATA LOCAL INFILE 'data_processed/countries.csv'
-- INTO TABLE countries
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;
--
-- LOAD DATA LOCAL INFILE 'data_processed/indicators.csv'
-- INTO TABLE indicators
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;
--
-- LOAD DATA LOCAL INFILE 'data_processed/debt_data.csv'
-- INTO TABLE debt_data
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;
