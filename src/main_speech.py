
import sys
import numpy as np
import speech_recognition as sr
from os import path
from googletrans import Translator
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_leading_silence, detect_nonsilent, detect_silence

sys.path.append('../')
sys.path.append('../audio_examples')
sys.path.append('../output')

from helper import helper_config

r = sr.Recognizer()
config = helper_config.read_config()
settings = config['SETTINGS']

def read_audio(file):
    audio_file = sr.AudioFile(file)
    with audio_file as source:
        audio = r.record(source)
        return audio

def split_audio_with_silence(audio):
    speeches = detect_nonsilent(audio, min_silence_len=int(settings['stop_time']), silence_thresh= int(settings['silence_thresh']), seek_step=1)
    return speeches

def get_long_transcript(time_range, audio):#example time_range: [30075,34567]
    speeches = break_into_small_parts(time_range, audio)#example speeches: [[30075,31567],[31567,34567]]
    long_text = ""
    for speech in speeches:##example speech: [30075,31567]
        new_range = list(map(lambda x:x+time_range[0], speech))
        split_audio_with_time(new_range, audio)
        small_audio = read_audio(settings['output_split'])
        long_text = long_text + " " + get_transcript(small_audio)
    return long_text

def break_into_small_parts(speeches, audio):#example speeches: [30075,34567]
    """ duration = speeches[1] - speeches[0]
    if duration >= 60000:
        #break into parts
        #np.linspace(speeches[0], speeches[1], num=-(duration/-60000), endpoint=True)

        return single_minute_speeches #example speeches: [[30075,31567],[31567,34567]]
    else:
        return list(speeches) """
    return detect_nonsilent(audio[speeches[0]:speeches[1]], min_silence_len=150, silence_thresh= -25, seek_step=1)

def split_audio_with_time(time_range, audio):
    newAudio = audio[time_range[0]:time_range[1]]
    newAudio.export(settings['output_split'], format=settings['proc_format'])
    return 0

def get_transcript(audio):
    try:
        text = r.recognize_google(audio, language = settings['source_language'])
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return ""

def translate_text_write(text, time_range):
    translator = Translator()
    try:
        out = translator.translate(text, dest=settings['dest_language'])
        caption = write_text(out.text, time_range)
        write_to_file(settings['output_transcript'],caption, "a+")
        return 0
    except TypeError:
        print("Type error, check the input")
        return 0
    except translator.raise_exception:
        print("Could not translate this time")
        return 0

def write_text(text, time_range):
    caption = "{},{}\n{}\n\n".format(convert(time_range[0]),convert(time_range[1]),text)
    return caption

def convert(ms):
    seconds = ms/1000
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return '%d:%02d:%0.3f' % (hour, min, sec)

def write_to_file(file, text, mode):
    f = open(file, mode, encoding='utf-8')
    f.write(text)
    f.close()

if __name__ == '__main__':
    audio = AudioSegment.from_file(settings['input_audio'], settings['in_format'])
    chunks = split_audio_with_silence(audio) #example chunks: [[30075,34567],[34678,56789],[64389,78906]]
    for audio_time_range in chunks:
        long_transcript = get_long_transcript(audio_time_range, audio) #example audio_time_range: [30075,34567]
        translated_long_text = translate_text_write(long_transcript, audio_time_range)