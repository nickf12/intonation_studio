import os
from ffprobe import FFProbe
from audio import GoogleSpeaker, AudioAnalyst
from image import ImageMaker
from utils import path_in_medialib
import ffmpeg


class VideoMaker:
    TARGET_EXTENSION = '.mp4'

    @staticmethod
    def get_meta(video_path):
        metadata = FFProbe(video_path)
        return metadata

    @classmethod
    def from_text(cls, text, videopath=None, rate=0.4):
        speaker = GoogleSpeaker()
        audio_filepath = speaker.speak(text, rate)
        if not videopath:
            basename = os.path.splitext(os.path.basename(audio_filepath))[0]
            filename = f'{basename}{cls.TARGET_EXTENSION}'
            video_path = path_in_medialib(filename)
        analyst = AudioAnalyst(audio_filepath, text)
        analysis = analyst.analyse()
        image_maker = ImageMaker(analysis)
        pattern = image_maker.save_images()
        outdict = {
            'vcodec': 'h264',
            'shortest': None
        }
        image = ffmpeg.input(pattern)
        audio = ffmpeg.input(audio_filepath)

        try:
            ffmpeg.output(image, audio, video_path, **outdict).run(
                capture_stdout=True,
                capture_stderr=True
            )
            return videopath
        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise e

    @staticmethod
    def pitch_video_from_audio(filename, text=None):
        wav_file = path_in_medialib(filename)
        analyst = AudioAnalyst(wav_file, text)
        analysis = analyst.analyse()
        image_maker = ImageMaker(analysis)
        pattern = image_maker.save_images()
        outdict = {
            'vcodec': 'h264',
            'shortest': None
        }
        image = ffmpeg.input(pattern)
        audio = ffmpeg.input(wav_file)
        video_path = f"{wav_file}.mp4"
        try:
            ffmpeg.output(image, audio, video_path, **outdict).run(
                capture_stdout=True,
                capture_stderr=True
            )
        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise e
