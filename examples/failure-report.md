# 视频分析失败示例

> 这是脱敏示例，用来展示拿不到视频证据时应该怎样停止，而不是靠标题或搜索结果猜。

- 来源: `https://example.com/share/video/123`
- 错误: `视频下载失败：yt-dlp 下载失败，分享页/SSR play_addr 兜底也失败。请提供本地视频文件或可访问直链。`

没有生成可用的 MP4、字幕、转写或关键帧证据。**不要基于标题、简介或搜索结果总结视频内容。**

## 下载诊断

- `failed` plain yt-dlp: Fresh cookies are needed
- `failed` yt-dlp browser cookies (chrome): cookie database is locked
- `ok` mobile share page: 48231 chars
- `failed` mobile share page play_addr: 分享页没有发现 play_addr 视频直链
- `failed` direct video download: 没有生成有效视频文件

## Agent 应该怎么回答

这个视频目前没有可用证据，不能总结内容。下载链路卡在 `mobile share page play_addr`：普通 `yt-dlp` 需要 fresh cookies，Chrome cookies 重试失败，分享页虽然可读取，但没有解析到可下载的视频地址。请提供本地视频文件或可访问的 MP4 直链，我再继续转写、抽帧并总结。

## Agent 不应该怎么回答

不要写：

> 根据标题和网上资料，这个视频可能主要讲……

这会把非视频证据包装成视频理解结果。
