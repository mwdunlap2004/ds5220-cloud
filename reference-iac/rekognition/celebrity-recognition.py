import boto3
import json
import sys

image_file_name = sys.argv[1]

rek = boto3.client('rekognition')

with open(image_file_name, 'rb') as image_file:
    image_bytes = image_file.read()

response = rek.recognize_celebrities(
    Image={'Bytes': image_bytes}
)

print(json.dumps(response, indent=2, default=str))
