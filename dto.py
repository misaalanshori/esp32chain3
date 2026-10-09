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
