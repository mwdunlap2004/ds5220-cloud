"""
Demonstrates generating realistic S3 event payloads
using Chalice's built-in test client.

Run with: python sample-object.py
"""

import json
from chalice.test import Client
from app import app


with Client(app) as client:

    # Basic: generate a minimal S3 ObjectCreated event
    basic_event = client.events.generate_s3_event(
        bucket='my-data-bucket',
        key='uploads/report.csv'
    )
    print("=== Basic S3 Event ===")
    print(json.dumps(basic_event.to_dict(), indent=2))

    # With key details: nested path and special characters
    nested_event = client.events.generate_s3_event(
        bucket='my-data-bucket',
        key='users/42/photos/headshot.png'
    )
    print("\n=== Nested Key S3 Event ===")
    print(json.dumps(nested_event.to_dict(), indent=2))

    # Invoke the handler directly and observe the debug log output
    print("\n=== Invoking s3_handler ===")
    event = client.events.generate_s3_event(
        bucket='my-data-bucket',
        key='incoming/data.json'
    )
    client.lambda_.invoke('s3_handler', event)
    print("Handler invoked — check debug log output above.")
