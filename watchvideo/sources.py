from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse

from .models import Source


def classify_source(value: str) -> Source:
    stripped = value.strip()
    parsed = urlparse(stripped)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return Source(kind="url", value=stripped)

    path = Path(stripped).expanduser()
    if path.is_file():
        return Source(kind="file", value=stripped, path=path.resolve())

    raise FileNotFoundError(f"{stripped} 不是可访问的视频文件，也不是 http/https 链接")


def slugify_title(title: str, fallback: str = "video") -> str:
    # 目录名边界：保留中文、字母和数字，其余符号统一压成短横线。
    slug = title.strip().lower()
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", slug, flags=re.UNICODE)
    slug = slug.replace("_", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or fallback
