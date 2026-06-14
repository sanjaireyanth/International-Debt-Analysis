from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data_processed" / "debt_cleaned_long.csv"
TOTAL_EXTERNAL_DEBT_CODE = "DT.DOD.DECT.CD"


st.set_page_config(
    page_title="International Debt Analysis",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error("Processed data not found. Run `python src/process_data.py` first.")
        st.stop()

    df = pd.read_csv(DATA_PATH)
    df["region"] = df["region"].fillna("Unknown")
    df["income_group"] = df["income_group"].fillna("Unknown")
    return df


df = load_data()

st.title("International Debt Analysis")

years = sorted(df["year"].unique(), reverse=True)
default_year_index = years.index(2022) if 2022 in years else 0
selected_year = st.sidebar.selectbox("Year", years, index=default_year_index)

regions = ["All"] + sorted(df["region"].dropna().unique())
selected_region = st.sidebar.selectbox("Region", regions)

measure_types = ["All"] + sorted(df["measure_type"].dropna().unique())
selected_measure_type = st.sidebar.selectbox("Measure Type", measure_types)

filtered = df[df["year"].eq(selected_year)].copy()
if selected_region != "All":
    filtered = filtered[filtered["region"].eq(selected_region)]
if selected_measure_type != "All":
    filtered = filtered[filtered["measure_type"].eq(selected_measure_type)]

total_debt = df[
    (df["year"].eq(selected_year)) & (df["series_code"].eq(TOTAL_EXTERNAL_DEBT_CODE))
].copy()
if selected_region != "All":
    total_debt = total_debt[total_debt["region"].eq(selected_region)]

global_total = total_debt["debt_value_usd"].sum()
country_count = total_debt["country_code"].nunique()
indicator_count = filtered["series_code"].nunique()
median_country_debt = total_debt["debt_value_usd"].median()

kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
kpi_1.metric("Total External Debt", f"${global_total / 1_000_000_000:,.1f}B")
kpi_2.metric("Countries", f"{country_count:,}")
kpi_3.metric("Indicators", f"{indicator_count:,}")
kpi_4.metric("Median Country Debt", f"${median_country_debt / 1_000_000_000:,.1f}B")

left, right = st.columns([1.2, 1])

with left:
    top_countries = total_debt.nlargest(15, "debt_value_usd").sort_values("debt_value_usd")
    fig = px.bar(
        top_countries,
        x="value_billions_usd",
        y="country_name",
        color="region",
        orientation="h",
        labels={
            "value_billions_usd": "Debt (USD Billions)",
            "country_name": "",
            "region": "Region",
        },
        title=f"Top Countries by Total External Debt, {selected_year}",
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    indicator_totals = (
        filtered.groupby(["series_name", "measure_type"], as_index=False)["debt_value_usd"]
        .sum()
        .assign(value_billions_usd=lambda data: data["debt_value_usd"] / 1_000_000_000)
        .nlargest(12, "debt_value_usd")
        .sort_values("debt_value_usd")
    )
    fig = px.bar(
        indicator_totals,
        x="value_billions_usd",
        y="series_name",
        color="measure_type",
        orientation="h",
        labels={
            "value_billions_usd": "Value (USD Billions)",
            "series_name": "",
            "measure_type": "Measure",
        },
        title=f"Highest Indicator Values, {selected_year}",
    )
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)

trend_source = df[df["series_code"].eq(TOTAL_EXTERNAL_DEBT_CODE)].copy()
if selected_region != "All":
    trend_source = trend_source[trend_source["region"].eq(selected_region)]

default_countries = (
    total_debt.nlargest(5, "debt_value_usd")["country_name"].sort_values().tolist()
)
country_options = sorted(trend_source["country_name"].unique())
selected_countries = st.multiselect(
    "Countries",
    country_options,
    default=[c for c in default_countries if c in country_options],
)

trend = trend_source[trend_source["country_name"].isin(selected_countries)].copy()
fig = px.line(
    trend,
    x="year",
    y="value_billions_usd",
    color="country_name",
    markers=True,
    labels={
        "year": "Year",
        "value_billions_usd": "Debt (USD Billions)",
        "country_name": "Country",
    },
    title="Total External Debt Trend",
)
fig.update_layout(height=460, margin=dict(l=10, r=10, t=60, b=10))
st.plotly_chart(fig, use_container_width=True)

region_total = (
    total_debt.groupby(["region"], as_index=False)["debt_value_usd"]
    .sum()
    .assign(value_billions_usd=lambda data: data["debt_value_usd"] / 1_000_000_000)
    .sort_values("debt_value_usd", ascending=False)
)

fig = px.treemap(
    region_total,
    path=["region"],
    values="debt_value_usd",
    color="value_billions_usd",
    color_continuous_scale="Tealrose",
    title=f"Regional Share of Total External Debt, {selected_year}",
)
fig.update_layout(height=420, margin=dict(l=10, r=10, t=60, b=10))
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    total_debt[
        [
            "country_name",
            "country_code",
            "region",
            "income_group",
            "year",
            "debt_value_usd",
            "value_billions_usd",
        ]
    ].sort_values("debt_value_usd", ascending=False),
    use_container_width=True,
    hide_index=True,
)
