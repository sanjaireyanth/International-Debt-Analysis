from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data_raw" / "IDS_CSV"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data_processed"
TOTAL_EXTERNAL_DEBT_CODE = "DT.DOD.DECT.CD"


def snake_case(value: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", value).strip("_")


def classify_measure(series_name: str, series_code: str) -> str:
    name = series_name.lower()
    if series_code == TOTAL_EXTERNAL_DEBT_CODE:
        return "total_external_debt_stock"
    if "debt service" in name:
        return "debt_service"
    if "external debt stocks" in name or "debt stock" in name:
        return "debt_stock"
    if "principal repayments" in name:
        return "principal_repayment"
    if "interest payments" in name:
        return "interest_payment"
    if "disbursements" in name:
        return "disbursement"
    if "commitments" in name:
        return "commitment"
    if "net flows" in name or "net transfers" in name:
        return "net_flow"
    if "imf credit" in name:
        return "imf_credit"
    if "debt forgiveness" in name or "debt reduction" in name:
        return "debt_relief"
    return "other_debt_monetary"


def is_relevant_debt_indicator(series_name: str) -> bool:
    name = series_name.lower()
    has_usd_unit = "current us$" in name
    debt_terms = (
        "debt",
        "principal",
        "interest payments",
        "disbursements",
        "commitments",
        "imf credit",
        "public and publicly guaranteed",
        "private nonguaranteed",
        "official creditors",
        "bilateral creditors",
        "multilateral creditors",
        "commercial banks",
        "bonds",
        "suppliers",
    )
    return has_usd_unit and any(term in name for term in debt_terms)


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="latin1", low_memory=False)


