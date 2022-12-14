import os
import spacy
from glob import glob

from recasepunc.recasepunc import CasePuncPredictor
from recasepunc.recasepunc import WordpieceTokenizer
from recasepunc.recasepunc import Config

def spacy_punctuation(text):
    nlp = spacy.load('en_core_web_sm')
    text_sentences = nlp(text)
    for sentence in text_sentences.sents:
        print(sentence.text)

def add_punctuation(destination_path, checkpoint_path, finalText):
    '''
    This function adds punctuation and corrects casing to the finalText string.
    Adapted from codade at https://codeberg.org/codade/SpeechToTextGUI
    '''
    try:
        casePunc_predictor = CasePuncPredictor(checkpoint_path, flavor='bert-base-uncased', lang='en')
        # self.logMsg("Adjusting punctuation and casing for:{}".format(audiofile))

        tokens = list(enumerate(casePunc_predictor.tokenize(finalText)))

        #Process every character of finalText string and correct punctuation and casing
        resultsCasepunc = ""
        for token, case_label, punc_label in casePunc_predictor.predict(tokens, lambda x: x[1]):
            prediction = casePunc_predictor.map_punc_label(casePunc_predictor.map_case_label(token[1], case_label), punc_label)
            if token[1][0] != '#':
                resultsCasepunc = resultsCasepunc + ' ' + prediction
            else:
                resultsCasepunc = resultsCasepunc + prediction

        # write finalText string to a file
        with open(destination_path +'_punc.txt', 'w') as output:
            output.write(resultsCasepunc.strip())
            print("Finished exporting text file with punctuation and case recognition:{}".format(destination_path + '_punc.txt'))
    except Exception as e:
        # throw error
        print("Error while trying to predict recognition and correct casing. Output raw text file", e)
        # write finalText string without punctuation correction to a file
        with open(destination_path +'_nopunc.txt', 'w') as output:
            output.write(finalText)
    except Exception as e:
        e.throw("Speech to text recognition failed. Please see the logs for more information", e)
    return

# for file in glob(r'transcriptions/*.txt'):
#     # Write to file
#     with open(f'transcriptions/{title}.txt', 'w') as f:
#         f.write(f"{transcription}\n")
#     with open(file, 'r') as f:
#         txt = f.read()
#         spacy_punctuation(txt)

# ⚠️ TESTING ⚠️
checkpoint = r'models/en.23000'

for file in glob(r'transcriptions/*.txt'):
    title = os.path.basename(file)
    with open(file, 'r') as f:
        txt = f.read()
        add_punctuation('transcriptions/' + title, checkpoint, txt)