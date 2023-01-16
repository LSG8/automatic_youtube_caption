
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
        r.adjust_for_ambient_noise(source, duration=0.1)
        audio = r.record(source)
        print(source.DURATION)
        return audio

def split_audio_with_silence(file):
    audio = AudioSegment.from_file(file, "wav") #change hardcoding
    audio_chunks = split_on_silence(audio, min_silence_len=15, silence_thresh=-43 ) #change hardcoding
    """ This function takes sound as a parameter which is our audio file next it takes min_silence_len by default it is 1000. 
    The minimum length for silent sections is in milliseconds. 
    If it is greater than the length of the audio segment an empty list will be returned. 
    Here we are giving it as 500 milliseconds and silence_thresh by default it is -16. 
    It is the upper bound for how quiet is silent in dBFS. We are giving it as -40. 
    This function returns a list of audio segments. """
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

""" def get_text(response):
    for result in response.result2:
        best_alternative = result.alternatives[0]
        transcript = best_alternative.transcript
        confidence = best_alternative.confidence
        for word_info in best_alternative.words:
            print(word_info.word)
            print(word_info.start_time)
            print(word_info.end_time)
        print("-" * 80)
        print(f"Transcript: {transcript}")
        print(f"Confidence: {confidence:.0%}") """

def translate_text(text):
    translator = Translator()
    try:
        out = translator.translate(text, dest=settings['dest_language'])
        return out.text
    except TypeError:
        print("Type error, check the input")
        return " "
    except translator.raise_exception:
        print("Could not translate this time")
        return " "

def write_to_file(file, text, mode):
    f = open(file, mode, encoding='utf-8')
    f.write(text)
    f.close()



if __name__ == '__main__':
    chunks = split_audio_with_silence(settings['input_audio'])
    for audio_split in chunks:
        print(len(audio_split))
        output_file = "../output/chunk.wav" #change hardcoding
        audio_split.export(output_file, format="wav")
        audio = read_audio(output_file)
        transcript = get_transcript(audio)
        translation = translate_text(transcript)
        print(translation)
        print("-" * 80)
    #write_to_file(settings['output_transcript'],translation.text, "w+")