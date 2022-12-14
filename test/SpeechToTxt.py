'''
Copyright 2021 SingerLinks Consulting LLC 

This file is part of AudioText.
AudioText is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
AudioText is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
You should have received a copy of the GNU General Public License
    along with AudioText. If not, see <https://www.gnu.org/licenses/>.

Modified by Daniel Krezdorn to integrate punctuation and case recognition and renamed to SpeechToTxt. 
Wav recognition was tightend and restricted to create a mono-wav file in any case. See the original file for more wav options. 
Moreover multiple file selection and processing was enabled.
Punctuation models based on Bert introduced by Benoit Favre: https://github.com/benob/recasepunc
Trained german punctuation model can be found on https://alphacephei.com/vosk/models/vosk-recasepunc-de-0.21.zip offered on Apache 2.0

Make sure to select the checkpoint directory before running the conversion
'''
import os
import datetime
import audioop
import wave
import json
import sys
import subprocess
import time

from vosk import Model, KaldiRecognizer

import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog as fd 

from transformers import logging
from voskRecasepunc.recasepunc import CasePuncPredictor
from voskRecasepunc.recasepunc import WordpieceTokenizer
from voskRecasepunc.recasepunc import Config


class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)        
        self.master = master
        self.useCasepunc = tk.IntVar(value=1)
        self.casepuncLang = tk.IntVar(value=1)
        self.casepuncLangDict = {1:'de',2:'en',3:'fr',4:'pt'}

        # if running the compiled version then tell pydub where the ffmpeg exe is found.
        if getattr(sys, 'frozen', False):
            this_script_dir = os.path.dirname(path.realpath(__file__))
            os.environ["PATH"] += os.pathsep + this_script_dir + '\\ffmpeg'
        
        # menu system
        menu = Menu(self.master)
        self.master.config(menu=menu)
        fileMenu = Menu(menu)
        fileMenu.add_command(label="Select Audio Recognition Model", command=self.openAudioModelPath)
        fileMenu.add_command(label="Select Checkpoint file", command=self.openRecasePuncCheckptPath)
        fileMenu.add_command(label="Select Audio File(s)", command=self.openAudioFiles)
        fileMenu.add_command(label="Exit", command=self.exitProgram)
        menu.add_cascade(label="File", menu=fileMenu)

        # speech recognition model file controls
        self.lbl0 = Label(self, text="Audio Recognition Model", font= ('Helvetica', 18, 'bold'))
        self.lbl0.place(x = 5,y = 0)
        self.lbl1 = Label(self, text="Model Path:")
        self.lbl1.place(x = 10,y = 30)
        self.audioModelPath = tk.StringVar(value=os.path.expanduser('~')) #define your default if not home directory
        self.txtBoxPath = Label(self, textvariable = self.audioModelPath)
        self.txtBoxPath.place(x=90, y = 30)

        # punctuation and recasing trained checkpoint file controls
        self.lbl2 = Label(self, text="Punction and Recasing Model", font= ('Helvetica', 18, 'bold'))
        self.lbl2.place(x=5,y = 60)
        self.lbl3 = Label(self, text="Checkpoint Filepath:")
        self.lbl3.place(x=10,y = 90)
        self.checkpointPath = os.path.expanduser('~')
        self.chkptPathVar = tk.StringVar(value=self.checkpointPath) #define your default if not home directory
        self.txtBoxPath = Label(self, textvariable = self.chkptPathVar)
        self.txtBoxPath.place(x=90, y = 90)
        
        # input file controls
        self.lbl4 = Label(self, text="Input Audio File", font= ('Helvetica', 18, 'bold'))
        self.lbl4.place(x=5,y=120)
        self.lbl5 = Label(self, text="File Name(s):")
        self.lbl5.place(x=10,y=160)
        self.audioFileNames = tk.StringVar()
        self.txtBoxName = Label(self, textvariable = self.audioFileNames,anchor="e", justify='left')
        self.txtBoxName.place(x=10, y = 180)

        
        # buttons
        ##Checkbutton for Casepunc and Language Choice
        self.lbl7 = Label(self, text="Use Punction and Recasing Model", font= ('Helvetica', 16, 'bold'))
        self.lbl7.place(x=5,y=260)
        self.checkCasePunc = Checkbutton(master, text="", variable=self.useCasepunc)
        self.checkCasePunc.place(x=450,y=260)

        self.lbl8 = Label(self,text="Choose language for recasing and punctuation:")
        self.lbl8.place(x=10,y=300)

        for val, txt in self.casepuncLangDict.items():
            Radiobutton(self, text=txt,padx=10, variable=self.casepuncLang, value=val).place(x=60*(val-1),y=320)

        self.btnConvertText = Button(root, text = 'Convert To Text', bd = '5',  command = self.convertText)
        self.btnConvertText.place(x=10, y=350)
        
        # text area
        self.frmTxt = Frame(root, height = 20, width = 70)
        self.frmTxt.pack(side=LEFT)
        self.frmTxt.place(x=10, y=410)
        
        self.vsb = Scrollbar ( self.frmTxt, orient='vertical' )
        self.vsb.pack( side = RIGHT, fill = Y )        
        self.txtLog = Text(self.frmTxt, height = 20, width = 70, yscrollcommand = self.vsb.set)
        self.txtLog.pack(side=LEFT, fill=Y)
        self.vsb.config( command = self.txtLog.yview )
        
        
        # widget can take all window
        self.pack(fill=BOTH, expand=1)
        
    def exitProgram(self):
        exit()

    def openAudioModelPath(self):
        'select path to audio recognition model'
        name= fd.askdirectory()
        self.audioModelPath.set(name)

    def openRecasePuncCheckptPath(self):
        'select folder with checkpoint file for punctuation'
        name = fd.askdirectory()
        self.checkpointPath = name 
        self.chkptPathVar.set(name)
        
    def openAudioFiles(self):
        'open audio files'
        filenames = fd.askopenfilenames(filetypes =[('Audio file', '*.WAV *.wav *.mp3 *.MP3')], initialdir = '/home/dogomil/Nextcloud/Blog-Buch/Blog/Diktaterkennung/') 
        stringFilenames = ',\n'.join(filenames)
        self.audioFileNames.set(stringFilenames)

    def logMsg(self, msg):
        ct = datetime.datetime.now()
        self.txtLog.insert(END, str(ct) + ": " + msg + "\n")
        self.txtLog.see(END)
        Tk.update_idletasks(self)

    def clearLog(self):
        self.txtLog.delete(0.0, END)
        
    def convertText(self):
            self.logMsg("Start Text Conversion")
            self.clearLog()
            self.processFiles()
            self.logMsg("Text Conversion Processing Complete")

    def convert_monowav(self, filename):

        try:
            # open the input and create mono output files
            inFile = wave.open(filename,'rb')
            monoWav = filename[:-4] + "_Mono" + '.wav' #get file path, extend it with mono and *.wav
            outFile = wave.open(monoWav,'wb')
            # force mono
            outFile.setnchannels(1)
            # set output file like the input file
            outFile.setsampwidth(inFile.getsampwidth())
            outFile.setframerate(inFile.getframerate())
            # read
            soundBytes = inFile.readframes(inFile.getnframes())
            print("frames read: {} length: {}".format(inFile.getnframes(),len(soundBytes)))
            # convert to mono and write file
            monoSoundBytes = audioop.tomono(soundBytes, inFile.getsampwidth(), 1, 1)
            outFile.writeframes(monoSoundBytes)
            self.logMsg("Finished exporting Mono WAV file:{}".format(monoWav))
            self.audioFiles.append(monoWav)

        except Exception as e:

            messagebox.showinfo("Error Converting WAV stereo To WAV Mono", e)
            return
            
        finally:
            #reset filename
            inFile.close()
            outFile.close()
            
    def processFiles(self):
        '''
        this method converts the audio file to text.  This is a three step process:
        1. convert wav file to mono file
        2. Process the mono wave or mp3 file and create json text files
        3. Build finalText string from created json and start punctuation model
        4. Process characters of final string with recasepunc model to correct punctuation and casing 
        '''
        self.logMsg("Start Text Conversion")
        
        if  self.audioFileNames.get() == '':
            messagebox.showinfo("AudioText", "No audio files selected. Select an Audio File.")
            return
            
        if self.audioModelPath.get() == "":
            messagebox.showinfo("AudioText", "No model file selected. Select a model path.")
            return         
        
        
        self.audioFiles = []
        #loop through audio files and convert wav files if existent:
        for audiofile in self.audioFileNames.get().split(',\n'):

            if audiofile[-4:] in ['.WAV', '.wav']:
                self.convert_monowav(audiofile)
                #mono Wav file is appended if transformation was successful

            elif audiofile[-4:] in ['.MP3', '.mp3']:
                #add mp3 to output dict
                self.audioFiles.append(audiofile)

            else:
                pass

        # convert audio text
        try:

            self.logMsg("convert Audio files to text")


            # build the models and recognizer objects.
            self.logMsg("Build language model (this takes some time).")
            vosk_model = Model(self.audioModelPath.get())
            self.logMsg("Start recognizer.")

            if self.useCasepunc.get():
                try:
                    self.logMsg("Loading punctuation and recasing recognition model. This might take some time")

                    #get chosen language to be used for punctuation
                    chosenLang = self.casepuncLangDict[self.casepuncLang.get()]
                    casePunc_predictor = CasePuncPredictor(self.checkpointPath+'/checkpoint', lang=chosenLang)
                except Exception as e:
                    messagebox.showinfo("Error while trying to load recognition and recasing model. Output raw text file", e)
                    self.useCasepunc.set(0)

            #loop through audio files:
            for audiofile in self.audioFiles:


                # initialize a str to hold results
                results = []
                textResults = []

                self.logMsg("Starting audio recognition for:{}".format(audiofile))

                audioPath = audiofile[:-4]
                audioExt = audiofile[-4:]

                if audioExt == '.wav':  
                    #process wav file
                    self.logMsg("Open Mono WAV file.")
                    wf = wave.open(audiofile, "rb")
                    recognizer = KaldiRecognizer(vosk_model, wf.getframerate())
                    recognizer.SetWords(True)

                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        if recognizer.AcceptWaveform(data):
                            recognizerResult = recognizer.Result()
                            # convert the recognizerResult string into a dictionary  
                            resultDict = json.loads(recognizerResult)
                            # save the entire dictionary in the list
                            results.append(resultDict)
                            # save the 'text' value from the dictionary into a list
                            textResults.append(resultDict.get("text", ""))
                            self.logMsg(resultDict.get("text", ""))
                    
                    #delete converted wave file after completion
                    os.remove(audiofile)


                else:
                    #Read mp3 file with ffmpeg decoder
                    sample_rate=16000
                    recognizer = KaldiRecognizer(vosk_model, sample_rate)      

                    #open subprocess for mp3 audio recognition
                    process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                                audiofile,
                                                '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                                                stdout=subprocess.PIPE)
                    while True:
                        data = process.stdout.read(4000)
                        if len(data) == 0:
                            break
                        if recognizer.AcceptWaveform(data):
                            recognizerResult = recognizer.Result()
                            # convert the recognizerResult string into a dictionary  
                            resultDict = json.loads(recognizerResult)
                            # save the entire dictionary in the list
                            results.append(resultDict)
                            # save the 'text' value from the dictionary into a list
                            textResults.append(resultDict.get("text", ""))
                            self.logMsg(resultDict.get("text", ""))

                    
                # process "final" result
                resultDict = json.loads(recognizer.FinalResult())
                results.append(resultDict)
                textResults.append(resultDict.get("text", ""))
                finalText = ' '.join(textResults)


                # Proceed with case Recognition and Punctuation if ticked
                if self.useCasepunc.get():
                    try:
                        self.logMsg("Adjusting punctuation and casing for:{}".format(audiofile))


                        tokens = list(enumerate(casePunc_predictor.tokenize(finalText)))

                        #Process every character of finalText string and correct punctuation and casing
                        resultsCasepunc = ""
                        for token, case_label, punc_label in casePunc_predictor.predict(tokens, lambda x: x[1]):
                            self.logMsg('Word: '+token[1]+' | Case Label: '+ case_label + ' | Punc Label: '+ punc_label)
                            prediction = casePunc_predictor.map_punc_label(casePunc_predictor.map_case_label(token[1], case_label), punc_label)
                            if token[1][0] != '#':
                               resultsCasepunc = resultsCasepunc + ' ' + prediction
                            else:
                               resultsCasepunc = resultsCasepunc + prediction

                        # write finalText string to a file
                        print('Casepunc finished')
                        print(audioPath)
                        with open(audioPath +'.txt', 'w') as output:
                            output.write(resultsCasepunc.strip())
                            self.logMsg("Finished exporting text file with punctuation and case recognition:{}".format(audioPath + '.txt'))
                    except Exception as e:
                        messagebox.showinfo("Error while trying to predict recognition and correct casing. Output raw text file", e)
                        # write finalText string without punctuation correction to a file
                        with open(audioPath +'_nopunc.txt', 'w') as output:
                            output.write(finalText)
                            self.logMsg("Finished exporting raw text file:{}".format(audioPath + '_nopunc.txt'))
                     
                else:
                    # write finalText string without punctuation correction to a file
                    with open(audioPath +'_nopunc.txt', 'w') as output:
                        output.write(finalText)
                        self.logMsg("Finished exporting raw text file:{}".format(audioPath + '_nopunc.txt'))

                #JSON export currently turned off
                # # write results to a file
                # with open(audioPath + "_Results.json", 'w') as output:
                #     print(json.dumps(results, indent=4), file=output)
                #     self.logMsg("Finished exporting json results file:{}".format(audioPath + "_Results.json"))

                # # write text portion of results to a file
                # with open(audioPath + "_Text.json", 'w') as output:
                #     print(json.dumps(textResults, indent=4), file=output)
                #     self.logMsg("Finished exporting json text file:{}".format(audioPath + "_Text.json"))
                

        except Exception as e:
            messagebox.showinfo("Speech to text recognition failed. Please see the logs for more information", e)
            return
                    
        
        
root = Tk()
app = Window(root)
root.wm_title("SpeechtoText")
root.geometry("600x800")
root.mainloop()