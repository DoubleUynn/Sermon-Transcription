from vosk import Model, KaldiRecognizer
import pyaudio

lite_model = Model(r'Sermon-Transcription\vosk-model-small-en-us-0.15')
model = Model(r'Sermon-Transcription\vosk-model-en-us-0.22')
recognizer = KaldiRecognizer(model, 16000)

cap = pyaudio.PyAudio()
stream = cap.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
stream.start_stream()

while True:
    data = stream.read(4096)
    if len(data) == 0:
        break
    if recognizer.AcceptWaveform(data):
        print(recognizer.Result())
    else:
        print(recognizer.PartialResult())