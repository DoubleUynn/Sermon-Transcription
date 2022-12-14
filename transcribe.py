'''
This program transcribes audio using the Vosk API, then adds punctuation and capitalization using the recasepunc package.
'''
import os
import wave
import json
from glob import glob
from vosk import Model, KaldiRecognizer
from recasepunc.recasepunc import CasePuncPredictor
from recasepunc.recasepunc import WordpieceTokenizer
from recasepunc.recasepunc import Config

def transcribe(modelpath, audio_file_directory):
    '''
    Transcribes audio from each file in audio_file_directory and saves the results to a text file in the 'transcriptions' folder.
    Adapted from Konstantin Rink on Medium:
    https://towardsdatascience.com/transcribe-large-audio-files-offline-with-vosk-a77ee8f7aa28
    '''
    # Initialize model
    model = Model(modelpath)
    # Loop through audio files
    for file in audio_file_directory:
        title = os.path.basename(file)
        print (f"Transcribing {title}...")
        # open audio file
        wf = wave.open(file, "rb")
        # Initialize recognizer
        rec = KaldiRecognizer(model, wf.getframerate())
        # store results in a list
        transcription = []
        #rec.SetWords(True)
        while True:
            data = wf.readframes(4000)
            # break the loop if there is no more audio
            if len(data) == 0:
                break
            # if there is audio, pass it to the recognizer
            if rec.AcceptWaveform(data):
                # Convert json output to dict
                result_dict = json.loads(rec.Result())
                # Extract text values and append them to transcription list
                transcription.append(result_dict.get("text", ""))
        # Get final bits of audio and flush the pipeline
        final_result = json.loads(rec.FinalResult())
        transcription.append(final_result.get("text", ""))
        # merge or join all list elements to one big string
        transcription = " ".join(transcription)

        # Parse string into a list of sentences
        transcription = add_punctuation('transcriptions', r'models/en.23000', transcription)
        transcription = transcription.split('.')

        # Write to file with each sentence on a new line
        with open(f'transcriptions/{title.split(".")[0]}.txt', 'w') as f:
            for sentence in transcription:
                f.write(f"{sentence.strip()}\n")
            

def add_punctuation(destination_path, checkpoint_path, text):
    '''
    This function adds punctuation and corrects casing to the text string.
    Adapted from Daniel Krezdorn's code at https://codeberg.org/codade/SpeechToTextGUI
    '''
    try:
        casePunc_predictor = CasePuncPredictor(checkpoint_path, flavor='bert-base-uncased', lang='en')
        # self.logMsg("Adjusting punctuation and casing for:{}".format(audiofile))

        tokens = list(enumerate(casePunc_predictor.tokenize(text)))

        #Process every character of finalText string and correct punctuation and casing
        resultsCasepunc = ""
        for token, case_label, punc_label in casePunc_predictor.predict(tokens, lambda x: x[1]):
            prediction = casePunc_predictor.map_punc_label(casePunc_predictor.map_case_label(token[1], case_label), punc_label)
            if token[1][0] != '#':
                resultsCasepunc = resultsCasepunc + ' ' + prediction
            else:
                resultsCasepunc = resultsCasepunc + prediction
        return resultsCasepunc.strip()
    except Exception as e:
        # throw error
        print("Error while trying to predict recognition and correct casing. Output raw text file", e)
        return text

# Language model paths
lite_model = r'models/vosk-model-small-en-us-0.15'
big_model = r'models/vosk-model-en-us-0.22'

# Get audio files from audio folder
# audio_files = glob(r'audio/wav/*.wav')
sermon_audio = glob(r'audio/*.wav')

# Run the program
if __name__ == '__main__':
    transcribe(big_model, sermon_audio)