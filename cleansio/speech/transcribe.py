""" Convert audio to text using Google Cloud Speech """

from itertools import repeat
from multiprocessing.dummy import Pool as ThreadPool
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from utils import append_before_ext

class Transcribe():
    """ Transcribes the lyrics from the vocals """
    def __init__(self, file_path, frame_rate, encoding='LINEAR16'):
        super().__init__()
        self.lyrics = self.__transcribe_chunks(encoding, frame_rate, file_path)

    def __transcribe_chunks(self, frame_rate, encoding, file_path):
        file_paths = [file_path, append_before_ext(file_path, '-overlapping')]
        async_iter = zip(repeat(frame_rate), repeat(encoding), file_paths)
        transcripts = ThreadPool(2).map(self.__transcribe_chunk, async_iter)
        return self.__combine_transcripts(transcripts)

    def __transcribe_chunk(self, async_iter):
        """ Accesses Google Cloud Speech and print the lyrics for each chunk """
        frame_rate, encoding, file_path = async_iter
        accuracy_chunk_path = append_before_ext(file_path, '-accuracy')
        with open(accuracy_chunk_path, 'rb') as audio_content:
            content = audio_content.read()
        config = self.__get_config(encoding, frame_rate)
        audio = types.RecognitionAudio(content=content)
        return speech.SpeechClient().recognize(config = config, audio = audio)

    @classmethod
    def __get_config(cls, frame_rate, encoding):
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            # sample_rate_hertz=frame_rate,
            language_code="id-ID",
            enable_word_time_offsets=True,
            profanity_filter=False,
            max_alternatives=1,
        )

        return config

    @classmethod
    def __combine_transcripts(cls, transcripts):
        """ Combine the words from the normal and overlapping chunks """
        words = []
        if transcripts[0].results: # Normal chunk
            words += transcripts[0].results[0].alternatives[0].words
        if transcripts[1].results: # Overlapping chunk
            overlapping = transcripts[1].results[0].alternatives[0].words
            shifted_time = list(map(cls.__shift_time, overlapping))
            words += shifted_time
        return None if words == [] else words

    @classmethod
    def __shift_time(cls, word):
        """ Increment the time relative to the normal chunk """
        word.start_time.seconds += 2
        word.start_time.nanos += 500000000
        word.end_time.seconds += 2
        word.end_time.nanos += 500000000
        return word
