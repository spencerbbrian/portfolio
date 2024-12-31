import boto3

# Create an S3 client
s3 = boto3.client('s3')

# Parameters
bucket_name = 'etl-project-bucket-final'
local_file_path = 'sales_data.csv'
s3_file_name = 'sales_data.csv'

# Upload file
s3.upload_file(local_file_path,bucket_name,s3_file_name)
print(f'{local_file_path} has been uploaded to {bucket_name} as {s3_file_name}')