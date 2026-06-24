# Video Analysis Failure Example

> This is a sanitized example. It shows how `watchvideo` should stop when no video evidence can be produced, instead of guessing from titles or search results.

- Source: `https://example.com/share/video/123`
- Error: `Video download failed: yt-dlp failed, and share-page/SSR play_addr fallback also failed. Please provide a local video file or an accessible direct URL.`

No usable MP4, subtitle, transcript, or keyframe evidence was produced. **Do not summarize the video from the title, description, or search results.**

## Download Diagnostics

- `failed` plain yt-dlp: Fresh cookies are needed
- `failed` yt-dlp browser cookies (chrome): cookie database is locked
- `ok` mobile share page: 48231 chars
- `failed` mobile share page play_addr: no play_addr video URL found
- `failed` direct video download: no valid video file was produced

## Correct Agent Response

I do not have usable video evidence yet, so I cannot summarize this video. The download chain stopped at `mobile share page play_addr`: plain `yt-dlp` needed fresh cookies, Chrome cookie retry failed, and the share page did not expose a downloadable video address. Please provide a local video file or an accessible MP4 URL, then I can continue with transcription, keyframes, and summary.

## Incorrect Agent Response

Do not write:

> Based on the title and public materials, this video probably says...

That presents non-video evidence as if it were video understanding.
