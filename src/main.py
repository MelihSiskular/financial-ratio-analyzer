import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ---------- SETTINGS ----------
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)

YEARS = ["2022/12", "2023/12", "2024/12", "2025/12"]

DATA_DIR = Path("../Data")
RESULT_DIR = Path("../Result")
RESULT_DIR.mkdir(exist_ok=True)


COMPANIES = {
    "COLA": {
        "file": "Data/COLA.xlsx"
    },
    "FORD": {
        "file": "Data/FORD.xlsx"
    }
}


# ---------- HELPER FUNCTIONS ----------
def clean_number(value):
    """
    Converts Excel values to float.

    Some Excel files may contain numbers as strings with commas or dots.
    This function standardizes them.
    """
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()
    value = value.replace(".", "")
    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return 0.0


def get_value(df, label, year, occurrence=0):
    """
    Finds a financial statement item by its label and returns the value for the selected year.

    Parameters:
        df: DataFrame containing financial statement data.
        label: Row name to search in the 'Bilanço' column.
        year: Column name such as '2024/12'.
        occurrence: Used when the same label appears more than once.
    """
    matches = df.index[df["Bilanço"].astype(str).str.strip() == label].tolist()

    if not matches:
        print(f"Warning: '{label}' not found for {year}. Value set to 0.")
        return 0.0

    if occurrence >= len(matches):
        print(f"Warning: '{label}' occurrence {occurrence} not found. First occurrence used.")
        occurrence = 0

    row_index = matches[occurrence]
    return clean_number(df.loc[row_index, year])


def safe_div(numerator, denominator):
    """
    Prevents division by zero.
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def save_table_as_image(result_df, company_name):
    """
    Saves the result DataFrame as a PNG table.
    """
    fig, ax = plt.subplots(figsize=(16, 4.8))
    ax.axis("off")

    table = ax.table(
        cellText=result_df.values,
        colLabels=result_df.columns,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.5)

    plt.title(f"{company_name} Financial Ratio Analysis", fontsize=14, pad=20)
    plt.tight_layout()

    output_path = RESULT_DIR / f"{company_name}_finansal_oran_tablosu.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"{company_name} table image saved: {output_path}")


# ---------- FINANCIAL ANALYSIS ----------
def analyze_company(company_name, file_path):
    """
    Reads the company's Excel file and calculates financial ratios for all selected years.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_excel(file_path)

    results = []

    for year in YEARS:
        # Balance sheet items
        current_assets = get_value(df, "DÖNEN VARLIKLAR", year)
        current_liabilities = get_value(df, "KISA VADELİ YÜKÜMLÜLÜKLER", year)
        inventories = get_value(df, "Stoklar", year)
        prepaid_expenses = get_value(df, "Peşin Ödenmiş Giderler", year, occurrence=0)

        total_liabilities = get_value(df, "TOPLAM YÜKÜMLÜLÜKLER", year)
        total_equity = get_value(df, "TOPLAM ÖZKAYNAKLAR", year)
        total_assets = get_value(df, "TOPLAM VARLIKLAR", year)

        paid_in_capital = get_value(df, "Ödenmiş Sermaye", year)
        net_income = get_value(df, "Net Dönem Karı veya Zararı", year)
        parent_equity = get_value(df, "Ana Ortaklığa Ait Özkaynaklar", year)

        stock_price = get_value(df, "Yıl Sonu Hisse Fiyatı", year)


        # Ratio calculations
        working_capital = current_assets - current_liabilities

        current_ratio = safe_div(current_assets, current_liabilities)

        quick_assets = current_assets - inventories - prepaid_expenses
        acid_test_ratio = safe_div(quick_assets, current_liabilities)

        net_quick_assets = quick_assets - current_liabilities

        debt_to_equity = safe_div(total_liabilities, total_equity)

        leverage_ratio = safe_div(total_liabilities, total_assets)

        book_value_per_share = safe_div(parent_equity, paid_in_capital)

        earnings_per_share = safe_div(net_income, paid_in_capital)

        price_to_book = safe_div(stock_price, book_value_per_share)

        price_to_earnings = safe_div(stock_price, earnings_per_share)

        roe = safe_div(net_income, parent_equity)




        results.append({
            "Year": year,
            "Working Capital": round(working_capital, 2),
            "Current Ratio": round(current_ratio, 2),
            "Acid-Test": round(acid_test_ratio, 2),
            "Net Quick Assets": round(net_quick_assets, 2),
            "Debt/Equity": round(debt_to_equity, 2),
            "Leverage": round(leverage_ratio, 2),
            "BVPS": round(book_value_per_share, 2),
            "EPS": round(earnings_per_share, 2),
            "P/B": round(price_to_book, 2),
            "P/E": round(price_to_earnings, 2),
            "ROE": round(roe, 2),
            "ROE %": round(roe * 100, 2),
        })

    result_df = pd.DataFrame(results)

    # EPS büyüme oranı
    result_df["EPS Growth %"] = result_df["HB Kar"].pct_change() * 100

    # EPS büyümesi pozitifse PEG hesapla, negatif veya 0 ise boş bırak
    result_df["PEG EPS Growth"] = result_df.apply(
        lambda row: round(row["F/K"] / row["EPS Growth %"], 2)
        if row["EPS Growth %"] > 0 else None,
        axis=1
    )
    result_df["EPS Growth %"] = result_df["EPS Growth %"].round(2)

    print("\n" + "=" * 100)
    print(f"{company_name} FINANCIAL RATIO ANALYSIS")
    print("=" * 100)
    print(result_df)

    save_table_as_image(result_df, company_name)

    return result_df


def export_results_to_excel(all_results):
    """
    Exports all company results into a single Excel file with separate sheets.
    """
    output_path = RESULT_DIR / "finansal_oran_sonuclari.xlsx"

    try:
        with pd.ExcelWriter(output_path) as writer:
            for company_name, result_df in all_results.items():
                result_df.to_excel(writer, sheet_name=company_name, index=False)

        print(f"\nExcel file saved: {output_path}")

    except Exception as error:
        print(f"Error while saving Excel file: {error}")


def main():
    all_results = {}

    for company_name, info in COMPANIES.items():
        result_df = analyze_company(
            company_name=company_name,
            file_path=info["file"]
        )

        all_results[company_name] = result_df

    export_results_to_excel(all_results)


if __name__ == "__main__":
    main()