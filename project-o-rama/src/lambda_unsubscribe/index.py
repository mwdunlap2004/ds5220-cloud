import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ.get('TABLE_NAME', 'WeatherSubscriptions')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        city = body.get('city')
        email = body.get('email')

        if not city or not email:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'city and email are required'})
            }

        # 1. Get record from DynamoDB to get topic_arn
        response = table.get_item(Key={'city': city, 'email': email})
        item = response.get('Item')
        
        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Subscription not found'})
            }

        topic_arn = item.get('topic_arn')

        # 2. Find SNS SubscriptionArn
        subscriptions = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
        sub_arn = None
        for sub in subscriptions.get('Subscriptions', []):
            if sub['Endpoint'] == email:
                sub_arn = sub['SubscriptionArn']
                break
        
        # 3. Unsubscribe if ARN found and not 'PendingConfirmation'
        if sub_arn and sub_arn != 'PendingConfirmation':
            sns.unsubscribe(SubscriptionArn=sub_arn)

        # 4. Delete from DynamoDB
        table.delete_item(Key={'city': city, 'email': email})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Successfully unsubscribed {email} from alerts for {city}.'})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
