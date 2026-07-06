"""Baidu image crawler used by XCrawler tasks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import requests
from PIL import Image

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Referer": "https://image.baidu.com/",
}

AJAX_URL = "https://image.baidu.com/search/acjson"
PAGE_SIZE = 30
MAX_EMPTY_PAGES = 2

FORMAT_EXT = {
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "png": ".png",
    "webp": ".webp",
}


@dataclass
class CrawlStats:
    total: int = 0
    downloaded: int = 0
    skipped_format: int = 0
    skipped_size: int = 0
    skipped_dup: int = 0
    failed: int = 0


@dataclass
class CrawlResult:
    images: list = field(default_factory=list)
    stats: CrawlStats = field(default_factory=CrawlStats)
    cancelled: bool = False


class BaiduImageCrawler:
    """Crawl images from Baidu's image search AJAX endpoint."""

    def __init__(
        self,
        headers: Optional[dict] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ):
        self.headers = dict(DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.is_cancelled = is_cancelled or (lambda: False)

    def crawl(
        self,
        keywords: Iterable[str],
        max_count: int,
        save_dir: str,
        allowed_format: Optional[str] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        checkpoint_callback: Optional[Callable[[CrawlResult], None]] = None,
        image_callback: Optional[Callable[[dict], None]] = None,
        search_items: Optional[list[dict]] = None,
    ) -> CrawlResult:
        os.makedirs(save_dir, exist_ok=True)
        result = CrawlResult()
        target_ext = FORMAT_EXT.get((allowed_format or "").lower())
        existing_hashes: set[str] = set()

        normalized_search_items = []
        if search_items:
            for item in search_items:
                query_keywords = [str(k).strip() for k in item.get("query_keywords", []) if str(k).strip()]
                if not query_keywords:
                    continue
                normalized_item = dict(item)
                normalized_item["query_keywords"] = query_keywords
                try:
                    normalized_item["target_count"] = int(normalized_item.get("target_count") or 0)
                except (TypeError, ValueError):
                    normalized_item["target_count"] = 0
                normalized_search_items.append(normalized_item)

        if normalized_search_items:
            total_target = sum(max(0, item.get("target_count", 0)) for item in normalized_search_items)
            if total_target <= 0:
                per_item = max(1, max_count // max(1, len(normalized_search_items)))
                for item in normalized_search_items:
                    item["target_count"] = per_item
            for item in normalized_search_items:
                if self.is_cancelled() or result.stats.downloaded >= max_count:
                    result.cancelled = self.is_cancelled()
                    break
                remaining_total = max_count - result.stats.downloaded
                item_target = min(max(1, item.get("target_count") or 1), remaining_total)
                downloaded_before = result.stats.downloaded
                self._crawl_search_item(
                    search_item=item,
                    remaining=item_target,
                    save_dir=save_dir,
                    target_ext=target_ext,
                    min_width=min_width,
                    min_height=min_height,
                    result=result,
                    existing_hashes=existing_hashes,
                    progress_callback=progress_callback,
                    checkpoint_callback=checkpoint_callback,
                    image_callback=image_callback,
                    total_goal=max_count,
                )
                if result.stats.downloaded == downloaded_before and remaining_total > 0:
                    continue
        else:
            normalized_keywords = [str(k).strip() for k in keywords if str(k).strip()]
            if not normalized_keywords:
                return CrawlResult()
            for keyword in normalized_keywords:
                if self.is_cancelled() or result.stats.downloaded >= max_count:
                    result.cancelled = self.is_cancelled()
                    break
                self._crawl_keyword(
                    keyword=keyword,
                    remaining=max_count - result.stats.downloaded,
                    save_dir=save_dir,
                    target_ext=target_ext,
                    min_width=min_width,
                    min_height=min_height,
                    result=result,
                    existing_hashes=existing_hashes,
                    progress_callback=progress_callback,
                    checkpoint_callback=checkpoint_callback,
                    image_callback=image_callback,
                    total_goal=max_count,
                    search_context={
                        "item_id": f"legacy_{self._safe_id(keyword)}",
                        "query_keywords": [keyword],
                        "labels": {},
                        "label_display": {},
                        "axis_key": None,
                        "axis_name": None,
                        "value_key": None,
                        "value_name": None,
                        "rationale": "legacy keyword crawl",
                    },
                )

        if progress_callback:
            progress_callback(1.0, "抓取完成")
        return result

    def _crawl_search_item(
        self,
        search_item: dict,
        remaining: int,
        save_dir: str,
        target_ext: Optional[str],
        min_width: Optional[int],
        min_height: Optional[int],
        result: CrawlResult,
        existing_hashes: set[str],
        progress_callback: Optional[Callable[[float, str], None]],
        checkpoint_callback: Optional[Callable[[CrawlResult], None]],
        image_callback: Optional[Callable[[dict], None]],
        total_goal: int,
    ) -> None:
        if remaining <= 0:
            return
        for keyword in search_item.get("query_keywords", []):
            if self.is_cancelled() or result.stats.downloaded >= total_goal or remaining <= 0:
                return
            downloaded_before = result.stats.downloaded
            self._crawl_keyword(
                keyword=keyword,
                remaining=remaining,
                save_dir=save_dir,
                target_ext=target_ext,
                min_width=min_width,
                min_height=min_height,
                result=result,
                existing_hashes=existing_hashes,
                progress_callback=progress_callback,
                checkpoint_callback=checkpoint_callback,
                image_callback=image_callback,
                total_goal=total_goal,
                search_context=search_item,
            )
            remaining -= max(0, result.stats.downloaded - downloaded_before)

    def _crawl_keyword(
        self,
        keyword: str,
        remaining: int,
        save_dir: str,
        target_ext: Optional[str],
        min_width: Optional[int],
        min_height: Optional[int],
        result: CrawlResult,
        existing_hashes: set[str],
        progress_callback: Optional[Callable[[float, str], None]],
        checkpoint_callback: Optional[Callable[[CrawlResult], None]] = None,
        image_callback: Optional[Callable[[dict], None]] = None,
        total_goal: int = 1,
        search_context: Optional[dict] = None,
    ) -> None:
        if remaining <= 0:
            return

        downloaded_for_kw = 0
        page = 0
        empty_pages = 0

        while downloaded_for_kw < remaining and empty_pages < MAX_EMPTY_PAGES:
            if self.is_cancelled():
                result.cancelled = True
                return

            page_data = self._fetch_page(keyword, page)
            if not page_data:
                empty_pages += 1
                page += 1
                time.sleep(1.0)
                continue

            empty_pages = 0
            for img in page_data:
                if self.is_cancelled():
                    result.cancelled = True
                    return
                if downloaded_for_kw >= remaining:
                    break

                saved = self._process_image(
                    img_data=img,
                    keyword=keyword,
                    save_dir=save_dir,
                    target_ext=target_ext,
                    min_width=min_width,
                    min_height=min_height,
                    result=result,
                    existing_hashes=existing_hashes,
                    search_context=search_context or {},
                )
                if saved:
                    downloaded_for_kw += 1
                    result.stats.downloaded += 1
                    image_record = result.images[-1]
                    if image_callback:
                        image_callback(image_record)
                    if progress_callback:
                        progress_callback(
                            min(result.stats.downloaded / max(1, total_goal), 0.99),
                            f"已下载 {result.stats.downloaded} 张 - 检索词「{keyword}」",
                        )
                    if checkpoint_callback:
                        checkpoint_callback(result)
                time.sleep(0.3)

            page += 1
            time.sleep(0.7)

    def _fetch_page(self, keyword: str, page: int) -> Optional[list]:
        params = {
            "tn": "resultjson_com",
            "logid": "7617111360412525441",
            "ipn": "rj",
            "ct": "201326592",
            "is": "",
            "fp": "result",
            "fr": "",
            "word": keyword,
            "queryWord": keyword,
            "cl": "2",
            "lm": "-1",
            "ie": "utf-8",
            "oe": "utf-8",
            "adpicid": "",
            "st": "-1",
            "z": "",
            "ic": "",
            "hd": "",
            "latest": "",
            "copyright": "",
            "s": "",
            "se": "",
            "tab": "",
            "width": "",
            "height": "",
            "face": "0",
            "istype": "2",
            "qc": "",
            "nc": "1",
            "expermode": "",
            "nojc": "",
            "isAsync": "",
            "pn": page * PAGE_SIZE,
            "rn": str(PAGE_SIZE),
            "gsm": "1e",
        }
        try:
            resp = requests.get(AJAX_URL, params=params, headers=self.headers, timeout=15)
            resp.raise_for_status()
        except Exception:
            return None

        text = resp.text
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        return [img for img in (payload.get("data") or []) if img]

    def _image_url(self, img_data: dict) -> Optional[str]:
        url = img_data.get("thumbURL") or img_data.get("middleURL") or img_data.get("objURL") or ""
        if not url or url.startswith("data:"):
            return None
        if not url.startswith("http"):
            if url.startswith("//"):
                return "https:" + url
            return None
        return url

    def _process_image(
        self,
        img_data: dict,
        keyword: str,
        save_dir: str,
        target_ext: Optional[str],
        min_width: Optional[int],
        min_height: Optional[int],
        result: CrawlResult,
        existing_hashes: set[str],
        search_context: dict,
    ) -> bool:
        url = self._image_url(img_data)
        if not url:
            return False

        ext = self._ext_from_url(url)
        if target_ext and ext and ext.lower() != target_ext.lower() and ext.lower() not in (".jpg", ".jpeg"):
            result.stats.skipped_format += 1
            return False

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            content = resp.content
        except Exception:
            result.stats.failed += 1
            return False

        if len(content) < 1024:
            result.stats.failed += 1
            return False

        img_hash = hashlib.md5(content).hexdigest()
        if img_hash in existing_hashes:
            result.stats.skipped_dup += 1
            return False

        real_ext = self._ext_from_bytes(content) or ext or ".jpg"
        if target_ext and real_ext.lower() != target_ext.lower():
            result.stats.skipped_format += 1
            return False

        width, height = self._read_dimensions(content)
        if min_width and width and width < min_width:
            result.stats.skipped_size += 1
            return False
        if min_height and height and height < min_height:
            result.stats.skipped_size += 1
            return False

        result.stats.total += 1
        index = result.stats.total
        filename = f"img_{index:05d}{real_ext}"
        full_path = os.path.join(save_dir, filename)

        try:
            with open(full_path, "wb") as output_file:
                output_file.write(content)
        except OSError:
            result.stats.failed += 1
            return False

        existing_hashes.add(img_hash)
        result.images.append(
            {
                "filename": filename,
                "relative_path": os.path.join("images", filename).replace("\\", "/"),
                "url": url,
                "width": width,
                "height": height,
                "file_size": len(content),
                "resolution": f"{width}x{height}" if width and height else "",
                "keyword": keyword,
                "hash": img_hash,
                "from_page_title": img_data.get("fromPageTitle", ""),
                "from_url": self._from_url(img_data),
                "labels": search_context.get("labels") or {},
                "label_display": search_context.get("label_display") or {},
                "search_metadata": {
                    "item_id": search_context.get("item_id"),
                    "query_keywords": search_context.get("query_keywords") or [keyword],
                    "matched_keyword": keyword,
                    "axis_key": search_context.get("axis_key"),
                    "axis_name": search_context.get("axis_name"),
                    "value_key": search_context.get("value_key"),
                    "value_name": search_context.get("value_name"),
                    "rationale": search_context.get("rationale", ""),
                },
                "mask_relative_path": "",
                "mask_status": "not_requested",
                "extra": {},
            }
        )
        return True

    @staticmethod
    def _safe_id(text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_") or "item"

    @staticmethod
    def _ext_from_url(url: str) -> str:
        path = url.split("?")[0]
        last = path.rsplit("/", 1)[-1]
        if "." in last:
            return "." + last.rsplit(".", 1)[-1].lower()
        return ""

    @staticmethod
    def _ext_from_bytes(content: bytes) -> Optional[str]:
        try:
            from io import BytesIO

            with Image.open(BytesIO(content)) as image:
                fmt = (image.format or "").lower()
            if fmt == "jpeg":
                return ".jpg"
            if fmt in ("jpg", "png", "webp", "gif", "bmp"):
                return "." + fmt
        except Exception:
            return None
        return None

    @staticmethod
    def _read_dimensions(content: bytes) -> tuple[int, int]:
        try:
            from io import BytesIO

            with Image.open(BytesIO(content)) as image:
                return image.size
        except Exception:
            return (0, 0)

    @staticmethod
    def _from_url(img_data: dict) -> str:
        replace = img_data.get("replaceUrl") or []
        if replace and isinstance(replace, list):
            return replace[0].get("FromURL", "") or ""
        return img_data.get("fromURL", "") or ""
