import boto3

# Create an S3 client
s3 = boto3.client('s3')

# Parameters
bucket_name = 'etl-project-bucket-final'
s3_file_name = 'sales_data.csv'
download_path = 'downloaded_sales_data.csv'

# Download the file
s3.download_file(bucket_name, s3_file_name, download_path)
print('File downloaded successfully')