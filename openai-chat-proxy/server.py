from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException
import argparse
import requests
import uvicorn
import json
import httpx
from typing import Dict
import asyncio
import time
import random
import os
from datetime import datetime
from fastapi.logger import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_url: str
    openai_api_key: str
    model_id: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()
print(f"Settings: {settings}")
MOCK_MODE = False
MOCK_MODEL_ID = "mock-tool-call-writer"
MOCK_CONTENT_CHARS = 128
MOCK_ARGUMENT_CHUNK_SIZE = 4
MOCK_CHUNK_DELAY_MS = 0.0
MOCK_TOKENS_PER_SECOND = 100.0
MOCK_APPROX_CHARS_PER_TOKEN = 4.0
MOCK_MODE_KIND = "default"


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


def configure_mock_from_env():
    global MOCK_MODE
    global MOCK_MODEL_ID
    global MOCK_CONTENT_CHARS
    global MOCK_ARGUMENT_CHUNK_SIZE
    global MOCK_CHUNK_DELAY_MS
    global MOCK_TOKENS_PER_SECOND
    global MOCK_APPROX_CHARS_PER_TOKEN
    global MOCK_MODE_KIND

    MOCK_MODE = _env_bool("CHAT_PROXY_MOCK_MODE", MOCK_MODE)
    MOCK_MODEL_ID = os.getenv("CHAT_PROXY_MOCK_MODEL", MOCK_MODEL_ID)
    MOCK_CONTENT_CHARS = _env_int("CHAT_PROXY_MOCK_CONTENT_CHARS", MOCK_CONTENT_CHARS)
    MOCK_ARGUMENT_CHUNK_SIZE = _env_int("CHAT_PROXY_MOCK_ARGUMENT_CHUNK_SIZE", MOCK_ARGUMENT_CHUNK_SIZE)
    MOCK_CHUNK_DELAY_MS = _env_float("CHAT_PROXY_MOCK_CHUNK_DELAY_MS", MOCK_CHUNK_DELAY_MS)
    MOCK_TOKENS_PER_SECOND = _env_float("CHAT_PROXY_MOCK_TOKENS_PER_SECOND", MOCK_TOKENS_PER_SECOND)
    MOCK_APPROX_CHARS_PER_TOKEN = _env_float(
        "CHAT_PROXY_MOCK_APPROX_CHARS_PER_TOKEN",
        MOCK_APPROX_CHARS_PER_TOKEN,
    )
    MOCK_MODE_KIND = os.getenv("CHAT_PROXY_MOCK_MODE_KIND", MOCK_MODE_KIND)


def create_app() -> FastAPI:
    configure_mock_from_env()
    if MOCK_MODE:
        print(
            "[MOCK配置] "
            f"模式={MOCK_MODE_KIND}，"
            f"输入token速度={MOCK_TOKENS_PER_SECOND} token/秒，"
            f"内容长度={MOCK_CONTENT_CHARS} 字符，"
            f"片段长度={MOCK_ARGUMENT_CHUNK_SIZE} 字符（单个delta字段最大长度；控制片段和最后片段可能更短，SSE整行会更长）"
        )
    return app


async def extract_chunk_data(chunk: str) -> Dict | None:
    """提取并解析 chunk 数据"""
    if not chunk or chunk == "data: [DONE]" or not chunk.startswith("data: "):
        return None
    try:
        data = json.loads(chunk.replace("data: ", ""))
        return data
    except json.JSONDecodeError:
        return None


RECORD_DIR = os.path.join(os.path.dirname(__file__), "record")


def gen_request_id():
    now = datetime.now()
    rand = f"{random.randint(0, 9999):04d}"
    return now.strftime(f"%m%d_%H%M_{rand}")


