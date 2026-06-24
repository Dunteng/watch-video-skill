# Remote Download Diagnostics Example

> This is a sanitized example showing how `watchvideo` records a short-video download chain. Real reports will contain different URLs, filenames, and errors.

## Successful Path

- `failed` plain yt-dlp: Fresh cookies are needed
- `failed` yt-dlp browser cookies (chrome): login required
- `ok` mobile share page: 69312 chars
- `ok` mobile share page play_addr: 2 candidate(s)
- `ok` direct video download: share-page-play-addr.mp4 via https://cdn.example.invalid/video.mp4

## What It Means

- Plain `yt-dlp` did not get the video.
- Browser-cookie retry also failed.
- The CLI did not open Chrome UI; it fetched the mobile share page directly.
- The share-page SSR data contained `play_addr.url_list`.
- An `aweme/v1/playwm`-style URL redirected to a CDN MP4.

## Next Evidence Steps

After download succeeds, the CLI continues to:

1. Read duration and resolution with `ffprobe`.
2. Prefer platform subtitles or sidecar subtitles.
3. Use system `whisper` or local `.tools/whisper.cpp` when subtitles are missing.
4. Extract keyframes and optionally run OCR.
5. Write `report.md`, `report.json`, and `summary-input.md`.
6. Delete the remote MP4 by default and record that cleanup in the report.
