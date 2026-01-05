import pandas as pd

load_file = "data_local/evalueringsdata_v2.csv"
save_file = load_file.replace('.csv', '_med_titler.csv')
evalueringsdata = pd.read_csv(load_file)
db25_struktur = pd.read_csv("data_local/db25_struktur.csv")

# Map branchekode til branchekode: titel
kode_kodetitel_mapping = {
    row["kode"]: f"{row['kode']}: {row['titel']}"
    for _, row in db25_struktur.iterrows()
}

# Function to format and map codes in the 'brancheforslag' column
def transform_codes(codes):
    """
    Reformat incorrectly structured codes to match the xx.yy.zz format,
    then map them to their corresponding titles.
    """
    # Convert string representation of a list to a Python list
    codes_list = eval(codes)
    formatted_codes = []
    
    for code in codes_list:
        # Reformat the code to xx.yy.zz structure
        formatted_code = f"{code[:2]}.{code[2:4]}.{code[4:6]}"
        # Map code to "formatted_code: title", or "Unknown" if not found
        mapped_code = kode_kodetitel_mapping.get(formatted_code, f"{formatted_code}: Unknown")
        formatted_codes.append(mapped_code)
    
    return formatted_codes

# Apply the transformation to create a new column
evalueringsdata["brancheforslag med titler"] = evalueringsdata["brancheforslag"].apply(transform_codes)

unknown_count = evalueringsdata["brancheforslag med titler"].apply(
    lambda x: sum("Unknown" in item for item in x)  # Check each item in the list for 'Unknown'
).sum()
print(f"In evalueringsdata_med_titler er der {unknown_count} 'Unknown' .")

evalueringsdata.to_csv(save_file, index=False)

print(f"Evalueringsdata med titler gemt til {save_file}.")