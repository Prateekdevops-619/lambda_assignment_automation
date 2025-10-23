import boto3
from botocore.exceptions import ClientError

# Initialize the S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    unencrypted_buckets = []
    
    # 1. List all S3 buckets
    response = s3.list_buckets()
    
    print("Starting scan of S3 buckets for encryption...")
    
    # 2. Iterate through each bucket
    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        
        try:
            # 3. Check for server-side encryption
            # This call will retrieve the encryption configuration
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            
            # If the call succeeds, encryption rules exist.
            rules = encryption['ServerSideEncryptionConfiguration']['Rules']
            print(f"Bucket '{bucket_name}': [ENCRYPTED]. Rule: {rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']}")
            
        except ClientError as e:
            # 4. If ClientError 'ServerSideEncryptionConfigurationNotFoundError' occurs,
            # it means no encryption rules are set. This is what we're looking for.
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                print(f"!!! Bucket '{bucket_name}': [UNENCRYPTED]. No default encryption configured.")
                unencrypted_buckets.append(bucket_name)
            else:
                # Handle other potential errors (e.g., permissions)
                print(f"Error checking {bucket_name}: {e}")

    # 5. Print the final list for logging
    if unencrypted_buckets:
        print(f"Scan complete. Unencrypted buckets found: {unencrypted_buckets}")
    else:
        print("Scan complete. All buckets have server-side encryption configured.")

    return {
        'statusCode': 200,
        'body': f'Scan complete. Found {len(unencrypted_buckets)} unencrypted buckets.'
    }