def strip_text_values(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if is_object_dtype(df[column]) or is_string_dtype(df[column]):
            df[column] = df[column].astype("string").str.strip()
    return df


def load_and_clean(raw_dir: Path, start_year: int, end_year: int) -> tuple[pd.DataFrame, dict]:
    data_path = raw_dir / "IDS_ALLCountries_Data.csv"
    country_meta_path = raw_dir / "IDS_CountryMetaData.csv"
    series_meta_path = raw_dir / "IDS_SeriesMetaData.csv"

    raw = load_csv(data_path)
    raw.columns = [c.strip() for c in raw.columns]
    raw = strip_text_values(raw)
    initial_shape = raw.shape
    raw = raw.drop_duplicates()

    year_columns = [str(y) for y in range(start_year, end_year + 1)]
    available_years = [c for c in year_columns if c in raw.columns]
    if not available_years:
        raise ValueError(f"No requested year columns found between {start_year} and {end_year}.")

    id_columns = [
        "Country Name",
        "Country Code",
        "Counterpart-Area Name",
        "Counterpart-Area Code",
        "Series Name",
        "Series Code",
    ]
    missing = [c for c in id_columns if c not in raw.columns]
    if missing:
        raise ValueError(f"Required columns missing from raw IDS data: {missing}")

    deduplicated_shape = raw.shape
    raw = raw[raw["Counterpart-Area Code"].fillna("").eq("WLD")].copy()
    raw = raw[raw["Series Name"].fillna("").map(is_relevant_debt_indicator)].copy()

    long_df = raw.melt(
        id_vars=id_columns,
        value_vars=available_years,
        var_name="year",
        value_name="debt_value_usd",
    )
    long_df["debt_value_usd"] = pd.to_numeric(long_df["debt_value_usd"], errors="coerce")
    long_df = long_df.dropna(subset=["debt_value_usd"])
    long_df["year"] = long_df["year"].astype(int)

    country_meta = load_csv(country_meta_path)
    country_meta.columns = [c.strip() for c in country_meta.columns]
    country_meta = strip_text_values(country_meta)
    country_keep = [
        "Code",
        "Region",
        "Income Group",
        "Lending category",
        "Currency Unit",
        "Short Name",
    ]
    country_meta = country_meta[[c for c in country_keep if c in country_meta.columns]].rename(
        columns={
            "Code": "Country Code",
            "Region": "region",
            "Income Group": "income_group",
            "Lending category": "lending_category",
            "Currency Unit": "currency_unit",
            "Short Name": "short_name",
        }
    )

    series_meta = load_csv(series_meta_path)
    series_meta.columns = [c.strip() for c in series_meta.columns]
    series_meta = strip_text_values(series_meta)
    series_keep = ["Code", "Topic", "Source", "Short definition"]
    series_meta = series_meta[[c for c in series_keep if c in series_meta.columns]].rename(
        columns={
            "Code": "Series Code",
            "Topic": "topic",
            "Source": "source",
            "Short definition": "short_definition",
            "Long definition": "long_definition",
        }
    )

    long_df = long_df.merge(country_meta, on="Country Code", how="left")
    long_df = long_df[long_df["region"].notna()].copy()
    long_df = long_df.merge(series_meta, on="Series Code", how="left")

    long_df["measure_type"] = [
        classify_measure(name, code)
        for name, code in zip(long_df["Series Name"], long_df["Series Code"])
    ]
    long_df["value_billions_usd"] = long_df["debt_value_usd"] / 1_000_000_000

    cleaned = long_df.rename(columns={c: snake_case(c) for c in long_df.columns})
    cleaned = cleaned.sort_values(
        ["year", "country_name", "series_name"], kind="stable"
    ).reset_index(drop=True)
    cleaned.insert(0, "debt_id", range(1, len(cleaned) + 1))

    profile = {
        "raw_shape": initial_shape,
        "after_duplicate_removal_shape": deduplicated_shape,
        "filtered_wide_shape": raw.shape,
        "year_start": min(available_years),
        "year_end": max(available_years),
        "cleaned_rows": int(len(cleaned)),
        "countries": int(cleaned["country_code"].nunique()),
        "indicators": int(cleaned["series_code"].nunique()),
        "missing_values_after_cleaning": int(cleaned["debt_value_usd"].isna().sum()),
    }
    return cleaned, profile


def build_dimensions(cleaned: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = (
        cleaned[
            [
                "country_code",
                "country_name",
                "short_name",
                "region",
                "income_group",
                "lending_category",
                "currency_unit",
            ]
        ]
        .drop_duplicates("country_code")
        .sort_values("country_name")
        .reset_index(drop=True)
    )

    indicators = (
        cleaned[
            [
                "series_code",
                "series_name",
                "measure_type",
                "topic",
                "source",
                "short_definition",
            ]
        ]
        .drop_duplicates("series_code")
        .rename(columns={"series_code": "indicator_code", "series_name": "indicator_name"})
        .sort_values("indicator_name")
        .reset_index(drop=True)
    )

    fact = cleaned[
        [
            "debt_id",
            "country_code",
            "series_code",
            "year",
            "debt_value_usd",
            "value_billions_usd",
        ]
    ].rename(columns={"series_code": "indicator_code"})

    return countries, indicators, fact


def build_summaries(cleaned: pd.DataFrame, output_dir: Path, main_year: int) -> dict:
    year_df = cleaned[cleaned["year"].eq(main_year)].copy()
    total_debt = year_df[year_df["series_code"].eq(TOTAL_EXTERNAL_DEBT_CODE)].copy()
    total_debt = total_debt.sort_values("debt_value_usd", ascending=False)

    top_countries = total_debt[
        [
            "country_name",
            "country_code",
            "region",
            "income_group",
            "year",
            "debt_value_usd",
            "value_billions_usd",
        ]
    ].head(20)
    top_countries.to_csv(output_dir / f"top_countries_total_external_debt_{main_year}.csv", index=False)

    indicator_totals = (
        year_df.groupby(["series_code", "series_name", "measure_type"], as_index=False)["debt_value_usd"]
        .sum()
        .assign(value_billions_usd=lambda d: d["debt_value_usd"] / 1_000_000_000)
        .sort_values("debt_value_usd", ascending=False)
    )
    indicator_totals.to_csv(output_dir / f"indicator_totals_{main_year}.csv", index=False)

    region_totals = (
        total_debt.groupby("region", as_index=False)["debt_value_usd"]
        .sum()
        .assign(value_billions_usd=lambda d: d["debt_value_usd"] / 1_000_000_000)
        .sort_values("debt_value_usd", ascending=False)
    )
    region_totals.to_csv(output_dir / f"region_total_external_debt_{main_year}.csv", index=False)

    trend = (
        cleaned[cleaned["series_code"].eq(TOTAL_EXTERNAL_DEBT_CODE)]
        .groupby("year", as_index=False)["debt_value_usd"]
        .sum()
        .assign(value_billions_usd=lambda d: d["debt_value_usd"] / 1_000_000_000)
    )
    trend.to_csv(output_dir / "global_total_external_debt_trend.csv", index=False)

    summary = {
        "main_year": main_year,
        "row_count": int(len(cleaned)),
        "country_count": int(cleaned["country_code"].nunique()),
        "indicator_count": int(cleaned["series_code"].nunique()),
        "total_external_debt_usd": float(total_debt["debt_value_usd"].sum()),
        "total_external_debt_billions_usd": float(total_debt["debt_value_usd"].sum() / 1_000_000_000),
        "top_country": None if total_debt.empty else str(total_debt.iloc[0]["country_name"]),
        "top_country_debt_billions_usd": None
        if total_debt.empty
        else float(total_debt.iloc[0]["value_billions_usd"]),
        "lowest_country": None if total_debt.empty else str(total_debt.iloc[-1]["country_name"]),
        "lowest_country_debt_billions_usd": None
        if total_debt.empty
        else float(total_debt.iloc[-1]["value_billions_usd"]),
        "top_indicator": None if indicator_totals.empty else str(indicator_totals.iloc[0]["series_name"]),
        "top_indicator_billions_usd": None
        if indicator_totals.empty
        else float(indicator_totals.iloc[0]["value_billions_usd"]),
    }
    return summary


def write_outputs(cleaned: pd.DataFrame, profile: dict, output_dir: Path, main_year: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    countries, indicators, fact = build_dimensions(cleaned)

    dashboard_columns = [
        "debt_id",
        "country_code",
        "country_name",
        "short_name",
        "region",
        "income_group",
        "lending_category",
        "series_code",
        "series_name",
        "measure_type",
        "year",
        "debt_value_usd",
        "value_billions_usd",
    ]
    cleaned[dashboard_columns].to_csv(output_dir / "debt_cleaned_long.csv", index=False)
    countries.to_csv(output_dir / "countries.csv", index=False)
    indicators.to_csv(output_dir / "indicators.csv", index=False)
    fact.to_csv(output_dir / "debt_data.csv", index=False)

    summary = build_summaries(cleaned, output_dir, main_year)
    data_quality = {
        **profile,
        "generated_files": [
            "debt_cleaned_long.csv",
            "countries.csv",
            "indicators.csv",
            "debt_data.csv",
            f"top_countries_total_external_debt_{main_year}.csv",
            f"indicator_totals_{main_year}.csv",
            f"region_total_external_debt_{main_year}.csv",
            "global_total_external_debt_trend.csv",
        ],
        "summary": summary,
    }

    with (output_dir / "data_quality_summary.json").open("w", encoding="utf-8") as f:
        json.dump(data_quality, f, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean World Bank IDS data for debt analysis.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2022)
    parser.add_argument("--main-year", type=int, default=2022)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaned, profile = load_and_clean(args.raw_dir, args.start_year, args.end_year)
    write_outputs(cleaned, profile, args.output_dir, args.main_year)
    print(
        f"Processed {len(cleaned):,} rows, "
        f"{cleaned['country_code'].nunique()} countries, "
        f"{cleaned['series_code'].nunique()} indicators."
    )


if __name__ == "__main__":
    main()
