import json
import boto3
import re
import os

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ.get('TABLE_NAME', 'WeatherSubscriptions')
table = dynamodb.Table(TABLE_NAME)

def sanitize_topic_name(city):
    # SNS topic names can only contain alphanumeric characters, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', city)
    return f"WeatherAlert_{sanitized}"

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        city = body.get('city')
        email = body.get('email')
        threshold_temp = body.get('threshold_temp', 95) # Default 95F

        if not city or not email:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'city and email are required'})
            }

        # 1. Create/Get SNS Topic
        topic_name = sanitize_topic_name(city)
        topic_response = sns.create_topic(Name=topic_name)
        topic_arn = topic_response['TopicArn']

        # 2. Subscribe email to topic
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )

        # 3. Store in DynamoDB
        table.put_item(
            Item={
                'city': city,
                'email': email,
                'threshold_temp': threshold_temp,
                'topic_arn': topic_arn
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully subscribed {email} to alerts for {city}. Please check your email to confirm.',
                'topic_arn': topic_arn
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
