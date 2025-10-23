import boto3
import datetime
from datetime import timezone # Python timezone library

# Initialize the EC2 client
ec2 = boto3.client('ec2')

# --- CONFIGURATION ---
VOLUME_ID = 'vol-05411a52ead11a820'
RETENTION_DAYS = 30
# ---------------------

def lambda_handler(event, context):
    
    print(f"Starting snapshot process for volume: {VOLUME_ID}")
    
    # --- 1. Create a new snapshot ---
    
    new_snapshot_id = None # Initialize variable
    try:
        # Create a description for the snapshot
        description = f"Lambda_Snapshot_for_{VOLUME_ID}_{datetime.datetime.now().strftime('%Y-%m-%d')}"
        
        response = ec2.create_snapshot(
            VolumeId=VOLUME_ID,
            Description=description,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'BackupType', 'Value': 'Automated'},
                        {'Key': 'CreatedBy', 'Value': 'LambdaEBSBackup'},
                        {'Key': 'SourceVolume', 'Value': VOLUME_ID} # Tag snapshot with its volume ID
                    ]
                }
            ]
        )
        
        new_snapshot_id = response['SnapshotId']
        print(f"Successfully created snapshot: {new_snapshot_id} for volume: {VOLUME_ID}")
        
    except Exception as e:
        print(f"Error creating snapshot for {VOLUME_ID}: {e}")
        # We can still proceed to cleanup even if creation fails

    # --- 2. Clean up old snapshots ---
    
    # Get the current time in UTC (Snapshot StartTime is in UTC)
    now = datetime.datetime.now(timezone.utc)
    
    # Calculate the cutoff date
    cutoff_date = now - datetime.timedelta(days=RETENTION_DAYS)
    print(f"Cleaning up snapshots older than: {cutoff_date}")
    
    deleted_snapshots = []
    
    try:
        # Get all snapshots for the specified volume, owned by you
        paginator = ec2.get_paginator('describe_snapshots')
        pages = paginator.paginate(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'volume-id', 'Values': [VOLUME_ID]}
            ]
        )
        
        for page in pages:
            for snapshot in page['Snapshots']:
                snapshot_id = snapshot['SnapshotId']
                start_time = snapshot['StartTime']
                
                # Compare the snapshot's creation time with the cutoff
                if start_time < cutoff_date:
                    print(f"Found old snapshot to delete: {snapshot_id} (Created: {start_time})")
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        deleted_snapshots.append(snapshot_id)
                        print(f"Successfully deleted snapshot: {snapshot_id}")
                    except Exception as e:
                        print(f"Error deleting snapshot {snapshot_id}: {e}")
                else:
                    print(f"Keeping snapshot: {snapshot_id} (Created: {start_time})")

        print(f"Cleanup complete. Deleted {len(deleted_snapshots)} snapshots.")
        
    except Exception as e:
        print(f"Error describing/deleting snapshots: {e}")

    return {
        'statusCode': 200,
        'body': f'Snapshot action complete. Created: {new_snapshot_id}. Deleted: {deleted_snapshots}'
    }