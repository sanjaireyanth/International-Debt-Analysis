# International Debt Analysis

End-to-end finance analytics project using World Bank International Debt Statistics.

## Project Scope

This project completes the requested workflow:

- CSV loading and Pandas DataFrame conversion
- Data cleaning, missing-value handling, duplicate removal, and long-format transformation
- Exploratory data analysis for country-wise and indicator-wise debt
- Normalized MySQL schema with country, indicator, and debt fact tables
- 30 analytical SQL queries
- Streamlit dashboard
- Final EDA documentation in DOCX, PDF, and Markdown

## Dataset

Source: World Bank International Debt Statistics  
Download used: `https://databankfiles.worldbank.org/public/ddpext_download/IDS_CSV.zip`

The cleaned dataset focuses on World-counterpart monetary debt indicators measured in current US dollars for 2010-2022. The main reporting year is 2022.

## Folder Structure

```text
international_debt_project/
  dashboard/
    streamlit_app.py
  data_processed/
    countries.csv
    indicators.csv
    debt_data.csv
    debt_cleaned_long.csv
    data_quality_summary.json
    summary CSV files
  data_raw/
    IDS_CSV.zip
    IDS_CSV/
  docs/
    International_Debt_Analysis_Report.docx
    International_Debt_Analysis_Report.pdf
    EDA_Report.md
  sql/
    schema_mysql.sql
    analytical_queries.sql
  src/
    process_data.py
    generate_report.py
  requirements.txt
```

## Run the Pipeline

```bash
pip install -r requirements.txt
python src/process_data.py
python src/generate_report.py
```

## Run the Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

## MySQL Import

1. Create tables using `sql/schema_mysql.sql`.
2. Import the CSV files in this order:
   1. `data_processed/countries.csv`
   2. `data_processed/indicators.csv`
   3. `data_processed/debt_data.csv`
3. Run `sql/analytical_queries.sql`.

## Main Outputs

- `data_processed/debt_cleaned_long.csv`: denormalized analytics table for dashboard and EDA.
- `data_processed/countries.csv`: country dimension table.
- `data_processed/indicators.csv`: indicator dimension table.
- `data_processed/debt_data.csv`: normalized fact table.
- `sql/schema_mysql.sql`: database schema with keys and indexes.
- `sql/analytical_queries.sql`: 30 SQL analytical queries.
- `dashboard/streamlit_app.py`: interactive dashboard.
- `docs/International_Debt_Analysis_Report.pdf`: final report.
