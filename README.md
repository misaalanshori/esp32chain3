# ESP32-C3 Pin Mapping

## Peripherals & Pins

| Peripheral | Function / Signal | ESP32-C3 GPIO | Notes |
|------------|-------------------|---------------|-------|
| **NeoPixel Matrix** | DIN (Data) | `GPIO 7` | 6x5 matrix (30 LEDs), serpentine layout |
| **Boot Button** | Input (Active LOW) | `GPIO 9` | Short press: cycle apps, Long press: open app / exit |
| **MPU6050 (GY-521)** | VCC / Power Control | `GPIO 2` | Output HIGH to power sensor |
| | SDA | `GPIO 3` | SoftI2C (`mpu = MPU6050(i2c=...)`) |
| | SCL | `GPIO 4` | SoftI2C |
| | I2C Address | `0x68` | Default address |

## Menu System (`menu.py`)

- **Short press (< 600ms)**: Cycles through registered apps (shows digit 1..9 in 3x5 font).
- **Hold (600ms)**: Column 5 fills up as a hold meter. When full, flashes and opens the app.
- **Exit app (optional)**: Holding BOOT for > 500ms exits back to the menu if the app uses `check_exit(btn)`.

### Registered Apps (`apps.py`):
1. `Rainbow`: Animated RGB wave on matrix.
2. `JedagJedug`: Fast color wheel cycle across the matrix.
3. `BubbleLevel`: Interactive tilt level using MPU6050.
4. `ShakeDice`: Physical board shake (or tap) to roll 1–6 with tumble animation.
5. `TiltPong`: Single-player arcade paddle game steered by IMU tilt.
6. `Hourglass`: Physics falling sand particles reacting to gravity orientation.
7. `GameOfLife`: Conway's cellular automata with toroidal wrap and cell aging.
8. `FireSim`: Rising ember flame diffusion with multiple color palettes.
9. `ReflexGame`: Reaction time tester measuring milliseconds to sudden green flash.
10. `WebPaint`: Interactive browser pixel canvas and animation player.
11. `WebTicker`: Live text marquee scroller with 3×5 font controlled via browser.
12. `WebStudio`: Mood lamp and ambient lighting studio with live browser presets.

## Framework Architecture

Built on an embedded, decoupled **MVC + IoC/DI + AOP** framework on top of a unified cooperative `uasyncio` event loop:

- **`container.py` (Inversion of Control & Dependency Injection)**: Central `Container` resolving singletons and factories (`state`, `matrix`, `imu`, `wifi`, `app_manager`, `webserver`).
- **`dto.py` (Data Transfer Objects)**: Strictly-validated request/response DTOs (`LaunchRequestDto`, `PaintRequestDto`, `TickerRequestDto`, `StudioRequestDto`, `ApiResponseDto`).
- **`aop.py` (Aspect-Oriented Programming)**:
  - `@route(path, method)`: Declarative MVC route binding aspect.
  - `@json_dto(DtoClass)`: Cross-cutting aspect automatically parsing/validating JSON payload into DTO.
  - `@handle_errors`: Exception boundary aspect generating uniform error DTOs.
  - `@timed`: Execution duration and telemetry aspect.
- **`controllers.py` (MVC Controllers)**: `SystemController`, `AppController`, `StreamController`.
- **`services.py` (Domain Services)**: `StateService`, `MatrixService`, `IMUService`, and `AppManager` (managing cooperative task preemption).
- **`apps.py` (Cooperative Micro-Apps)**: All 12 apps run as non-blocking async tasks with cooperative preemption, yielding to the event loop on every frame.
- **`menu.py` (Async Menu Engine)**: Non-blocking physical button polling and 3×5 / 2-digit number renderer.
- **`webserver.py`**: Async HTTP server routing requests through controller actions and streaming views in 1460-byte chunks.
- **`main.py`**: Framework bootstrap and unified single-loop `asyncio.gather()` runner (zero `_thread` stack overhead).

## Multi WiFi Manager (`wifi_manager.py`)

- **Auto-connect & Switch**: Priority-based connecting across configured SSIDs in `secrets.py`.
- **Auto-reconnect**: Detects dropped connections and restores STA link.
- **Auto-AP fallback**: Starts `ESP32-Chain3` AP (`192.168.4.1`) if no known networks are reachable, and periodically scans to resume STA mode.

### Setup Credentials (`secrets.py`)
Copy `secrets.py.example` to `secrets.py` (which is in `.gitignore`):
```python
WIFI_NETWORKS = [
    ("MainSSID", "MainPassword"),
    ("SecondarySSID", "SecondaryPassword"),
]
```

## Async Web Server (`webserver.py`)

Runs as a background async task on port 80 at boot.

- `GET /`: Responsive dark-mode dashboard with live status updates and real-time screen mirror.
- `GET /events`: **Server-Sent Events (SSE)** binary stream (90 raw RGB bytes base64-encoded to 120 chars, zero heap allocation, `~16 FPS` on screen updates, idle heartbeat every 5s).
- `GET /api/state`: Full system state JSON endpoint (RAM, WiFi, App, Sensors, Screen).
- `GET /api/scan`: Trigger WiFi scan and return visible networks.
- `POST /api/launch`: Remotely switch running apps or return to menu (`{"app": 1..12}` or `{"app": "menu"}`).
- `POST /api/paint`: Push custom 30-LED pixel array for `WebPaint`.
- `POST /api/ticker`: Push text and color for `WebTicker`.
- `POST /api/studio`: Push procedural lighting effects for `WebStudio`.

