'''
This script converts mp3 files to wav files.
Directly from Konstantin Rink on Medium: https://towardsdatascience.com/transcribe-large-audio-files-offline-with-vosk-a77ee8f7aa28
'''

from pydub import AudioSegment
import ffmpeg
# import avconv
import os

def mp3_to_wav(source, skip=0, excerpt=False):
    
    print(os.path.exists(source))
    sound = AudioSegment.from_mp3(source) # load source
    sound = sound.set_channels(1) # mono
    sound = sound.set_frame_rate(16000) # 16000Hz
    
    if excerpt:
        excrept = sound[skip*1000:skip*1000+30000] # 30 seconds - Does not work anymore when using skip
        output_path = os.path.splitext(source)[0]+"_converted.wav"
        excrept.export(output_path, format="wav")
    else:
        audio = sound[skip*1000:]
        output_path = os.path.splitext(source)[0]+".wav"
        audio.export(output_path, format="wav")
    
    return output_path

# ⚠️ TESTING ⚠️
mp3 = r'audio/mp3/ignoring_signs.mp3'
chan = r'audio/mp3/francis_chan.mp3'
wav = r'audio/wav/hs1_f.wav'

bob = mp3_to_wav(chan, skip=0, excerpt=True)
# print(bob)