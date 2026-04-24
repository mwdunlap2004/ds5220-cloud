import json
import boto3
import os
import urllib.request
import urllib.parse

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ.get('TABLE_NAME', 'WeatherSubscriptions')
table = dynamodb.Table(TABLE_NAME)

def get_weather(city):
    try:
        # Step 1: Geocode
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        with urllib.request.urlopen(geo_url) as response:
            geo_data = json.loads(response.read().decode())
        
        if not geo_data.get('results'):
            return None
        
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        
        # Step 2: Fetch weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=True&temperature_unit=fahrenheit"
        with urllib.request.urlopen(weather_url) as response:
            weather_data = json.loads(response.read().decode())
        
        return weather_data.get('current_weather')
    except Exception as e:
        print(f"Error fetching weather for {city}: {e}")
        return None

def handler(event, context):
    try:
        # 1. Scan for all subscriptions
        response = table.scan()
        subscriptions = response.get('Items', [])
        
        # 2. Group by city to minimize API calls
        city_groups = {}
        for sub in subscriptions:
            city = sub['city']
            if city not in city_groups:
                city_groups[city] = []
            city_groups[city].append(sub)
            
        # 3. Check weather for each city
        for city, subs in city_groups.items():
            weather = get_weather(city)
            if not weather:
                continue
                
            temp = weather.get('temperature')
            condition_code = weather.get('weathercode')
            
            # Simple threshold check: 
            # If temp > ANY subscriber's threshold, alert the topic
            # Or if it's a thunderstorm (code 95, 96, 99)
            
            thresholds = [float(s.get('threshold_temp', 95)) for s in subs]
            min_threshold = min(thresholds) if thresholds else 95
            
            is_hot = temp >= min_threshold
            is_stormy = condition_code in [95, 96, 99]
            
            if is_hot or is_stormy:
                topic_arn = subs[0].get('topic_arn')
                if not topic_arn:
                    continue
                
                message = f"Weather Alert for {city}!\n"
                message += f"Current Temperature: {temp}F\n"
                if is_hot:
                    message += f"Status: Temperature has exceeded the threshold of {min_threshold}F.\n"
                if is_stormy:
                    message += f"Status: Severe weather/thunderstorms detected.\n"
                
                sns.publish(
                    TopicArn=topic_arn,
                    Subject=f"Weather Alert: {city}",
                    Message=message
                )
                print(f"Published alert for {city}")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Weather check completed'})
        }

    except Exception as e:
        print(f"Error in weather checker: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
