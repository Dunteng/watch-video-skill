import unittest

from watchvideo.processes import (
    ProcessInfo,
    find_watchvideo_processes,
    parse_ps_output,
    render_process_report,
    scan_processes,
)


class ProcessTests(unittest.TestCase):
    def test_parse_ps_output_keeps_full_command_and_skips_header(self):
        text = """  PID  PPID STAT  %CPU %MEM COMMAND
  101     1 S      12.5  1.2 python3 -m watchvideo https://example.com
  bad line
  202   101 S+      8.0  0.8 /usr/bin/ffmpeg -i input.mp4 audio.wav
"""

        processes = parse_ps_output(text)

        self.assertEqual(
            processes,
            [
                ProcessInfo(
                    pid=101,
                    ppid=1,
                    stat="S",
                    pcpu=12.5,
                    pmem=1.2,
                    command="python3 -m watchvideo https://example.com",
                ),
                ProcessInfo(
                    pid=202,
                    ppid=101,
                    stat="S+",
                    pcpu=8.0,
                    pmem=0.8,
                    command="/usr/bin/ffmpeg -i input.mp4 audio.wav",
                ),
            ],
        )

    def test_find_watchvideo_processes_matches_keywords_and_excludes_scanners(self):
        processes = [
            ProcessInfo(101, 1, "S", 1.0, 0.1, "python3 -m watchvideo demo.mp4"),
            ProcessInfo(102, 1, "S", 1.0, 0.1, "/usr/bin/yt-dlp -P /opt/watch-video-skill/analysis https://example.com"),
            ProcessInfo(103, 1, "S", 1.0, 0.1, "rg watchvideo"),
            ProcessInfo(104, 1, "S", 1.0, 0.1, "ps -axo pid=,ppid=,stat=,pcpu=,pmem=,command="),
            ProcessInfo(105, 1, "S", 1.0, 0.1, "zsh"),
            ProcessInfo(106, 1, "S", 1.0, 0.1, "whisper.cpp/build/bin/whisper-cli audio.wav"),
            ProcessInfo(107, 1, "S", 1.0, 0.1, "python3 -m watchvideo processes"),
            ProcessInfo(108, 1, "S", 1.0, 0.1, "helper --message 'Python/FFmpeg/浏览器自动化'"),
            ProcessInfo(109, 1, "S", 1.0, 0.1, "python3 -m watchvideo analyze demo.mp4"),
            ProcessInfo(110, 1, "S", 1.0, 0.1, "/usr/bin/ffmpeg -i unrelated.mp4 out.wav"),
        ]

        matches = find_watchvideo_processes(
            processes,
            project_root="/opt/watch-video-skill",
            current_pid=109,
        )

        self.assertEqual([process.pid for process in matches], [101, 102, 106])

    def test_render_process_report_lists_matches_without_kill_instructions(self):
        processes = [
            ProcessInfo(101, 1, "S", 12.5, 1.2, "python3 -m watchvideo demo.mp4"),
            ProcessInfo(202, 101, "S+", 8.0, 0.8, "/usr/bin/ffmpeg -i input.mp4 audio.wav"),
        ]

        report = render_process_report(processes)

        self.assertIn("发现 2 个相关进程", report)
        self.assertIn("`101`", report)
        self.assertIn("python3 -m watchvideo demo.mp4", report)
        self.assertIn("/usr/bin/ffmpeg -i input.mp4 audio.wav", report)
        self.assertNotIn("kill", report.lower())

    def test_render_process_report_handles_empty_matches(self):
        report = render_process_report([])

        self.assertIn("未发现 watchvideo 相关进程。", report)

    def test_scan_processes_uses_runner_and_returns_filtered_matches(self):
        calls = []

        def fake_runner(args):
            calls.append(args)
            return """101 1 S 12.5 1.2 python3 -m watchvideo demo.mp4
102 1 S 0.0 0.1 zsh
"""

        matches = scan_processes(runner=fake_runner, current_pid=999)

        self.assertEqual(
            calls,
            [["ps", "-axo", "pid=,ppid=,stat=,pcpu=,pmem=,command="]],
        )
        self.assertEqual([process.pid for process in matches], [101])


if __name__ == "__main__":
    unittest.main()
