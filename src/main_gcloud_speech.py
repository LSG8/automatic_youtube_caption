
import sys
import io
from os import path
from googletrans import Translator
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_leading_silence, detect_nonsilent, detect_silence

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
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code=settings['source_language'],
        #enable_automatic_punctuation=True,
        audio_channel_count=int(settings['channel_count']),
        #enable_word_time_offsets=True,
    )
    try:
        #operation = client.long_running_recognize(config=config, audio=audio)
        #response = operation.result(timeout=1000)
        response = client.recognize(config=config, audio=audio)

        for result in response.results:
            alternative = result.alternatives[0]
            """ for word_info in alternative.words:
                word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                print(
                    f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}"
                ) """
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
    audio = speech.RecognitionAudio(uri='gs://speech_to_text_storage_bucket/Speech_files/speech_short.wav')
    chunks = split_audio_with_silence(audio) #example chunks: [[30075,34567],[34678,56789],[64389,78906]]
    for audio_time_range in chunks:
        long_transcript = get_long_transcript(audio_time_range, audio) #example audio_time_range: [30075,34567]
        translated_long_text = translate_text_write(long_transcript, audio_time_range)