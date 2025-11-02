import sys
import pandas as pd

"""
Usage:
  python scripts/profile_csv.py <path_to_csv>
Prints columns, sample rows, and basic stats to help map to the project schema.
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/profile_csv.py <path_to_csv>")
        sys.exit(1)

    path = sys.argv[1]
    df = pd.read_csv(path, nrows=5000)

    print("\n=== File:", path, "===")
    print("Rows (previewed):", len(df))
    print("\nColumns:")
    for i, c in enumerate(df.columns, 1):
        print(f"  {i}. {c}")

    print("\nHead:")
    print(df.head(5).to_string(index=False))

    print("\nNon-null counts:")
    print(df.count().sort_values(ascending=False).to_string())

    print("\nNumeric columns summary:")
    print(df.select_dtypes(include='number').describe().transpose().to_string())

if __name__ == "__main__":
    main()
