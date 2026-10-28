
import pandas as pd

# STEP 1: EXTRACT
df = pd.read_csv("data/raw/orders.csv", sep="\t")

print("Dataset:")
print(df)

# STEP 2: DATA QUALITY CHECKS

print("\n--- DATA QUALITY REPORT ---")

# Check missing values
print("\nMissing values:")
print(df.isnull().sum())

# Check for duplicate orders
print("\nDuplicate orders:")
print(df[df.duplicated(subset=["order_id"], keep=False)])

# Check negative prices
print("\nNegative prices:")
print(df[df["price"] < 0])

# Check invalid quantities
print("\nInvalid quantities (zero or less):")
print(df[df["quantity"] <= 0])
