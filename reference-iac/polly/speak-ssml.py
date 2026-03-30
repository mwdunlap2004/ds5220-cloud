import boto3

polly = boto3.client("polly")

ssml_text = """
<speak>
    <prosody rate="medium" pitch="low">
        Welcome to Amazon Polly, a text-to-speech service powered by deep learning.
    </prosody>
    <break time="500ms"/>
    Today, we will demonstrate several features of SSML markup,
    including pauses, emphasis, and pronunciation.
    <break time="300ms"/>
    <p>
        For example, the word
        <phoneme alphabet="ipa" ph="ˌɒnəˌmætəˈpiːə">onomatopoeia</phoneme>
        is notoriously difficult to pronounce.
        Similarly, <phoneme alphabet="ipa" ph="ˌsʌpərˌkælɪˌfrædʒɪˌlɪstɪkˌɛkspiˌælɪˈdoʊʃəs">supercalifragilisticexpialidocious</phoneme>
        is a mouthful, to say the least.
    </p>
    <break time="400ms"/>
    <p>
        Now, let me speak <emphasis level="strong">very clearly</emphasis>:
        SSML gives you fine-grained control over speech output.
    </p>
    <break time="300ms"/>
    <p>
        <prosody rate="fast">
            I can speak quickly when the situation demands it,
        </prosody>
        <break time="200ms"/>
        <prosody rate="slow">
            or I can slow things down for dramatic effect.
        </prosody>
    </p>
    <break time="500ms"/>
    <prosody volume="soft">
        And finally, I can whisper a quiet goodbye.
    </prosody>
</speak>
"""

response = polly.synthesize_speech(
    TextType="ssml",
    Text=ssml_text,
    OutputFormat="mp3",
    VoiceId="Joanna",
)

with open("output-ssml.mp3", "wb") as f:
    f.write(response["AudioStream"].read())

print("SSML audio saved to output-ssml.mp3")
