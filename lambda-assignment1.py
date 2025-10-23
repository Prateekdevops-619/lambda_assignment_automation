import boto3

# Initialize the EC2 client
ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    
    # --- 1. Handle Auto-Stop Instances ---
    
    # Define the filter for 'Auto-Stop' tags and 'running' state
    stop_filter = [
        {'Name': 'tag:Action', 'Values': ['Auto-Stop']},
        {'Name': 'instance-state-name', 'Values': ['running']} 
    ]
    
    # Find all instances matching the filter
    stop_instances = ec2.describe_instances(Filters=stop_filter)
    
    stop_list = []
    
    # Loop through the reservations and instances to get their IDs
    for reservation in stop_instances['Reservations']:
        for instance in reservation['Instances']:
            stop_list.append(instance['InstanceId'])
            
    # Stop the instances if any were found
    if stop_list:
        print(f"Stopping instances: {stop_list}")
        ec2.stop_instances(InstanceIds=stop_list)
    else:
        print("No running instances found with tag 'Auto-Stop'.")

    # --- 2. Handle Auto-Start Instances ---
    
    # Define the filter for 'Auto-Start' tags and 'stopped' state
    start_filter = [
        {'Name': 'tag:Action', 'Values': ['Auto-Start']},
        {'Name': 'instance-state-name', 'Values': ['stopped']} 
    ]
    
    # Find all instances matching the filter
    start_instances = ec2.describe_instances(Filters=start_filter)
    
    start_list = []
    
    # Loop through the reservations and instances to get their IDs
    for reservation in start_instances['Reservations']:
        for instance in reservation['Instances']:
            start_list.append(instance['InstanceId'])
            
    # Start the instances if any were found
    if start_list:
        print(f"Starting instances: {start_list}")
        ec2.start_instances(InstanceIds=start_list)
    else:
        print("No stopped instances found with tag 'Auto-Start'.")

    return {
        'statusCode': 200,
        'body': 'EC2 instance state management complete.'
    }