# webserver.py - Async MVC Web Server Engine with Static Stream & Route Dispatching
import asyncio
import gc
import os
from aop import ROUTES

class HttpRequest:
    def __init__(self, method, path, headers, body, writer):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.writer = writer

class WebServer:
    def __init__(self, ioc, port=80):
        self.ioc = ioc
        self.port = port
        self.routes = []

    def register_controller(self, controller_instance):
        cls = controller_instance.__class__
        for method, path, fn in ROUTES:
            for attr in dir(cls):
                if getattr(cls, attr) == fn:
                    self.routes.append((method, path, controller_instance, fn))
                    break

    async def _dispatch(self, request):
        for method, route_path, ctrl, action in self.routes:
            if method == request.method and route_path == request.path:
                return await action(ctrl, request)
        return 404, "text/plain", "Not Found"

    async def _stream_index_file(self, writer):
        try:
            size = os.stat("index.html")[6]
            hdr = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\nContent-Length: {size}\r\n\r\n".encode("utf-8")
            writer.write(hdr)
            await writer.drain()

            buf = bytearray(1460)
            with open("index.html", "rb") as f:
                while True:
                    n = f.readinto(buf)
                    if not n:
                        break
                    writer.write(memoryview(buf)[:n])
                    await writer.drain()
        except Exception as e:
            msg = b"Error loading index.html"
            hdr = f"HTTP/1.1 500 Internal Error\r\nContent-Type: text/plain\r\nConnection: close\r\nContent-Length: {len(msg)}\r\n\r\n".encode("utf-8")
            writer.write(hdr + msg)
            await writer.drain()

    async def handle_client(self, reader, writer):
        try:
            req_line = await reader.readline()
            if not req_line:
                writer.close()
                return

            parts = req_line.decode("utf-8", "ignore").split()
            if len(parts) < 2:
                writer.close()
                return

            method, path = parts[0], parts[1]

            # Read headers
            headers = {}
            content_len = 0
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n" or line == b"\n":
                    break
                if line.lower().startswith(b"content-length:"):
                    try:
                        content_len = int(line.split(b":")[1].strip())
                    except Exception:
                        pass

            body = b""
            if content_len > 0:
                body = await reader.readexactly(content_len)

            request = HttpRequest(method, path, headers, body, writer)

            if method == "OPTIONS":
                writer.write(b"HTTP/1.1 204 No Content\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: GET, POST, OPTIONS\r\nAccess-Control-Allow-Headers: Content-Type\r\nConnection: close\r\n\r\n")
            elif path == "/" or path == "/index.html":
                await self._stream_index_file(writer)
            else:
                code, ctype, res_body = await self._dispatch(request)
                if code is not None:
                    res_bytes = res_body.encode("utf-8") if isinstance(res_body, str) else res_body
                    hdr = f"HTTP/1.1 {code} OK\r\nContent-Type: {ctype}\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\nContent-Length: {len(res_bytes)}\r\n\r\n".encode("utf-8")
                    writer.write(hdr + res_bytes)

            await writer.drain()
            gc.collect()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def run_server(self):
        server = await asyncio.start_server(self.handle_client, "0.0.0.0", self.port)
        print(f"MVC WebServer listening on port {self.port}")
        while True:
            await asyncio.sleep(1)
