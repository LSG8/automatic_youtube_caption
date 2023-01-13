
import sys
import speech_recognition as sr
from os import path
from googletrans import Translator

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
        r.adjust_for_ambient_noise(source, duration=0.1)
        audio = r.record(source)
        return audio

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

def translate_text(text):
    translator = Translator()
    out = translator.translate(text, dest=settings['dest_language'])
    return out

def write_to_file(file, text, mode):
    f = open(file, mode, encoding='utf-8')
    f.write(text)
    f.close()



if __name__ == '__main__':
    audio = read_audio(settings['input_audio'])
    transcript = get_transcript(audio)
    translation = translate_text(transcript)
    print(translation.text)
    write_to_file(settings['output_transcript'],translation.text, "w+")