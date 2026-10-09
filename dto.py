# dto.py - Data Transfer Objects (DTOs) for MVC Web Layer

class DTO:
    def to_dict(self):
        return self.__dict__

class LaunchRequestDto(DTO):
    def __init__(self, target):
        self.target = target

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")
        target = data.get("app") or data.get("name") or data.get("id")
        if target is None:
            raise ValueError("Missing 'app' or 'name' parameter")
        return cls(target)

class PaintRequestDto(DTO):
    def __init__(self, pixels=None, frames=None, speed=200):
        self.pixels = pixels
        self.frames = frames
        self.speed = int(speed)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")
        pixels = data.get("pixels")
        frames = data.get("frames")
        speed = data.get("speed", 200)
        return cls(pixels=pixels, frames=frames, speed=speed)

class TickerRequestDto(DTO):
    def __init__(self, text, color="#00ffff", speed=70):
        self.text = str(text)
        self.color = str(color)
        self.speed = int(speed)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")
        text = data.get("text", "")
        color = data.get("color", "#00ffff")
        speed = data.get("speed", 70)
        return cls(text=text, color=color, speed=speed)

class StudioRequestDto(DTO):
    def __init__(self, effect="candle", color="#ff8800", speed=40):
        self.effect = str(effect)
        self.color = str(color)
        self.speed = int(speed)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")
        effect = data.get("effect", "candle")
        color = data.get("color", "#ff8800")
        speed = data.get("speed", 40)
        return cls(effect=effect, color=color, speed=speed)

class FftConfigRequestDto(DTO):
    def __init__(self, size=128, sample_delay=3, gain=1.0, window="hann", energy_scale=0.2):
        s = int(size)
        self.size = 32 if s <= 32 else (64 if s <= 64 else 128)
        self.sample_delay = max(2, min(20, int(sample_delay)))
        self.gain = max(0.1, min(10.0, float(gain)))
        self.window = "rect" if str(window).lower() == "rect" else "hann"
        self.energy_scale = max(0.01, min(10.0, float(energy_scale)))

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")
        return cls(
            size=data.get("size", 128),
            sample_delay=data.get("sample_delay", 3),
            gain=data.get("gain", 1.0),
            window=data.get("window", "hann"),
            energy_scale=data.get("energy_scale", 0.2)
        )

class ApiResponseDto(DTO):
    def __init__(self, ok=True, data=None, error=None):
        self.ok = ok
        self.data = data
        self.error = error

    def to_dict(self):
        res = {"ok": self.ok}
        if self.data is not None:
            res["data"] = self.data
        if self.error is not None:
            res["error"] = self.error
        return res