def save_record(req_id, request_body, response_body, meta):
    if MOCK_MODE:
        return
    day = req_id[:4]  # MMDD
    day_dir = os.path.join(RECORD_DIR, day)
    os.makedirs(day_dir, exist_ok=True)
    with open(os.path.join(day_dir, f"{req_id}_REQUEST.txt"), "w", encoding="utf-8") as f:
        f.write(request_body)
    with open(os.path.join(day_dir, f"{req_id}_RESPONSE.txt"), "w", encoding="utf-8") as f:
        f.write(response_body)
    with open(os.path.join(day_dir, f"{req_id}_META.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False, indent=2))


def _mock_make_file_content(char_count: int) -> str:
    parts: list[str] = []
    current_length = 0
    line_index = 0
    while current_length < char_count:
        line = (
            f"mock-line={line_index:04d} offset={current_length:06d} "
            "这是一段用于复现 Blade Agent 高并发流式工具调用卡顿的模拟文本。\n"
        )
        remaining = char_count - current_length
        chunk = line[:remaining]
        parts.append(chunk)
        current_length += len(chunk)
        line_index += 1
    return "".join(parts)


def _mock_write_arguments(request_id: str, char_count: int) -> str:
    payload = {
        "description": "写入压测文件",
        "file_path": f"mock-load/{request_id}.txt",
        "content": _mock_make_file_content(char_count),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _mock_content_text(char_count: int) -> str:
    return _mock_make_file_content(char_count)


def _mock_ls_arguments() -> str:
    return json.dumps({"description": "查看项目结构", "path": "."}, ensure_ascii=False, separators=(",", ":"))


def _mock_chunk_text(text: str, size: int) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]


def _mock_chunk_delay_seconds(part: str) -> float:
    explicit_delay = max(MOCK_CHUNK_DELAY_MS, 0.0) / 1000.0
    if MOCK_TOKENS_PER_SECOND <= 0 or MOCK_APPROX_CHARS_PER_TOKEN <= 0:
        return explicit_delay
    approx_tokens = max(len(part) / MOCK_APPROX_CHARS_PER_TOKEN, 1e-6)
    paced_delay = approx_tokens / MOCK_TOKENS_PER_SECOND
    return max(explicit_delay, paced_delay)


def _mock_stream_chunk(model: str, delta: dict, *, finish_reason: str | None = None) -> dict:
    return {
        "id": "chatcmpl-mock-stream",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }


def _mock_models_payload() -> dict:
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": MOCK_MODEL_ID,
                "object": "model",
                "created": now,
                "owned_by": "mock",
                "context_length": 1_000_000,
            },
            {"id": "qwen3.5-version-proxy", "object": "model", "created": 1750922734, "owned_by": "system"},
        ],
    }


def _is_mock_model(model: str | None) -> bool:
    return model == MOCK_MODEL_ID


def _mock_response_kind() -> str:
    if MOCK_MODE_KIND == "default":
        return "content-only" if random.random() < 0.5 else "tool-only"
    return MOCK_MODE_KIND


