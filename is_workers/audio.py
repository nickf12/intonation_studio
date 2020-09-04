import os
import json

from aubio import source, pitch
from google.cloud import texttospeech
from google.oauth2 import service_account
import ffmpeg
import numpy as np
from scipy.cluster.hierarchy import linkage

from utils import path_in_medialib, NoteTools


class GoogleSpeaker:
    FILENAME_MAX_CHARS = 40
    FILENAME_EXTENSION = 'mp3'
    DEFAULT_CREDENTIAL_FILEPATH = \
        "/Users/elio/projects/writersup/credentials.json"
    default_credentials = None

    def __init__(self):
        credential_filepath = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not credential_filepath or not os.path.exists(credential_filepath):
            self.default_credentials = \
                service_account.Credentials.from_service_account_file(
                    self.DEFAULT_CREDENTIAL_FILEPATH)
        self.client = texttospeech.TextToSpeechClient() \
            if not self.default_credentials \
            else texttospeech.TextToSpeechClient(
                    credentials=self.default_credentials
                )

    @staticmethod
    def mp3_to_wav(mp3_path, wav_path):
        try:
            mp3 = ffmpeg.input(mp3_path)
            outdict = {
                'acodec': 'pcm_u8',
            }
            ffmpeg.output(mp3, wav_path, **outdict).run(
                capture_stdout=True,
                capture_stderr=True
            )
        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise e

    def filename_from_text(self, text, language_code, speak_rate):
        out = text.replace(" ", "_").lower()
        out = out[:self.FILENAME_MAX_CHARS] \
            if self.FILENAME_MAX_CHARS < len(out) else out
        out = f"{out}_{language_code}_{str(speak_rate).replace('.','_')}"
        return out

    def speak(
        self,
        text,
        rate=0.8,
        language='en-US',
        filename=None,
        voice_name='en-US-Wavenet-D'
    ):
        """
        Create the audio file from text.
        """
        if not filename:
            filename = self.filename_from_text(text, rate, language)
        filepath = path_in_medialib(filename)
        filepath_wav = f'{filepath}.wav'
        filepath_mp3 = f'{filepath}.mp3'
        if os.path.exists(filepath_wav):
            return filepath_wav
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice_name
        )
        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=rate
        )
        # voice parameters and audio file type
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        # The response's audio_content is binary.
        with open(filepath_mp3, "wb") as out:
            out.write(response.audio_content)
        self.mp3_to_wav(filepath_mp3, filepath_wav)
        return filepath_wav


class AudioAnalyst:
    debug = True
    hop = 512  # downsample # hop size
    downsample = 1
    win_s = 4096  # downsample # fft size
    tolerance = 0.8
    silence = -40
    clean = False
    clean_tollerance = 0.35
    clean_value = -1.0
    analysis = None

    def __init__(
        self,
        filename,
        title,
        unit='midi',
        method='yin',
        samplerate=12800,
        hop=512,
        win_s=4096
    ):
        """
        Default values  128000 / 512 = 25 sample per second.
        """
        self.filename = filename
        self.title = title
        self.unit = unit
        self.hop = hop
        self.win_s = win_s
        # Support to frequency not completed and never used
        self.is_midi = self.unit == 'midi'
        self.method = method
        self.samplerate = samplerate
        self.s = source(filename, self.samplerate, self.hop)
        self.pitch_o = pitch(
            self.method, self.win_s, self.hop, self.samplerate
        )
        self.pitch_o.set_unit(self.unit)
        self.pitch_o.set_silence(self.silence)
        self.pitch_o.set_tolerance(self.tolerance)

    def plot_samples(self, plot):
        times = [t * self.hop for t in range(len(self.samples))]
        plot.plot(times, self.samples, '.-')
        plot.axis(ymin=0.0, ymax=1.1 * self.max_y)

    def plot_histogram(self, plot):
        plot.hist(self.histogram)

    def save_file(self, filepath):
        with open(filepath) as json_file:
            json.dump(self.analysis, json_file)

    def cluster(self):
        """
        Create clusters using hierarchical clustering
        """
        zeros = np.zeros(len(self.samples))
        points = np.column_stack(
            (zeros.astype(np.double), self.samples.astype(np.double))
        )
        self.linkage = linkage(points, 'ward')
        return self.linkage

    def set_analysis(self, samples):
        """
        Set samples and compute stats
        """
        self.samples = samples
        self.max_x = self.samples.size
        self.min_y = np.min(self.samples)
        self.max_y = np.max(self.samples)
        self.histogram = np.histogram(
            self.samples,
            bins=int(self.max_y)
        )
        if not self.is_midi:
            self.max_note, self.min_note = NoteTools.freq_to_note(
                self.max_y), \
                NoteTools.freq_to_note(self.min_y)
        else:
            self.max_note, self.min_note = NoteTools.midi_to_note(
                self.max_y), \
                NoteTools.midi_to_note(self.min_y)

        self.analysis = {
                'samples': self.samples.tolist(),
                'tolerance': self.tolerance,
                'silence': str(self.silence),
                'hop': str(self.hop),
                'filename': self.filename,
                'samplerate': self.samplerate,
                'max_x': self.max_x,
                'min_y': self.min_y,
                'max_y': self.max_y,
                'max_note': self.max_note,
                'min_note': self.min_note,
                'histogram': self.histogram,
                'unit': self.unit,
                'title': self.title
        }
        return self.analysis

    def analyse(self, json_path=None):
        total_frames = 0
        pitches = []
        confidences = []
        while True:
            samples, read = self.s()
            pitch = self.pitch_o(samples)[0]
            confidence = self.pitch_o.get_confidence()
            if self.clean and confidence < self.clean_tollerance:
                pitch = self.clean_value
            pitches += [pitch]
            confidences += [confidence]
            total_frames += read
            if read < self.hop:
                break
        # clean results
        pitches = np.array(pitches)
        pitches = np.ma.masked_where(
            pitches <= 12.0,
            pitches
        )
        # save and return analysis
        return self.set_analysis(pitches)
