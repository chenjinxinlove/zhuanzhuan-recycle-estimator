#!/usr/bin/env python3
"""OpenClaw 回收 Skill 调用脚本。"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from typing import Any
from urllib import request
from urllib.error import HTTPError

STATE_DIR = os.path.expanduser("~/.claude/skills/zhuanzhuan-recycle-estimator")
STATE_FILE = os.path.join(STATE_DIR, ".skill_state.json")
THREAD_ENV_KEYS = (
    "CLAUDE_CONVERSATION_ID",
    "CLAUDE_SESSION_ID",
    "CLAUDE_THREAD_ID",
    "ANTHROPIC_SESSION_ID",
    "CODEX_THREAD_ID",
)


def parse_bool(value: str) -> bool:
    """解析布尔字符串。"""
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"无效的布尔值: {value}")


def resolve_thread_scope() -> str | None:
    """解析当前会话标识，用于对话级状态隔离。"""
    for key in THREAD_ENV_KEYS:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return None


def resolve_state_file() -> str:
    """解析当前请求应使用的状态文件路径。"""
    thread_scope = resolve_thread_scope()
    if not thread_scope:
        return STATE_FILE

    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", thread_scope).strip("_")
    if not normalized:
        return STATE_FILE
    return os.path.join(STATE_DIR, f".skill_state_{normalized}.json")


def load_state() -> dict[str, Any]:
    """加载最近一次调用状态。"""
    state_file = resolve_state_file()
    if not os.path.exists(state_file):
        return {}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict[str, Any]) -> None:
    """保存最近一次调用状态。"""
    state_file = resolve_state_file()
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def parse_json_argument(raw: str, argument_name: str) -> dict[str, Any]:
    """解析命令行中的 JSON 对象参数。"""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{argument_name} 必须是合法 JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError(f"{argument_name} 必须是 JSON 对象")
    return parsed


_MIME_FALLBACK = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}
FILE_SIZE_WARN_BYTES = 5 * 1024 * 1024


def resolve_image_source(image_value: str) -> tuple[str, str | None]:
    """URL 直接返回；本地文件读取后返回 data URI。"""
    if image_value.startswith(("http://", "https://")):
        return image_value, None

    if not os.path.isfile(image_value):
        return image_value, None  # 保持向后兼容

    file_size = os.path.getsize(image_value)
    if file_size > FILE_SIZE_WARN_BYTES:
        print(
            f"警告: 图片 {os.path.basename(image_value)} 大小 "
            f"{file_size / 1024 / 1024:.1f} MB，base64 后约 "
            f"{file_size * 4 / 3 / 1024 / 1024:.1f} MB",
            file=sys.stderr,
        )

    mime_type, _ = mimetypes.guess_type(image_value)
    if not mime_type:
        ext = os.path.splitext(image_value)[1].lower()
        mime_type = _MIME_FALLBACK.get(ext, "application/octet-stream")

    with open(image_value, "rb") as f:
        b64_str = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime_type};base64,{b64_str}", mime_type


def build_structured_attachments(args: argparse.Namespace) -> list[dict[str, Any]]:
    """构造图片和结构化选项附件。"""
    attachments: list[dict[str, Any]] = []

    for index, image_value in enumerate(args.image):
        media_id = args.image_media_id[index] if index < len(args.image_media_id) else None
        resolved_url, mime_type = resolve_image_source(image_value)
        payload_dict: dict[str, Any] = {
            "url": resolved_url,
            "signed_url": resolved_url,
            "media_id": media_id,
            "source": args.image_source,
        }
        if mime_type:
            payload_dict["mime_type"] = mime_type
        attachments.append({"type": "image", "payload": payload_dict})

    for raw_attrs in args.attrs:
        attachments.append(
            {
                "type": "attrs",
                "payload": parse_json_argument(raw_attrs, "--attrs"),
            }
        )

    for raw_model_option in args.model_option:
        attachments.append(
            {
                "type": "model_option",
                "payload": parse_json_argument(raw_model_option, "--model-option"),
            }
        )

    return attachments


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    """构造请求体。"""
    state = load_state()
    attachments = build_structured_attachments(args)

    message = {
        "role": "user",
        "content": args.text,
    }
    if attachments:
        message["attachments"] = attachments

    client_info: dict[str, Any] = {
        "user_agent": "claude-code-openclaw-recycle-skill",
    }
    resolved_client_ip = args.client_ip or state.get("client_ip")
    if resolved_client_ip:
        client_info["ip"] = resolved_client_ip

    payload: dict[str, Any] = {
        "messages": [message],
        "context_control": {
            "allow_auto_resume": args.allow_auto_resume,
            "force_new_session": args.force_new_session,
        },
        "client_info": client_info,
    }

    resolved_skill_token = args.skill_token or state.get("skill_token")
    resolved_session_id = args.session_id or state.get("session_id")

    if resolved_skill_token:
        payload["skill_token"] = resolved_skill_token
    if resolved_session_id:
        payload["session_id"] = resolved_session_id

    return payload


def format_request_error(exc: Exception) -> str:
    """格式化请求异常，优先透传后端错误码和错误信息。"""
    if isinstance(exc, HTTPError):
        error_message = f"HTTP {exc.code}: {exc.reason}"
        try:
            response_body = exc.read().decode("utf-8")
            parsed = json.loads(response_body)
            backend_code = parsed.get("error_code")
            backend_message = parsed.get("error_message")
            if backend_code or backend_message:
                details = " | ".join(part for part in [backend_code, backend_message] if part)
                return f"{error_message} | {details}"
        except Exception:
            return error_message
        return error_message
    return str(exc)


def main() -> int:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="调用 OpenClaw 回收估价接口")
    parser.add_argument("--text", required=True, help="用户输入文本")
    parser.add_argument(
        "--image", action="append", default=[], help="图片 URL 或本地文件路径，可传多次；本地文件会自动 base64 编码"
    )
    parser.add_argument(
        "--image-media-id", action="append", default=[], help="图片 media_id，可传多次并与 --image 对齐"
    )
    parser.add_argument("--image-source", default="openclaw_im", help="图片来源标识")
    parser.add_argument("--attrs", action="append", default=[], help='核心属性附件 JSON，如 {"capacityId":"678742"}')
    parser.add_argument(
        "--model-option",
        action="append",
        default=[],
        help='型号选项附件 JSON，如 {"selected_id":"1011385","selected_name":"iPhone 17 Pro"}',
    )
    parser.add_argument("--skill-token", help="上一轮返回的 skill_token")
    parser.add_argument("--session-id", help="上一轮返回的 session_id")
    parser.add_argument("--client-ip", help="透传给接口的测试 IP，未传时默认复用本地状态")
    parser.add_argument("--reset-state", action="store_true", help="清空本地缓存的 skill_token/session_id")
    parser.add_argument("--allow-auto-resume", type=parse_bool, default=True, help="是否允许自动续接")
    parser.add_argument("--force-new-session", type=parse_bool, default=False, help="是否强制新建 session")
    parser.add_argument(
        "--base-url",
        default="https://zai.zhuanzhuan.com/zai/find_mate/v1/openclaw/recycle-skill/valuate",
        help="接口地址",
    )
    args = parser.parse_args()

    state_file = resolve_state_file()
    if args.reset_state and os.path.exists(state_file):
        os.remove(state_file)

    payload = build_payload(args)
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url=args.base_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
            parsed = json.loads(response_body)
            if parsed.get("success"):
                save_state(
                    {
                        "skill_token": parsed.get("skill_token"),
                        "session_id": parsed.get("session_id"),
                        "valuation_context_id": parsed.get("valuation_context_id"),
                        "client_ip": payload.get("client_info", {}).get("ip"),
                    }
                )
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            return 0
    except Exception as exc:
        print(f"请求失败: {format_request_error(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