def _mock_non_stream_response(request_json: dict, request_id: str) -> dict:
    model = str(request_json.get("model") or MOCK_MODEL_ID)
    if _mock_response_kind() == "content-only":
        return {
            "id": f"chatcmpl-mock-{request_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": _mock_content_text(MOCK_CONTENT_CHARS),
                        "tool_calls": [
                            {
                                "id": f"call_mock_ls_{request_id}",
                                "type": "function",
                                "function": {
                                    "name": "Ls",
                                    "arguments": _mock_ls_arguments(),
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
    return {
        "id": f"chatcmpl-mock-{request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call_mock_write_{request_id}",
                            "type": "function",
                            "function": {
                                "name": "Write",
                                "arguments": _mock_write_arguments(request_id, MOCK_CONTENT_CHARS),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


app = FastAPI()


def fix_result(result: dict):
    tool_calls = result.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
    if len(tool_calls) == 0:
        return result

    for idx, tool_call in enumerate(tool_calls):
        print(type(tool_call["function"]["arguments"]))
        if type(tool_call["function"]["arguments"]) is dict:
            tool_call["function"]["arguments"] = json.dumps(tool_call["function"]["arguments"])
            tool_calls[idx] = tool_call
            print("[tool_call]", tool_call)
    result["choices"][0]["message"]["tool_calls"] = tool_calls
    return result


request_stoage = {}


@app.get("/v1/models")
async def chat_completions_proxy():
    if MOCK_MODE:
        return _mock_models_payload()
    return {
        "object": "list",
        "data": [{"id": "qwen3.5-version-proxy", "object": "model", "created": 1750922734, "owned_by": "system"}],
    }


@app.post("/v1/chat/completions")
async def chat_completions_proxy(request: Request):
    request_json = await request.json()
    message_size = len(json.dumps(request_json.get("messages", [])))
    request_model = str(request_json.get("model") or "")
    if MOCK_MODE and _is_mock_model(request_model):
        req_id = gen_request_id()
        payload = json.dumps(request_json, ensure_ascii=False)
        if not request_json.get("stream", False):
            result = _mock_non_stream_response(request_json, req_id)
            meta = {
                "target_url": "mock://chat/completions",
                "model_id": str(request_json.get("model") or MOCK_MODEL_ID),
                "usage": result.get("usage", {}),
                "ttft": 0,
                "tps": 0,
                "mock": True,
            }
            save_record(req_id, payload, json.dumps(result, ensure_ascii=False), meta)
            return result

        async def mock_event_stream():
            sse_lines = []
            call_id = f"call_mock_write_{req_id}"
            content_call_id = f"call_mock_ls_{req_id}"
            model = str(request_json.get("model") or MOCK_MODEL_ID)
            arguments = _mock_write_arguments(req_id, MOCK_CONTENT_CHARS)
            ls_arguments = _mock_ls_arguments()
            content = _mock_content_text(MOCK_CONTENT_CHARS)
            response_kind = _mock_response_kind()
            try:
                if response_kind == "content-only":
                    start_chunk = _mock_stream_chunk(model, {"role": "assistant"})
                    start_line = f"data: {json.dumps(start_chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(start_line)
                    yield start_line + "\n\n"

                    for part in _mock_chunk_text(content, MOCK_ARGUMENT_CHUNK_SIZE):
                        chunk = _mock_stream_chunk(model, {"content": part})
                        line = f"data: {json.dumps(chunk, ensure_ascii=False, separators=(',', ':'))}"
                        sse_lines.append(line)
                        delay = _mock_chunk_delay_seconds(part)
                        if delay > 0:
                            await asyncio.sleep(delay)
                        yield line + "\n\n"

                    tool_start_chunk = _mock_stream_chunk(
                        model,
                        {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": content_call_id,
                                    "type": "function",
                                    "function": {"name": "Ls", "arguments": ""},
                                }
                            ]
                        },
                    )
                    tool_start_line = f"data: {json.dumps(tool_start_chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(tool_start_line)
                    yield tool_start_line + "\n\n"

                    tool_args_chunk = _mock_stream_chunk(
                        model,
                        {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {"arguments": ls_arguments},
                                }
                            ]
                        },
                    )
                    tool_args_line = f"data: {json.dumps(tool_args_chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(tool_args_line)
                    yield tool_args_line + "\n\n"

                    end_chunk = _mock_stream_chunk(model, {}, finish_reason="tool_calls")
                    end_line = f"data: {json.dumps(end_chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(end_line)
                    yield end_line + "\n\n"
                    sse_lines.append("data: [DONE]")
                    yield "data: [DONE]\n\n"
                    return

                chunks = [
                    _mock_stream_chunk(model, {"role": "assistant"}),
                    _mock_stream_chunk(
                        model,
                        {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": call_id,
                                    "type": "function",
                                    "function": {"name": "Write", "arguments": ""},
                                }
                            ]
                        },
                    ),
                ]
                for chunk in chunks:
                    line = f"data: {json.dumps(chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(line)
                    yield line + "\n\n"
                for part in _mock_chunk_text(arguments, MOCK_ARGUMENT_CHUNK_SIZE):
                    chunk = _mock_stream_chunk(
                        model,
                        {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {"arguments": part},
                                }
                            ]
                        },
                    )
                    line = f"data: {json.dumps(chunk, ensure_ascii=False, separators=(',', ':'))}"
                    sse_lines.append(line)
                    delay = _mock_chunk_delay_seconds(part)
                    if delay > 0:
                        await asyncio.sleep(delay)
                    yield line + "\n\n"
                end_chunk = _mock_stream_chunk(model, {}, finish_reason="tool_calls")
                end_line = f"data: {json.dumps(end_chunk, ensure_ascii=False, separators=(',', ':'))}"
                sse_lines.append(end_line)
                yield end_line + "\n\n"
                sse_lines.append("data: [DONE]")
                yield "data: [DONE]\n\n"
            finally:
                meta = {
                    "target_url": "mock://chat/completions",
                    "model_id": model,
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    "ttft": 0,
                    "tps": 0,
                    "mock": True,
                }
                save_record(req_id, payload, "\n".join(sse_lines), meta)

        return StreamingResponse(mock_event_stream(), media_type="text/event-stream")

    request_json["model"] = settings.model_id
    headers = dict(request.headers)
    BASE_URL = settings.base_url

    if "glm" in settings.model_id:
        request_json["thinking"] = {"type": "disabled"}
        request_json["enable_thinking"] = False
        request_json["chat_template_kwargs"] = {"enable_thinking": False}

    if settings.model_id == "qwen/qwen3.5-35b-a3b":
        request_json["provider"] = {"order": ["alibaba"], "allow_fallbacks": False}

    # 转发请求到目标 URL
    target_url = f"{BASE_URL}/chat/completions"
    print(settings.openai_api_key)
    payload = json.dumps(request_json, ensure_ascii=False)
    print("[URL]", target_url)
    print("[INPUT]", payload)
    print("[MESSAGE_SIZE]", message_size)
    stream = request_json.get("stream", False)
    t0 = time.time()
    req_id = gen_request_id()

    if not stream:
        response = requests.post(
            target_url,
            json=request_json,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )
        ttft = time.time() - t0
        print(f"[TTFT] {ttft:.3f}s")
        try:
            result = response.json()
            print("[RESULT]", json.dumps(result, ensure_ascii=False))
            # logger.info(json.dumps(result, ensure_ascii=False))
            # result = fix_result(result)
        except Exception as e:
            print("[EXCEPTION]", response.text)
            raise (e)
        usage = result.get("usage", {})
        elapsed = time.time() - t0
        tps = usage.get("completion_tokens", 0) / elapsed if elapsed > 0 else 0
        meta = {
            "target_url": target_url,
            "model_id": settings.model_id,
            "usage": usage,
            "ttft": round(ttft, 3),
            "tps": round(tps, 1),
        }
        save_record(req_id, payload, json.dumps(result, ensure_ascii=False), meta)
        return result
    else:
        # 先建立连接并检查状态码（在返回 StreamingResponse 之前）
        client = httpx.AsyncClient(timeout=3600, verify=False)
        await client.__aenter__()

        stream_ctx = client.stream(
            method="POST",
            url=target_url,
            json=request_json,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )
        resp = await stream_ctx.__aenter__()

        # 检查状态码，如果失败就抛出异常（此时响应还未开始）
        if resp.status_code != 200:
            error_content = await resp.aread()
            error_text = error_content.decode("utf-8")
            print(f"[ERROR] Status: {resp.status_code}, Content: {error_text}")

            # 清理资源
            await stream_ctx.__aexit__(None, None, None)
            await client.__aexit__(None, None, None)

            # 抛出异常
            raise HTTPException(status_code=resp.status_code, detail=f"API request failed: {error_text}")

        # 状态码OK，创建流式响应
        async def event_stream():
            first_token = True
            ttft = 0
            usage = {}
            tps = 0
            sse_lines = []
            try:
                async for line in resp.aiter_lines():
                    sse_lines.append(line)
                    if "[DONE]" in line:
                        print("[DONE]")
                    if chunk_data := await extract_chunk_data(line):
                        if first_token:
                            ttft = time.time() - t0
                            print(f"[TTFT] {ttft:.3f}s")
                            print("[DELTA]")
                            first_token = False
                        try:
                            choices = chunk_data.get("choices", [{}])
                            if len(choices) > 0:
                                choices0 = choices[0]
                                delta = choices0.get("delta", {})
                            else:
                                delta = {}
                        except Exception as e:
                            print("解析失败:", chunk_data, e)
                        print(json.dumps(delta, ensure_ascii=False))
                        if "usage" in chunk_data and chunk_data["usage"]["total_tokens"]:
                            usage = chunk_data["usage"]
                            print("[USAGE]", usage)
                            elapsed = time.time() - t0
                            tps = usage["completion_tokens"] / elapsed
                            print(f"[TPS] {tps:.1f} tokens/s")
                    await asyncio.sleep(0.01)
                    yield line + "\n"
            finally:
                # 确保资源被正确清理
                await stream_ctx.__aexit__(None, None, None)
                await client.__aexit__(None, None, None)
                # 流结束后落盘日志
                meta = {
                    "target_url": target_url,
                    "model_id": settings.model_id,
                    "usage": usage,
                    "ttft": round(ttft, 3),
                    "tps": round(tps, 1),
                }
                save_record(req_id, payload, "\n".join(sse_lines), meta)

        return StreamingResponse(event_stream(), media_type="text/event-stream")


