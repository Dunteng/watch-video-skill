from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PpmImage:
    width: int
    height: int
    pixels: bytes


def candidate_timestamps(
    duration_seconds: float,
    interval_seconds: float = 10.0,
) -> list[list[float]]:
    if duration_seconds <= 0:
        return []
    if interval_seconds <= 0:
        raise ValueError("interval_seconds 必须大于 0")

    groups: list[list[float]] = []
    start = 0.0
    while start < duration_seconds:
        end = min(duration_seconds, start + interval_seconds)
        span = end - start
        margin = 0.75 if span >= 1.5 else span / 4
        group = [start + margin, start + span / 2, end - margin]
        groups.append([round(timestamp, 3) for timestamp in group])
        start += interval_seconds
    return groups


def parse_ppm(data: bytes) -> PpmImage:
    # PPM 解析边界：只支持 ffmpeg 输出的 P6 二进制格式，用于清晰度评分。
    tokens: list[bytes] = []
    index = 0
    while len(tokens) < 4:
        while index < len(data) and chr(data[index]).isspace():
            index += 1
        if index < len(data) and data[index:index + 1] == b"#":
            while index < len(data) and data[index:index + 1] != b"\n":
                index += 1
            continue
        start = index
        while index < len(data) and not chr(data[index]).isspace():
            index += 1
        tokens.append(data[start:index])

    magic, width, height, max_value = tokens
    if magic != b"P6" or max_value != b"255":
        raise ValueError("只支持 P6/255 PPM 图片")
    if index >= len(data) or not chr(data[index]).isspace():
        raise ValueError("PPM header 缺少像素分隔符")

    # 函数职责：只消费 header 与像素之间的分隔符，不把像素里的空白字节当作 header 空白。
    index += 2 if data[index:index + 2] == b"\r\n" else 1

    width_int = int(width)
    height_int = int(height)
    expected = width_int * height_int * 3
    pixels = data[index:index + expected]
    if len(pixels) != expected:
        raise ValueError("PPM 像素数据不完整")
    return PpmImage(width=width_int, height=height_int, pixels=pixels)


def score_ppm_sharpness(data: bytes) -> float:
    image = parse_ppm(data)
    if image.width < 2 or image.height < 2:
        return 0.0

    gray = [
        int(
            0.299 * image.pixels[i]
            + 0.587 * image.pixels[i + 1]
            + 0.114 * image.pixels[i + 2]
        )
        for i in range(0, len(image.pixels), 3)
    ]

    total = 0
    count = 0
    for y in range(image.height):
        row = y * image.width
        for x in range(image.width):
            current = gray[row + x]
            if x + 1 < image.width:
                total += abs(current - gray[row + x + 1])
                count += 1
            if y + 1 < image.height:
                total += abs(current - gray[row + image.width + x])
                count += 1
    return total / count if count else 0.0
