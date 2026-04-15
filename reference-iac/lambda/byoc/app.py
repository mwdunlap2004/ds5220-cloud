import boto3

def handler(event, context):
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()['Buckets']
    bucket_list = [
        {"Name": b["Name"], "CreationDate": b["CreationDate"].isoformat()}
        for b in buckets
    ]
    return {"statusCode": 200, "buckets": bucket_list}
