# 远程下载诊断示例

> 这是脱敏示例，用来展示 `watchvideo` 如何记录短视频下载链路。真实报告中的 URL、文件名和错误信息会不同。

## 成功路径

- `failed` plain yt-dlp: Fresh cookies are needed
- `failed` yt-dlp browser cookies (chrome): login required
- `ok` mobile share page: 69312 chars
- `ok` mobile share page play_addr: 2 candidate(s)
- `ok` direct video download: share-page-play-addr.mp4 via https://cdn.example.invalid/video.mp4

## 报告含义

- 普通 `yt-dlp` 没有拿到视频。
- 浏览器 cookies 重试也没有成功。
- CLI 没有打开 Chrome UI，而是直接抓取移动端分享页。
- 分享页 SSR 数据里找到了 `play_addr.url_list`。
- `aweme/v1/playwm` 或同类地址跳转到了 CDN MP4。

## 后续证据

下载成功后，CLI 会继续：

1. 用 `ffprobe` 读取时长和分辨率。
2. 优先加载平台字幕或旁路字幕。
3. 没有字幕时用系统 `whisper` 或本地 `.tools/whisper.cpp` 转写。
4. 抽取关键帧，可选 OCR。
5. 生成 `report.md`、`report.json` 和 `summary-input.md`。
6. 默认删除远程下载 MP4，并在报告里写入 `清理记录`。
