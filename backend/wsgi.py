import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from main import app


def application(environ, start_response):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    headers = []
    for key, value in environ.items():
        if key == "CONTENT_TYPE":
            headers.append((b"content-type", value.encode()))
        elif key == "CONTENT_LENGTH":
            headers.append((b"content-length", value.encode()))
        elif key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").lower().encode()
            headers.append((header_name, value.encode()))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.0").split("/")[-1],
        "method": environ["REQUEST_METHOD"],
        "scheme": environ.get("wsgi.url_scheme", "http"),
        "path": environ.get("PATH_INFO", "/"),
        "query_string": environ.get("QUERY_STRING", "").encode(),
        "root_path": environ.get("SCRIPT_NAME", ""),
        "headers": headers,
    }

    body = environ["wsgi.input"].read()
    status_code = 500
    resp_headers = []
    resp_body = bytearray()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        nonlocal status_code, resp_headers
        if message["type"] == "http.response.start":
            status_code = message["status"]
            resp_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            resp_body.extend(message.get("body", b""))

    async def run():
        await app(scope, receive, send)

    loop.run_until_complete(run())
    loop.close()

    status_text = {
        200: "OK", 201: "Created", 204: "No Content",
        301: "Moved Permanently", 302: "Found",
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 422: "Unprocessable Entity",
        500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
    }.get(status_code, "Unknown")

    start_response(f"{status_code} {status_text}",
                   [(k.decode(), v.decode()) for k, v in resp_headers])
    return [bytes(resp_body)]
