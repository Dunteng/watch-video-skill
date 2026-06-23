from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.media import FfmpegClient


class RecordingFfmpegClient(FfmpegClient):
    def __init__(self):
        super().__init__()
        self.ppm_timestamps = []
        self.saved_frames = []

    def extract_ppm(self, video_path, timestamp_seconds):
        self.ppm_timestamps.append(timestamp_seconds)
        return b"P6\n2 1\n255\n" + bytes([0, 0, 0, 255, 255, 255])

    def extract_frame(self, video_path, timestamp_seconds, output_path):
        self.saved_frames.append((timestamp_seconds, output_path))
        output_path.write_bytes(b"jpg")


class MediaTests(unittest.TestCase):
    def test_extract_keyframes_stops_at_max_keyframes(self):
        client = RecordingFfmpegClient()

        with TemporaryDirectory() as tmp:
            frames = client.extract_keyframes(
                video_path=Path("video.mp4"),
                output_dir=Path(tmp) / "keyframes",
                duration_seconds=50.0,
                interval_seconds=10.0,
                max_keyframes=2,
            )

        self.assertEqual(len(frames), 2)
        self.assertEqual(len(client.saved_frames), 2)
        self.assertEqual(len(client.ppm_timestamps), 6)
        self.assertEqual(frames[0].path.name, "frame_0001.jpg")
        self.assertEqual(frames[1].path.name, "frame_0002.jpg")


if __name__ == "__main__":
    unittest.main()
