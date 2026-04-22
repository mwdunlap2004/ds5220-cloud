import boto3
from chalice import Chalice

app = Chalice(app_name='ec2-timer')
app.debug = True

ec2 = boto3.client('ec2')

def timer_instances():
    # get all instances tagged with "business_hours_only=True"
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:business_hours_only', 'Values': ['True']},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
    )
    instance_ids = [
        instance['InstanceId']
        for reservation in response['Reservations']
        for instance in reservation['Instances']
    ]
    return instance_ids

@app.schedule('cron(48 13 ? * MON-FRI *)')
def turn_on(event):
    instances = timer_instances()
    ec2.start_instances(InstanceIds=instances)
    return True

@app.schedule('cron(01 14 ? * MON-FRI *)')
def turn_off(event):
    instances = timer_instances()
    ec2.stop_instances(InstanceIds=instances)
    return True

# @app.lambda_function()
# def first_function(event, context):
#     return {'hello': 'world'}

