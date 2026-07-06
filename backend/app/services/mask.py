import asyncio
import io
import os
from typing import Optional, Tuple

import requests
from alibabacloud_imageseg20191230 import models as imageseg_20191230_models
from alibabacloud_imageseg20191230.client import Client as ImageSeg20191230Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from app.config import settings


def is_mask_service_configured() -> bool:
    return bool(settings.aliyun_access_key_id and settings.aliyun_access_key_secret)


class MaskGenerationError(RuntimeError):
    pass


def _do_generate_mask(image_path: str, output_path: str) -> Tuple[str, bool, str]:
    """Generate a single mask. Returns (output_path, success, error_msg)."""
    try:
        if not is_mask_service_configured():
            return (output_path, False, "未配置阿里云图像分割密钥")
        if not os.path.exists(image_path):
            return (output_path, False, f"原图不存在: {image_path}")

        config = open_api_models.Config(
            access_key_id=settings.aliyun_access_key_id,
            access_key_secret=settings.aliyun_access_key_secret,
            endpoint=settings.aliyun_imageseg_endpoint,
            region_id=settings.aliyun_imageseg_region,
        )
        client = ImageSeg20191230Client(config)

        request = imageseg_20191230_models.SegmentCommonImageAdvanceRequest()
        with open(image_path, "rb") as image_file:
            request.image_urlobject = io.BytesIO(image_file.read())
        request.return_form = "mask"

        runtime = util_models.RuntimeOptions()
        response = client.segment_common_image_advance(request, runtime)
        mask_url: Optional[str] = response.body.data.image_url if response.body and response.body.data else None
        if not mask_url:
            return (output_path, False, "阿里云接口未返回 mask 地址")

        download = requests.get(mask_url, timeout=60)
        download.raise_for_status()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as output_file:
            output_file.write(download.content)

        return (output_path, True, "")
    except Exception as exc:
        return (output_path, False, str(exc))


async def generate_masks_batch(
    images: list[dict],
    images_dir: str,
    masks_dir: str,
    concurrency: int = 20,
    progress_callback: Optional[callable] = None,
) -> None:
    """Generate masks for a list of image dicts in parallel.

    Each image dict is updated in-place:
      - on success: mask_status="completed", mask_relative_path set
      - on failure: mask_status="failed", extra.mask_error set
    """
    if not is_mask_service_configured():
        for img in images:
            img["mask_status"] = "failed"
            img["extra"] = {**(img.get("extra") or {}), "mask_error": "未配置阿里云图像分割密钥"}
        return

    # Build list of (image_dict, image_path, mask_path)
    tasks = []
    for img in images:
        filename = img.get("filename", "")
        if not filename:
            continue
        image_path = os.path.join(images_dir, filename)
        base = os.path.splitext(filename)[0]
        mask_filename = base + ".mask.png"
        # Write to task_dir/masks/ (not images/masks/) to match old on_image behavior
        mask_path = os.path.join(masks_dir, mask_filename)
        tasks.append((img, image_path, mask_path))

    total = len(tasks)
    completed = [0]

    async def worker(img: dict, image_path: str, mask_path: str) -> None:
        ok, _, err = await asyncio.to_thread(_do_generate_mask, image_path, mask_path)
        if ok:
            img["mask_status"] = "completed"
            img["mask_relative_path"] = f"masks/{os.path.basename(mask_path)}"
        else:
            img["mask_status"] = "failed"
            img["extra"] = {**(img.get("extra") or {}), "mask_error": err}
        completed[0] += 1
        if progress_callback:
            progress_callback(completed[0] / max(total, 1), f"生成 Mask {completed[0]}/{total}")

    semaphore = asyncio.Semaphore(concurrency)
    async def bounded(img, image_path, mask_path):
        async with semaphore:
            await worker(img, image_path, mask_path)

    await asyncio.gather(*(bounded(img, ip, mp) for img, ip, mp in tasks))
