import boto3
import datetime
from datetime import timezone

# Initialize the S3 client
s3 = boto3.client('s3')

# --- CONFIGURATION ---

BUCKET_NAME = 'lambda-cleanup-test-prateek-123'
RETENTION_DAYS = 30
# ---------------------

def lambda_handler(event, context):
    
    # Get the current time in UTC (S3 LastModified is in UTC)
    now = datetime.datetime.now(timezone.utc)
    
    # Calculate the cutoff date
    cutoff_date = now - datetime.timedelta(days=RETENTION_DAYS)
    
    print(f"Connecting to bucket: {BUCKET_NAME}")
    print(f"Current time: {now}")
    print(f"Cutoff date (deleting files older than this): {cutoff_date}")
    
    objects_to_delete = []
    
    # Use a paginator to handle buckets with many (1000+) objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET_NAME)
    
    try:
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Compare the object's last modified time with the cutoff
                    if obj['LastModified'] < cutoff_date:
                        objects_to_delete.append({'Key': obj['Key']})
                        
        if not objects_to_delete:
            print(f"No objects found older than {RETENTION_DAYS} days. No action taken.")
            return {'statusCode': 200, 'body': 'No old files to delete.'}

        # S3 delete_objects can only handle 1000 keys at a time
        # We must "chunk" the list into batches of 1000
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i + 1000]
            print(f"Deleting batch of {len(batch)} objects...")
            
            response = s3.delete_objects(
                Bucket=BUCKET_NAME,
                Delete={'Objects': batch}
            )
            
            # Log deleted keys
            deleted_keys = [obj['Key'] for obj in response.get('Deleted', [])]
            print(f"Successfully deleted: {deleted_keys}")
            
            # Log any errors
            if 'Errors' in response:
                for error in response['Errors']:
                    print(f"Error deleting {error['Key']}: {error['Message']}")

        return {
            'statusCode': 200,
            'body': f'Deleted {len(objects_to_delete)} objects.'
        }
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return {'statusCode': 500, 'body': str(e)}