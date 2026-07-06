"""XCrawlerAgent - validates task config via conversational QA with DeepSeek."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings

PLACEHOLDER = "待用户确认"
PLACEHOLDER_TOKENS = ("待用户确认", "未知", "无", "TBD", "tbd", "n/a", "N/A", "null", "NULL", "None")
VALID_FORMATS = {"jpg", "png", "webp"}

REQUIRED_FIELDS = [
    "subject",
    "classification_axes",
    "max_count",
    "name",
    "format",
    "description",
    "need_mask",
]


class XCrawlerAgent:
    """Agent that validates image crawler task config through conversation."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _build_system_prompt(self) -> str:
        return '[XCrawler Agent - Concise QA prompt]\n\nYou are XCrawler Agent, a concise and rigorous image-dataset configuration assistant.\n\n# Required fields (collect all of these):\n- `subject`: dataset theme, e.g. "ChaHu teapot"\n- `classification_axes`: a list of axes. A dataset may have multiple independent axes.\n  Each axis must contain `axis_key`, `axis_name`, and `values`. Each value contains `value_key`, `value_name`, and optional `aliases`.\n- `max_count`: 1-10000\n- `name`: dataset name\n- `format`: one of jpg / png / webp\n- `description`: at least 10 Chinese characters, describing intended use\n- `need_mask`: true / false\n\n# Optional fields:\n- `tags`: array of tags\n- `min_width`, `min_height`: integer lower bounds (or null)\n- `search_policy`: keyword generation policy (default: multi_axis_independent_strict)\n- `sampling_notes`: e.g. balance across eras\n\n# Keyword planning rules\n- Use short, rigorous query keywords like "紫砂壶 西施壶" or "ChaHu teapot Xishi shape".\n- Use one search item per (axis, value) pair; do NOT cross-combine unless the user asks for it.\n- The system auto-derives `search_items` and the flat `keywords` list server-side from `subject` + `classification_axes` + `max_count`. You do NOT need to include these in [CONFIG_SUMMARY].\n\n# mask\n- If the user wants masks: emit `need_mask: true`, `mask_provider: "aliyun_imageseg"`.\n- Otherwise: emit `need_mask: false`, `mask_provider: null`.\n\n# Conversation style\n- First reply: brief greeting + 5 short questions.\n- After the first user reply: only ask for missing fields, max 3 questions per turn.\n- Be concise. Never repeat or summarize source documents. Never mention internal implementation details.\n\n# Output format\nEnd every reply with ONE JSON block under [CONFIG_SUMMARY] that contains ALL the high-level fields you have collected so far:\n  subject, classification_axes, max_count, name, format, description, need_mask, mask_provider, tags, min_width, min_height, search_policy, sampling_notes.\nUse the literal string "TBD" for any field whose value is still unknown. Do NOT emit placeholders that are NOT the literal "TBD".\nFor unknown or unconfirmed string fields you may also use null.\nDo NOT include `keywords` or `search_items` in your JSON: the system auto-derives these server-side from `subject` + `classification_axes` + `max_count`.\nWhen the user confirms the final config, your [CONFIG_SUMMARY] should have NO "TBD" placeholders anywhere. Just one confirmation message + one [CONFIG_SUMMARY] block (no separate [CONFIG_COMPLETE] block needed; the system expands it server-side).\nKeep the narrative before [CONFIG_SUMMARY] concise (max ~6 sentences, no source-document paraphrasing).\n\nAlways respond in Chinese for narrative text. JSON keys stay English.\n'

    def _extract_marked_json(self, content: str, marker: str) -> Optional[Dict[str, Any]]:
        if marker not in content:
            return None
        json_str = content.split(marker, 1)[1].strip()
        start = json_str.find("{")
        if start < 0:
            return None
        json_str = json_str[start:]
        # Strategy: walk through the JSON tracking depth, ignoring braces inside strings.
        depth = 0
        in_string = False
        escape = False
        end_index = -1
        for index, char in enumerate(json_str):
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == "\"" and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_index = index
                    break
        if end_index >= 0:
            try:
                return json.loads(json_str[: end_index + 1])
            except json.JSONDecodeError:
                pass
        # Fallback: try to parse a truncated JSON by closing open braces / brackets.
        truncated = json_str
        # Strip a trailing partial line if any
        if not truncated.rstrip().endswith(("}", "]")):
            last_comma = truncated.rfind(",")
            last_brace_open = max(truncated.rfind("{"), truncated.rfind("["))
            if last_comma > last_brace_open:
                truncated = truncated[:last_comma]
        # Balance braces / brackets from inside string-aware perspective
        def balance(s):
            in_s = False
            esc = False
            opens = []
            for ch in s:
                if esc:
                    esc = False
                    continue
                if ch == "\\":
                    esc = True
                    continue
                if ch == "\"" and not esc:
                    in_s = not in_s
                    continue
                if in_s:
                    continue
                if ch in "{[":
                    opens.append("}" if ch == "{" else "]")
                elif ch in "}]":
                    if opens:
                        opens.pop()
            return s + "".join(reversed(opens))
        try:
            return json.loads(balance(truncated))
        except json.JSONDecodeError:
            return None

    def _slugify(self, text: str) -> str:
        text = (text or "").strip().lower()
        text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", text)
        text = re.sub(r"_+", "_", text).strip("_")
        return text or "item"

    def _normalize_axis(self, axis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(axis, dict):
            return None
        axis_name = str(axis.get("axis_name") or axis.get("name") or "").strip()
        axis_key = str(axis.get("axis_key") or self._slugify(axis_name)).strip()
        raw_values = axis.get("values") or []
        values = []
        for raw_value in raw_values:
            if isinstance(raw_value, str):
                value_name = raw_value.strip()
                if not value_name:
                    continue
                values.append(
                    {
                        "value_key": self._slugify(value_name),
                        "value_name": value_name,
                        "aliases": [],
                    }
                )
                continue
            if not isinstance(raw_value, dict):
                continue
            value_name = str(raw_value.get("value_name") or raw_value.get("name") or "").strip()
            if not value_name:
                continue
            aliases = raw_value.get("aliases") or []
            aliases = [str(alias).strip() for alias in aliases if str(alias).strip()]
            values.append(
                {
                    "value_key": str(raw_value.get("value_key") or self._slugify(value_name)).strip(),
                    "value_name": value_name,
                    "aliases": aliases,
                }
            )
        if not axis_name or not axis_key or not values:
            return None
        return {
            "axis_key": axis_key,
            "axis_name": axis_name,
            "values": values,
        }

    def _build_search_items(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        subject = str(config.get("subject") or "").strip()
        axes = config.get("classification_axes") or []
        max_count = int(config.get("max_count") or 0)
        normalized_axes = [self._normalize_axis(axis) for axis in axes]
        normalized_axes = [axis for axis in normalized_axes if axis]
        if not subject or not normalized_axes:
            return []

        raw_items: List[Dict[str, Any]] = []
        for axis in normalized_axes:
            for value in axis["values"]:
                primary = f"{subject} {value['value_name']}"
                keywords = [primary]
                for alias in value.get("aliases", [])[:2]:
                    keywords.append(f"{subject} {alias}")
                if axis["axis_name"] not in primary:
                    keywords.append(f"{subject} {axis['axis_name']} {value['value_name']}")
                deduped_keywords = []
                seen = set()
                for keyword in keywords:
                    cleaned = re.sub(r"\s+", " ", keyword).strip()
                    if cleaned and cleaned not in seen:
                        seen.add(cleaned)
                        deduped_keywords.append(cleaned)
                raw_items.append(
                    {
                        "item_id": f"{axis['axis_key']}_{value['value_key']}",
                        "query_keywords": deduped_keywords[:3],
                        "labels": {axis["axis_key"]: value["value_key"]},
                        "label_display": {axis["axis_name"]: value["value_name"]},
                        "axis_key": axis["axis_key"],
                        "axis_name": axis["axis_name"],
                        "value_key": value["value_key"],
                        "value_name": value["value_name"],
                        "rationale": "主题词结合分类值，优先覆盖单一分类轴，降低搜索歧义",
                    }
                )

        if not raw_items:
            return []

        base = max(1, max_count // len(raw_items)) if max_count else 1
        remainder = max(0, max_count - base * len(raw_items)) if max_count else 0
        for index, item in enumerate(raw_items):
            item["target_count"] = base + (1 if index < remainder else 0)
        return raw_items

    def _normalize_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        current = dict(config or {})

        def clean_placeholder(value):
            if value is None:
                return None
            if isinstance(value, str):
                stripped = value.strip()
                if stripped in PLACEHOLDER_TOKENS:
                    return None
            return value

        subject = str(clean_placeholder(current.get("subject")) or "").strip()
        if not subject and current.get("name"):
            subject = str(current.get("name")).replace("\u6570\u636e\u96c6", "").strip()
        current["subject"] = subject

        normalized_axes = []
        for axis in current.get("classification_axes") or []:
            normalized = self._normalize_axis(axis)
            if normalized:
                normalized_axes.append(normalized)
        current["classification_axes"] = normalized_axes

        fmt = clean_placeholder(current.get("format"))
        if fmt:
            current["format"] = str(fmt).lower().strip()
        else:
            current["format"] = None

        need_mask = clean_placeholder(current.get("need_mask"))
        if isinstance(need_mask, str):
            need_mask = need_mask.lower() in {"true", "1", "yes", "y", "t", "是", "对"}
        current["need_mask"] = bool(need_mask) if need_mask is not None else False
        current["mask_provider"] = "aliyun_imageseg" if current["need_mask"] else None

        max_count = clean_placeholder(current.get("max_count"))
        try:
            current["max_count"] = int(max_count) if max_count not in (None, "") else None
        except (TypeError, ValueError):
            current["max_count"] = None

        for size_key in ("min_width", "min_height"):
            size_value = clean_placeholder(current.get(size_key))
            try:
                current[size_key] = int(size_value) if size_value not in (None, "") else None
            except (TypeError, ValueError):
                current[size_key] = None

        tags = current.get("tags") or []
        if isinstance(tags, str):
            tags = [part.strip() for part in re.split(r"[,,、，;\s]+", tags) if part.strip()]
        current["tags"] = tags

        if not current.get("search_policy"):
            current["search_policy"] = "multi_axis_independent_strict"

        search_items = current.get("search_items") or []
        if not search_items and current["classification_axes"] and current.get("subject") and current.get("max_count"):
            search_items = self._build_search_items(current)
        current["search_items"] = search_items

        keywords = current.get("keywords") or []
        if not keywords and search_items:
            flattened = []
            seen = set()
            for item in search_items:
                for keyword in item.get("query_keywords", []):
                    if keyword not in seen:
                        seen.add(keyword)
                        flattened.append(keyword)
            keywords = flattened
        current["keywords"] = keywords

        if not current.get("name") and subject:
            current["name"] = f"{subject}\u591a\u7ef4\u5206\u7c7b\u6570\u636e\u96c6"

        return current

    def _merge_config(self, current_config: Optional[Dict[str, Any]], new_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        merged = dict(current_config or {})
        for key, value in (new_config or {}).items():
            if value in (None, PLACEHOLDER):
                continue
            merged[key] = value
        return self._normalize_config(merged)

    def _parse_config_from_response(self, content: str, current_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        marked = self._extract_marked_json(content, "[CONFIG_COMPLETE]")
        if marked is None:
            marked = self._extract_marked_json(content, "[CONFIG_SUMMARY]")
        if marked is None:
            return self._normalize_config(current_config)
        return self._merge_config(current_config, marked)

    def _validate_config(self, config: Dict[str, Any]) -> List[str]:
        normalized = self._normalize_config(config)
        missing: List[str] = []

        if not normalized.get("subject"):
            missing.append("subject")

        axes = normalized.get("classification_axes") or []
        if not axes:
            missing.append("classification_axes")
        else:
            has_invalid_axis = any(not axis.get("values") for axis in axes)
            if has_invalid_axis:
                missing.append("classification_axes")

        max_count = normalized.get("max_count")
        if not isinstance(max_count, int) or max_count < 1 or max_count > 10000:
            missing.append("max_count")

        name = str(normalized.get("name") or "")
        if len(name) < 2:
            missing.append("name")

        fmt = normalized.get("format")
        if fmt not in VALID_FORMATS:
            missing.append("format")

        desc = str(normalized.get("description") or "")
        if len(desc) < 10:
            missing.append("description")

        if "need_mask" not in normalized:
            missing.append("need_mask")

        if axes and max_count and not normalized.get("search_items"):
            missing.append("search_items")

        if normalized.get("need_mask") and normalized.get("mask_provider") != "aliyun_imageseg":
            missing.append("mask_provider")

        search_items = normalized.get("search_items") or []
        if search_items and max_count:
            covered = sum(max(0, int(item.get("target_count") or 0)) for item in search_items)
            if covered <= 0:
                missing.append("search_items")

        return list(dict.fromkeys(missing))

    async def chat(
        self,
        messages: List[Dict[str, str]],
        current_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]], bool, List[str]]:
        system_prompt = self._build_system_prompt()
        normalized_current = self._normalize_config(current_config)
        if normalized_current:
            system_prompt += "\n\n当前已收集配置：\n" + json.dumps(normalized_current, ensure_ascii=False, indent=2)

        api_messages = [{"role": "system", "content": system_prompt}, *messages]

        try:
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": settings.deepseek_model,
                    "messages": api_messages,
                    "temperature": 0.3,
                    "max_tokens": 1800,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            config = self._parse_config_from_response(content, normalized_current)
            missing = self._validate_config(config or {})
            return content, config, len(missing) == 0, missing
        except Exception as exc:
            return f"Agent 调用失败: {exc}", normalized_current, False, self._validate_config(normalized_current)

    async def close(self):
        await self.client.aclose()


agent = XCrawlerAgent()


async def get_agent() -> XCrawlerAgent:
    return agent
