import pandas as pd

file_path = 'downloaded_sales_data.csv'
df = pd.read_csv(file_path)

# Transform the data
df['order_date'] = pd.to_datetime(df['order_date'], format="%Y-%m-%d")
df = df[df['price'] > 50]

# Save the transformed data
transformed_file_path = 'transformed_sales_data.csv'
df.to_csv(transformed_file_path, index=False)
print(f'Transformed data saved to {transformed_file_path}')