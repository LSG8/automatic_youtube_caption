
import sys
import io
from os import path
from googletrans import Translator
from pydub import AudioSegment
from pydub.silence import split_on_silence

from google.oauth2 import service_account
from google.cloud import speech

sys.path.append('../')
sys.path.append('../audio_examples')
sys.path.append('../output')

from helper import helper_config

config = helper_config.read_config()
settings = config['SETTINGS']
credentials = service_account.Credentials.from_service_account_file(settings['gcloud_credentials'])
client = speech.SpeechClient(credentials=credentials)

def read_audio(file):
    with io.open(file, "rb") as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        return audio

def split_audio_with_silence(file):
    audio = AudioSegment.from_file(file, settings['in_format'])
    audio_chunks = split_on_silence(audio, min_silence_len=int(settings['stop_time']), silence_thresh= int(settings['silence_thresh']))
    return list(filter(lambda x : len(x) > 1000, audio_chunks))


def get_transcript(audio):
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code=settings['source_language'],
        enable_automatic_punctuation=True,
        audio_channel_count=int(settings['channel_count']),
        #enable_word_time_offsets=True,
    )
    try:
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            alternative = result.alternatives[0]
            for word_info in alternative.words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                print(
                    f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}"
                )
            return alternative.transcript
    except Exception as e:
        print("Google Cloud Speech to Text failed due to {}".format(e))
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
        return " "
    except translator.raise_exception:
        print("Could not translate this time")
        return " "

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
    chunks = split_audio_with_silence(settings['input_audio'])
    time_start = 0
    for audio_split in chunks:
        duration = len(audio_split)/1000
        #print(len(audio_split))
        output_file = settings['output_split']
        audio_split.export(output_file, format= settings['proc_format'])
        audio = read_audio(output_file)
        transcript = get_transcript(audio)
        translation = translate_text_write(transcript, time_start, time_start+duration)
        time_start = time_start + duration
        #print(translation)
        #print("-" * 80) 