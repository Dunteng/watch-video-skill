from __future__ import annotations

from pathlib import Path

from .commands import CommandError
from .downloader import YtDlpClient
from .media import FfmpegClient
from .models import AnalysisReport, Source, SubtitleCue
from .ocr import TesseractOcr
from .sources import classify_source
from .subtitles import collect_subtitle_files, cues_to_plain_text, load_subtitle_file
from .transcription import WhisperCppTranscriber, WhisperTranscriber


class VideoAnalyzer:
    def __init__(
        self,
        downloader: YtDlpClient | None = None,
        media_client: FfmpegClient | None = None,
        transcriber: WhisperTranscriber | None = None,
        whisper_cpp_transcriber: WhisperCppTranscriber | None = None,
        ocr_engine: TesseractOcr | None = None,
    ):
        self.downloader = downloader or YtDlpClient()
        self.media_client = media_client or FfmpegClient()
        self.transcriber = transcriber or WhisperTranscriber()
        self.whisper_cpp_transcriber = whisper_cpp_transcriber or WhisperCppTranscriber()
        self.ocr_engine = ocr_engine or TesseractOcr(enabled=True)

    def analyze(
        self,
        source_value: str,
        output_dir: Path,
        subtitle_languages: list[str] | None = None,
        max_height: int | None = 1080,
        keyframe_interval: float = 10.0,
        max_keyframes: int | None = None,
        language: str | None = None,
        enable_ocr: bool = False,
    ) -> AnalysisReport:
        # 编排边界：这里负责调度各阶段，不把下载/转写/抽帧细节写在一起。
        source = classify_source(source_value)
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []

        video_path, subtitle_files = self._prepare_source(
            source=source,
            output_dir=output_dir,
            subtitle_languages=subtitle_languages or ["zh.*", "en.*"],
            max_height=max_height,
            warnings=warnings,
        )

        media = self.media_client.probe(video_path)
        transcript_cues = self._load_or_transcribe(
            video_path=video_path,
            output_dir=output_dir,
            subtitle_files=subtitle_files,
            language=language,
            warnings=warnings,
        )
        keyframes = self.media_client.extract_keyframes(
            video_path=video_path,
            output_dir=output_dir / "keyframes",
            duration_seconds=media.duration_seconds,
            interval_seconds=keyframe_interval,
            max_keyframes=max_keyframes,
        )
        ocr_results = self.ocr_engine.extract(keyframes, warnings) if enable_ocr else []

        return AnalysisReport(
            source=source,
            work_dir=output_dir,
            video_path=video_path,
            media=media,
            transcript_cues=transcript_cues,
            transcript_text=cues_to_plain_text(transcript_cues),
            keyframes=keyframes,
            ocr_results=ocr_results,
            subtitle_files=subtitle_files,
            warnings=warnings,
        )

    def _prepare_source(
        self,
        source: Source,
        output_dir: Path,
        subtitle_languages: list[str],
        max_height: int | None,
        warnings: list[str],
    ) -> tuple[Path, list[Path]]:
        if source.kind == "file":
            assert source.path is not None
            return source.path, collect_subtitle_files(source.path.parent, stem=source.path.stem)

        subtitle_files: list[Path] = []
        subtitles_dir = output_dir / "subtitles"
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        try:
            subtitle_files = self.downloader.fetch_subtitles(
                source.value,
                subtitles_dir,
                subtitle_languages,
            )
        except (CommandError, FileNotFoundError, OSError) as exc:
            warnings.append(f"字幕下载失败，后续会尝试语音转写: {exc}")

        video_path = self.downloader.fetch_remote(
            source.value,
            output_dir / "video",
            max_height=max_height,
        )
        return video_path, subtitle_files

    def _load_or_transcribe(
        self,
        video_path: Path,
        output_dir: Path,
        subtitle_files: list[Path],
        language: str | None,
        warnings: list[str],
    ) -> list[SubtitleCue]:
        for subtitle_file in subtitle_files:
            cues = load_subtitle_file(subtitle_file)
            if cues:
                return cues

        try:
            cues = self.transcriber.transcribe(
                video_path=video_path,
                output_dir=output_dir / "transcript",
                language=language,
            )
        except (CommandError, FileNotFoundError, OSError) as exc:
            warnings.append(f"语音转写失败: {exc}")
            cues = []

        if cues:
            return cues

        unavailable_reason = getattr(self.whisper_cpp_transcriber, "unavailable_reason", lambda: None)
        reason = unavailable_reason()
        if reason:
            warnings.append(reason)
            cues = []
        else:
            try:
                cues = self.whisper_cpp_transcriber.transcribe(
                    video_path=video_path,
                    output_dir=output_dir / "transcript",
                    language=language,
                )
            except (CommandError, FileNotFoundError, OSError) as exc:
                warnings.append(f"whisper.cpp 转写失败: {exc}")
                cues = []

        if not cues:
            warnings.append("没有可用字幕，且本机未检测到可用 Whisper 转写结果")
        return cues
