import boto3

polly = boto3.client("polly")

response = polly.synthesize_speech(
    Text="A man a plan a canal panama",
    OutputFormat="mp3",
    VoiceId="Joanna",
)

with open("output.mp3", "wb") as f:
    f.write(response["AudioStream"].read())

print("Audio saved to output.mp3")
