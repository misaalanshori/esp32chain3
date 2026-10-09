# apps/__init__.py - Application Package Aggregate & Registry
from apps.rainbow import app_rainbow
from apps.jedagjedug import app_jedagjedug
from apps.bubble import app_bubble
from apps.dice import app_dice
from apps.pong import app_pong
from apps.hourglass import app_hourglass
from apps.life import app_life
from apps.fire import app_fire
from apps.reflex import app_reflex
from apps.paint import app_paint
from apps.ticker import app_ticker
from apps.studio import app_studio
from apps.mpu_fft import app_fft

REGISTERED_APPS = (
    ("Rainbow", app_rainbow),
    ("JedagJedug", app_jedagjedug),
    ("BubbleLevel", app_bubble),
    ("ShakeDice", app_dice),
    ("TiltPong", app_pong),
    ("Hourglass", app_hourglass),
    ("GameOfLife", app_life),
    ("FireSim", app_fire),
    ("ReflexGame", app_reflex),
    ("WebPaint", app_paint),
    ("WebTicker", app_ticker),
    ("WebStudio", app_studio),
    ("MPU_FFT", app_fft),
)
