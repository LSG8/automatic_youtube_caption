
import sys
import speech_recognition as sr
from os import path
from googletrans import Translator
from pydub import AudioSegment
from pydub.silence import split_on_silence

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
        r.adjust_for_ambient_noise(source, duration= float(settings['offset_time']))
        audio = r.record(source)
        return audio

def split_audio_with_silence(file):
    audio = AudioSegment.from_file(file, settings['in_format'])
    audio_chunks = split_on_silence(audio, min_silence_len=int(settings['stop_time']), silence_thresh= int(settings['silence_thresh']) )
    return list(filter(lambda x : len(x) > 1000, audio_chunks))

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

def translate_text_write(text, time_start, time_end):
    translator = Translator()
    try:
        out = translator.translate(text, dest=settings['dest_language'])
        caption = write_text(out.text, time_start, time_end)
        write_to_file(settings['output_transcript'],caption, "a+")
        return 0
    except TypeError:
        print("Type error, check the input")
        return 0
    except translator.raise_exception:
        print("Could not translate this time")
        return 0

def write_text(text, time_start, time_end):
    caption = "{},{}\n{}\n\n".format(convert(time_start),convert(time_end),text)
    return caption

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return '%d:%02d:%0.3f' % (hour, min, sec)

def write_to_file(file, text, mode):
    f = open(file, mode, encoding='utf-8')
    f.write(text)
    f.close()

if __name__ == '__main__':
    #print("start working")
    chunks = split_audio_with_silence(settings['input_audio'])
    time_start = 0
    for audio_split in chunks:
        duration = len(audio_split)/1000
        output_file = settings['output_split']
        audio_split.export(output_file, format=settings['proc_format'])
        audio = read_audio(output_file)
        transcript = get_transcript(audio)
        translate_text_write(transcript, time_start, time_start+duration)
        time_start = time_start + duration
        #print("-" * 80)