def test_fix():
    result = json.loads(
        """{"id": "0196a430c2b71699861bebfc1176d6e1", "object": "chat.completion", "created": 1746511381, "model": "Qwen/Qwen3-235B-A22B", "choices": [{"index": 0, "message": {"role": "assistant", "content": "", "tool_calls": [{"index": 0, "id": "0196a430c54dad289e05ac7459d1afe5", "type": "function", "function": {"name": "LLMPlanning", "arguments": {"plans": [{"agent_or_tool_id": "shopping.jd", "status": "waiting", "task": "搜索用户需要的商品"}, {"agent_or_tool_id": "shopping.jd", "status": "waiting", "task": "搜索商品并获取价格"}, {"agent_or_tool_id": "shopping.jd", "status": "waiting", "task": "帮助用户下单购买"}]}}}]}, "finish_reason": "tool_calls"}], "usage": {"prompt_tokens": 1019, "completion_tokens": 106, "total_tokens": 1125}, "system_fingerprint": ""}"""
    )
    print(result)
    result = fix_result(result)
    print(result)


# 运行 FastAPI 应用
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--mock-model", default=MOCK_MODEL_ID)
    parser.add_argument("--mock-content-chars", type=int, default=MOCK_CONTENT_CHARS)
    parser.add_argument("--mock-argument-chunk-size", type=int, default=MOCK_ARGUMENT_CHUNK_SIZE)
    parser.add_argument("--mock-chunk-delay-ms", type=float, default=MOCK_CHUNK_DELAY_MS)
    parser.add_argument("--mock-tokens-per-second", type=float, default=MOCK_TOKENS_PER_SECOND)
    parser.add_argument("--mock-approx-chars-per-token", type=float, default=MOCK_APPROX_CHARS_PER_TOKEN)
    parser.add_argument("--mode", choices=["default", "content-only", "tool-only"], default=MOCK_MODE_KIND)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    os.environ["CHAT_PROXY_MOCK_MODE"] = "1" if args.mock else "0"
    os.environ["CHAT_PROXY_MOCK_MODEL"] = args.mock_model
    os.environ["CHAT_PROXY_MOCK_CONTENT_CHARS"] = str(args.mock_content_chars)
    os.environ["CHAT_PROXY_MOCK_ARGUMENT_CHUNK_SIZE"] = str(args.mock_argument_chunk_size)
    os.environ["CHAT_PROXY_MOCK_CHUNK_DELAY_MS"] = str(args.mock_chunk_delay_ms)
    os.environ["CHAT_PROXY_MOCK_TOKENS_PER_SECOND"] = str(args.mock_tokens_per_second)
    os.environ["CHAT_PROXY_MOCK_APPROX_CHARS_PER_TOKEN"] = str(args.mock_approx_chars_per_token)
    os.environ["CHAT_PROXY_MOCK_MODE_KIND"] = args.mode

    uvicorn.run(
        "server:create_app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        factory=True,
    )
