# controllers.py - MVC Controllers with Aspect-Oriented Routing and DTO Injection
import json
import ubinascii
import time
import asyncio
from aop import route, json_dto, handle_errors
from dto import (
    LaunchRequestDto, PaintRequestDto, TickerRequestDto, StudioRequestDto,
    FftConfigRequestDto, ApiResponseDto
)

class BaseController:
    def __init__(self, ioc):
        self.ioc = ioc

class SystemController(BaseController):
    @route("/api/state", "GET")
    @handle_errors
    async def get_state(self, request):
        state_service = self.ioc.resolve("state")
        summary = state_service.get_summary()
        return 200, "application/json", json.dumps(summary)

    @route("/api/scan", "GET")
    @handle_errors
    async def get_scan(self, request):
        wifi = self.ioc.resolve("wifi")
        results = wifi.scan() if wifi else []
        return 200, "application/json", json.dumps(results)

class AppController(BaseController):
    @route("/api/launch", "POST")
    @json_dto(LaunchRequestDto)
    @handle_errors
    async def launch(self, request, dto):
        app_mgr = self.ioc.resolve("app_manager")
        app_mgr.request_switch(dto.target)
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True, data={"target": dto.target}).to_dict())

    @route("/api/paint", "POST")
    @json_dto(PaintRequestDto)
    @handle_errors
    async def update_paint(self, request, dto):
        state = self.ioc.resolve("state")
        app_mgr = self.ioc.resolve("app_manager")
        if dto.pixels:
            state.paint_frames = [dto.pixels]
        if dto.frames:
            state.paint_frames = dto.frames
        state.paint_speed = dto.speed
        app_mgr.request_switch(10)
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True).to_dict())

    @route("/api/ticker", "POST")
    @json_dto(TickerRequestDto)
    @handle_errors
    async def update_ticker(self, request, dto):
        state = self.ioc.resolve("state")
        app_mgr = self.ioc.resolve("app_manager")
        state.ticker_text = dto.text
        state.ticker_color = dto.color
        state.ticker_speed = dto.speed
        app_mgr.request_switch(11)
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True).to_dict())

    @route("/api/studio", "POST")
    @json_dto(StudioRequestDto)
    @handle_errors
    async def update_studio(self, request, dto):
        state = self.ioc.resolve("state")
        app_mgr = self.ioc.resolve("app_manager")
        state.studio_effect = dto.effect
        state.studio_color = dto.color
        state.studio_speed = dto.speed
        app_mgr.request_switch(12)
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True).to_dict())

    @route("/api/fft/config", "POST")
    @json_dto(FftConfigRequestDto)
    @handle_errors
    async def set_fft_config(self, request, dto):
        state = self.ioc.resolve("state")
        state.fft_size = dto.size
        state.fft_sample_delay = dto.sample_delay
        state.fft_gain = dto.gain
        state.fft_window = dto.window
        state.fft_energy_scale = dto.energy_scale
        res = {
            "size": state.fft_size,
            "sample_delay": state.fft_sample_delay,
            "gain": state.fft_gain,
            "window": state.fft_window,
            "energy_scale": state.fft_energy_scale,
        }
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True, data=res).to_dict())

    @route("/api/fft/config", "GET")
    @handle_errors
    async def get_fft_config(self, request):
        state = self.ioc.resolve("state")
        res = {
            "size": state.fft_size,
            "sample_delay": state.fft_sample_delay,
            "gain": state.fft_gain,
            "window": state.fft_window,
            "energy_scale": state.fft_energy_scale,
        }
        return 200, "application/json", json.dumps(ApiResponseDto(ok=True, data=res).to_dict())

class StreamController(BaseController):
    @route("/events", "GET")
    async def sse_stream(self, request):
        state = self.ioc.resolve("state")
        writer = request.writer
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n\r\n"
        )
        writer.write(headers.encode("utf-8"))
        await writer.drain()

        last_raw = bytearray(90)
        last_heartbeat = time.ticks_ms()
        try:
            while True:
                curr = state.get_screen_raw()
                now = time.ticks_ms()
                if curr != last_raw or time.ticks_diff(now, last_heartbeat) > 4000:
                    b64 = ubinascii.b2a_base64(curr)
                    writer.write(b"data: " + b64 + b"\n")
                    await writer.drain()
                    last_raw[:] = curr
                    last_heartbeat = now
                await asyncio.sleep_ms(60)
        except Exception:
            pass
        return None, None, None # Stream closed

    @route("/events/fft", "GET")
    async def sse_fft_stream(self, request):
        state = self.ioc.resolve("state")
        writer = request.writer
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n\r\n"
        )
        writer.write(headers.encode("utf-8"))
        await writer.drain()

        last_seq = -1
        last_heartbeat = time.ticks_ms()
        try:
            while True:
                curr = state.get_fft_raw()
                seq = curr[0]
                now = time.ticks_ms()
                if seq != last_seq or time.ticks_diff(now, last_heartbeat) > 3000:
                    b64 = ubinascii.b2a_base64(curr)
                    writer.write(b"data: " + b64 + b"\n")
                    await writer.drain()
                    last_seq = seq
                    last_heartbeat = now
                await asyncio.sleep_ms(40)
        except Exception:
            pass
        return None, None, None
