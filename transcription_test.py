from vosk import Model, KaldiRecognizer
# from vosk import BatchModel, BatchRecognizer, Model, KaldiRecognizer, Path, SpkModel, tqdm, ZipFile
import pyaudio

'''
Model - language model
KaldiRecognizer - speech recognition
BatchModel - batch processing
BatchRecognizer -
SpkModel - Speaker Model
tqdm - Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable, but prints a dynamically updating
    progressbar every time a value is requested.
'''
lite_model = Model(r'Sermon-Transcription\vosk-model-small-en-us-0.15')
model = Model(r'Sermon-Transcription\vosk-model-en-us-0.22')
recognizer = KaldiRecognizer(model, 16000)

# read file
with open(r'Sermon-Transcription\audio\hs1_f.wav', 'rb') as f:
    audiof = f.read()

for data in audiof:
    # data = stream.read(4096)
    # if len(data) == 0:
    #     break
    if recognizer.AcceptWaveform(data):
        print(recognizer.Result())
    else:
        print(recognizer.PartialResult())