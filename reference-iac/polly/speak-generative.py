import boto3

polly = boto3.client("polly")

text = """
Picture this: you're standing at the edge of the Grand Canyon at sunrise.
The first rays of light spill over the rim, painting the ancient rock layers
in shades of amber, crimson, and gold. A cool breeze carries the faint
sound of the Colorado River far below. You take a deep breath, and for
a moment, the sheer scale of it all makes the rest of the world feel
wonderfully small.
"""

response = polly.synthesize_speech(
    Text=text.strip(),
    OutputFormat="mp3",
    VoiceId="Ruth",
    Engine="generative",
)

with open("output-generative.mp3", "wb") as f:
    f.write(response["AudioStream"].read())

print("Generative audio saved to output-generative.mp3")
