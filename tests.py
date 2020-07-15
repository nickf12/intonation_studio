import unittest
import os.path

import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram

from image import ImageMaker
from utils import path_in_medialib, augmented_dendrogram
from audio import GoogleSpeaker, AudioAnalyst
from video import VideoMaker

TEST_SENTENCE = 'Intonation Studio'
JSON_FILE = 'test1.json'
VIDEO_FILE = 'test1.mp4'
WAV_FILE = 'test1'


class TestGoogleSpeaker(unittest.TestCase):

    def test_speak_correct(self):
        speaker = GoogleSpeaker()
        filepath = speaker.speak(TEST_SENTENCE, filename=WAV_FILE)
        assert(os.path.exists(filepath))


class TestAudioAnalyst(unittest.TestCase):

    def test_clustering(self):
        """
        Hierachical clustering analysis
        """
        plt.clf()
        filepath = path_in_medialib(f'{WAV_FILE}.wav')
        analyst1 = AudioAnalyst(filepath, TEST_SENTENCE)
        analyst1.analyse()
        clusters = analyst1.cluster()
        augmented_dendrogram(clusters.astype(float))
        plt.savefig(path_in_medialib('test_dendogram.svg'), format='svg')

    def test_analysis(self):
        """
        Test parametrization
        """
        plt.clf()
        filepath = path_in_medialib(f'{WAV_FILE}.wav')
        # not subsampled 86 sample per second
        analyst1 = AudioAnalyst(
            filepath, 'Processing 86 / s',
            samplerate=44100
        )
        # subsampled 25 samples per second
        analyst2 = AudioAnalyst(filepath, TEST_SENTENCE)
        # 15 seconds per second
        analyst3 = AudioAnalyst(
            filepath, 'Processing 15 / s',
            samplerate=15360, hop=1024,
        )
        # subsampled 10 samples per second
        analyst4 = AudioAnalyst(
            filepath, 'Processing 10 / s',
            samplerate=22050, hop=1024
        )

        analyst1.analyse()
        analyst2.analyse()
        analyst3.analyse()
        analyst4.analyse()

        axs = plt.subplots(4, 2)[1]
        analyst1.plot_samples(axs[0][0])
        analyst1.plot_histogram(axs[0][1])
        analyst2.plot_samples(axs[1][0])
        analyst2.plot_histogram(axs[1][1])
        analyst3.plot_samples(axs[2][0])
        analyst3.plot_histogram(axs[2][1])
        analyst4.plot_samples(axs[3][0])
        analyst4.plot_histogram(axs[3][1])
        plt.savefig(path_in_medialib('test_analyst.svg'), format='svg')


class TestImageMaker(unittest.TestCase):

    def setUp(self):
        filepath = path_in_medialib(f'{WAV_FILE}.wav')
        self.analysis = AudioAnalyst(filepath, TEST_SENTENCE).analyse()

    def test_make_images(self):
        generator = ImageMaker(self.analysis)
        images = generator.make_images()
        images[0].write_to_png(path_in_medialib('test_cairo_frame_0.jpg'))
        images[4].write_to_png(path_in_medialib('test_cairo_frame_4.jpg'))

    @unittest.SkipTest
    def test_cairo_save_images(self):
        """
        Test the frame generation to be used by the Video Maker
        """
        generator = ImageMaker(self.analysis)
        generator.cairo_save_images()


class TestVideoMaker(unittest.TestCase):

    @unittest.SkipTest
    def test_meta_video(self):
        metadata = VideoMaker.get_meta(path_in_medialib(VIDEO_FILE))
        return metadata

    def test_from_text(self):
        """
        Temporary entry point of the software
        """
        videopath = VideoMaker.from_text(TEST_SENTENCE)
        self.assertTrue(os.path.exists(videopath))


if __name__ == '__main__':
    unittest.main()
