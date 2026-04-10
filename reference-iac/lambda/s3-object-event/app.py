import os
import boto3
from chalice import Chalice

app = Chalice(app_name='s3-object-event')
app.debug = True

# Set the value of BUCKET_NAME in the .chalice/config.json file.
S3_BUCKET = os.environ.get('BUCKET_NAME', '')

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('s3-linecount')


@app.on_s3_event(bucket=S3_BUCKET, events=['s3:ObjectCreated:*'])
def s3_handler(event):
    app.log.debug("Received event for bucket: %s, key: %s",
                  event.bucket, event.key)

    response = s3_client.get_object(Bucket=event.bucket, Key=event.key)
    body = response['Body'].read().decode('utf-8')
    line_count = len(body.splitlines())

    table.put_item(
        Item={
            'fileid': event.key,
            'line_count': line_count,
        }
    )

    app.log.debug("Wrote %d lines for %s to s3-linecount table",
                  line_count, event.key)
