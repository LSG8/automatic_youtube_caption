
import sys
import speech_recognition as sr
from os import path
from googletrans import Translator

sys.path.append('../helper')
sys.path.append('../audio_examples')
sys.path.append('../output')
from helper import helper_config
#from helper import helper_config as input_settings
#import helper.helper_config as input_settings

r = sr.Recognizer()

def read_audio(file):
    with file as source:
        r.adjust_for_ambient_noise(source, duration=0.1)
        audio = r.record(source)  # read the entire audio file
        return audio

def get_transcript(audio):
    try:
        text = r.recognize_google(audio, language = "bn")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return ""

def translate_text(text):
    translator = Translator()
    out = translator.translate(text, dest='en')
    return out



if __name__ == '__main__':
    print("Hello")
    config = helper_config.read_config()
    settings = config['SETTINGS']
    print(settings['input_audio'])
    print(settings['output_transcript'])
    print(settings['source_language'])
    print(settings['dest_language'])
