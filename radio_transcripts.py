import pyaudio
import wave
import requests
import json
import subprocess
import os
from configure import auth_key
from datetime import datetime 

DATE = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 60
WAV_OUTPUT_FILENAME = "audio_output.wav"
p = pyaudio.PyAudio()
 
# starts recording
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

print("* recording")

frames = []

for i in range(0, int(RATE / FRAMES_PER_BUFFER * RECORD_SECONDS)):
    data = stream.read(FRAMES_PER_BUFFER)
    frames.append(data)

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAV_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

bashCommand = "sox audio_output.wav audio_output_processed_.mp3 silence 1 0.5 1% 1 5.0 1% : newfile : restart"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()

prefixed = [filename for filename in os.listdir('.') if filename.startswith("audio_output_processed")]
    
for item in prefixed:
    print(item)
    #for later use
    json = {"webhook_url": "https://foo.bar/your-webhook-url"}
    headers = {"authorization": auth_key, "content-type": "application/json"}

    def read_file(filename):
       with open(filename, 'rb') as _file:
           while True:
               data = _file.read(5242880)
               if not data:
                   break
               yield data
    
    upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=read_file(prefixed))
    audio_url = upload_response.json()['upload_url']

    transcript_request = {'audio_url': audio_url}
    endpoint = "https://api.assemblyai.com/v2/transcript"
    transcript_response = requests.post(endpoint, json=transcript_request, headers=headers)
    _id = transcript_response.json()['id']

    endpoint = "https://api.assemblyai.com/v2/transcript/" + _id
    polling_response = requests.get(endpoint, headers=headers)
    if polling_response.json()['status'] != 'completed':
       print(polling_response.json())
    else:
       with open(_id + '.txt', 'w') as f:
           f.write(polling_response.json()['text'])
       print('Transcript saved to', _id, '.txt')