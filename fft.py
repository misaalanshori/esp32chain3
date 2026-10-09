# fft.py - MicroPython Viper-Accelerated Configurable FFT Engine (up to 64 Bins / N=128)
import array
import math

MAX_N = 128
MAX_HALF_N = 64

def _bit_rev(x, bits):
    res = 0
    for _ in range(bits):
        res = (res << 1) | (x & 1)
        x >>= 1
    return res

# Precompute tables for N=32, N=64, N=128
BIT_REV_32 = tuple(_bit_rev(i, 5) for i in range(32))
BIT_REV_64 = tuple(_bit_rev(i, 6) for i in range(64))
BIT_REV_128 = tuple(_bit_rev(i, 7) for i in range(128))

COS_128 = tuple(int(round(math.cos(2 * math.pi * k / 128) * 16384)) for k in range(64))
SIN_128 = tuple(int(round(math.sin(2 * math.pi * k / 128) * 16384)) for k in range(64))

HANN_32 = tuple(int(round((1.0 - math.cos(2 * math.pi * i / 31)) * 0.5 * 16384)) for i in range(32))
HANN_64 = tuple(int(round((1.0 - math.cos(2 * math.pi * i / 63)) * 0.5 * 16384)) for i in range(64))
HANN_128 = tuple(int(round((1.0 - math.cos(2 * math.pi * i / 127)) * 0.5 * 16384)) for i in range(128))

_cos_arr = array.array('i', COS_128)
_sin_arr = array.array('i', SIN_128)

_rev32_arr = array.array('i', BIT_REV_32)
_rev64_arr = array.array('i', BIT_REV_64)
_rev128_arr = array.array('i', BIT_REV_128)

_hann32_arr = array.array('i', HANN_32)
_hann64_arr = array.array('i', HANN_64)
_hann128_arr = array.array('i', HANN_128)

@micropython.viper
def remove_dc_and_window(src_p: ptr32, dst_p: ptr32, hann_p: ptr32, n: int, use_window: int):
    sum_val = 0
    for i in range(n):
        sum_val += int(src_p[i])
    mean = sum_val // n
    for i in range(n):
        diff = int(src_p[i]) - mean
        if use_window:
            w = int(hann_p[i])
            dst_p[i] = (diff * w) >> 14
        else:
            dst_p[i] = diff

@micropython.viper
def fft_radix2_viper(re_ptr: ptr32, im_ptr: ptr32,
                     cos_p: ptr32, sin_p: ptr32, rev_p: ptr32, n: int):
    # 1. Bit-reversal permutation
    for i in range(n):
        j = int(rev_p[i])
        if i < j:
            tr = int(re_ptr[i]); re_ptr[i] = int(re_ptr[j]); re_ptr[j] = tr
            ti = int(im_ptr[i]); im_ptr[i] = int(im_ptr[j]); im_ptr[j] = ti

    # 2. Butterfly stages
    stage_len = 2
    while stage_len <= n:
        half_len = stage_len >> 1
        step = 128 // stage_len
        i = 0
        while i < n:
            k = 0
            while k < half_len:
                idx = k * step
                wr = int(cos_p[idx])
                wi = int(sin_p[idx])

                p = i + k
                q = p + half_len

                qr = int(re_ptr[q])
                qi = int(im_ptr[q])

                tr = (wr * qr + wi * qi) >> 14
                ti = (wr * qi - wi * qr) >> 14

                pr = int(re_ptr[p])
                pi_val = int(im_ptr[p])

                re_ptr[q] = pr - tr
                im_ptr[q] = pi_val - ti

                re_ptr[p] = pr + tr
                im_ptr[p] = pi_val + ti

                k += 1
            i += stage_len
        stage_len <<= 1

@micropython.viper
def calc_mag_approx(re_p: ptr32, im_p: ptr32, mag_p: ptr32, half_n: int):
    for i in range(half_n):
        r = int(re_p[i])
        im_val = int(im_p[i])
        if r < 0: r = -r
        if im_val < 0: im_val = -im_val
        mx = r if r > im_val else im_val
        mn = im_val if r > im_val else r
        mag_p[i] = mx + ((mn * 3) >> 3)

class FastFFT:
    """Configurable 3-Axis FFT Engine supporting 16, 32, or 64 bins (N=32, 64, 128)."""
    def __init__(self, size=128):
        self.size = 128
        self.half_n = 64
        self.re = array.array('i', [0] * MAX_N)
        self.im = array.array('i', [0] * MAX_N)
        self.mag_x = array.array('i', [0] * MAX_HALF_N)
        self.mag_y = array.array('i', [0] * MAX_HALF_N)
        self.mag_z = array.array('i', [0] * MAX_HALF_N)
        self.set_size(size)

    def set_size(self, size):
        if size <= 32:
            self.size = 32
            self.half_n = 16
            self.rev_arr = _rev32_arr
            self.hann_arr = _hann32_arr
        elif size <= 64:
            self.size = 64
            self.half_n = 32
            self.rev_arr = _rev64_arr
            self.hann_arr = _hann64_arr
        else:
            self.size = 128
            self.half_n = 64
            self.rev_arr = _rev128_arr
            self.hann_arr = _hann128_arr

    def process_axis(self, raw_samples, mag_out, use_window=True):
        n = self.size
        half_n = self.half_n
        remove_dc_and_window(raw_samples, self.re, self.hann_arr, n, 1 if use_window else 0)
        for i in range(n):
            self.im[i] = 0
        fft_radix2_viper(self.re, self.im, _cos_arr, _sin_arr, self.rev_arr, n)
        calc_mag_approx(self.re, self.im, mag_out, half_n)

    def process_3axis(self, x_samps, y_samps, z_samps, use_window=True):
        self.process_axis(x_samps, self.mag_x, use_window)
        self.process_axis(y_samps, self.mag_y, use_window)
        self.process_axis(z_samps, self.mag_z, use_window)
        total_e = 0
        for i in range(1, self.half_n):
            total_e += self.mag_x[i] + self.mag_y[i] + self.mag_z[i]
        return self.mag_x, self.mag_y, self.mag_z, total_e, self.half_n
