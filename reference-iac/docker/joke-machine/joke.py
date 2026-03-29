import requests
import time

url = 'https://official-joke-api.appspot.com/random_joke'

payload = requests.get(url)
response = payload.json()

setup = response['setup']
punchline = response['punchline']

print(f"{setup}")
time.sleep(3)
print(f"{punchline}")
