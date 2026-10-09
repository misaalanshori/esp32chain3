# fft.py - MicroPython Viper-Accelerated 32-Point FFT & Spectral Analysis Library
import array
import math

N = 32
HALF_N = 16

BIT_REV = (
    0, 16, 8, 24, 4, 20, 12, 28, 2, 18, 10, 26, 6, 22, 14, 30,
    1, 17, 9, 25, 5, 21, 13, 29, 3, 19, 11, 27, 7, 23, 15, 31
)
COS_Q14 = tuple(int(round(math.cos(2 * math.pi * k / N) * 16384)) for k in range(HALF_N))
SIN_Q14 = tuple(int(round(math.sin(2 * math.pi * k / N) * 16384)) for k in range(HALF_N))
HANNING_Q14 = tuple(int(round((1.0 - math.cos(2 * math.pi * i / (N - 1))) * 0.5 * 16384)) for i in range(N))

_cos_arr = array.array('i', COS_Q14)
_sin_arr = array.array('i', SIN_Q14)
_bitrev_arr = array.array('i', BIT_REV)
_hann_arr = array.array('i', HANNING_Q14)

@micropython.viper
def remove_dc_and_window(src_p: ptr32, dst_p: ptr32, hann_p: ptr32, n: int):
    sum_val = 0
    for i in range(n):
        sum_val += int(src_p[i])
    mean = sum_val // n
    for i in range(n):
        diff = int(src_p[i]) - mean
        w = int(hann_p[i])
        dst_p[i] = (diff * w) >> 14

@micropython.viper
def fft32_viper(re_ptr: ptr32, im_ptr: ptr32,
                cos_p: ptr32, sin_p: ptr32, rev_p: ptr32):
    n = 32
    # 1. Bit-reversal permutation
    for i in range(n):
        j = int(rev_p[i])
        if i < j:
            tr = int(re_ptr[i])
            re_ptr[i] = int(re_ptr[j])
            re_ptr[j] = tr
            ti = int(im_ptr[i])
            im_ptr[i] = int(im_ptr[j])
            im_ptr[j] = ti

    # 2. Cooley-Tukey butterfly stages
    stage_len = 2
    while stage_len <= n:
        half_len = stage_len >> 1
        step = n // stage_len
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
    # Alpha-max beta-min: mag = max(|re|, |im|) + 3/8 * min(|re|, |im|)
    for i in range(half_n):
        r = int(re_p[i])
        im_val = int(im_p[i])
        if r < 0: r = -r
        if im_val < 0: im_val = -im_val
        mx = r if r > im_val else im_val
        mn = im_val if r > im_val else r
        mag_p[i] = mx + ((mn * 3) >> 3)

class FastFFT32:
    """Preallocated 3-Axis FFT engine with zero heap allocation during execution."""
    def __init__(self):
        self.re = array.array('i', [0] * N)
        self.im = array.array('i', [0] * N)
        self.mag_x = array.array('i', [0] * HALF_N)
        self.mag_y = array.array('i', [0] * HALF_N)
        self.mag_z = array.array('i', [0] * HALF_N)

    def process_axis(self, raw_samples, mag_out):
        remove_dc_and_window(raw_samples, self.re, _hann_arr, N)
        for i in range(N):
            self.im[i] = 0
        fft32_viper(self.re, self.im, _cos_arr, _sin_arr, _bitrev_arr)
        calc_mag_approx(self.re, self.im, mag_out, HALF_N)

    def process_3axis(self, x_samples, y_samples, z_samples):
        self.process_axis(x_samples, self.mag_x)
        self.process_axis(y_samples, self.mag_y)
        self.process_axis(z_samples, self.mag_z)
        total_e = 0
        for i in range(1, HALF_N):
            total_e += self.mag_x[i] + self.mag_y[i] + self.mag_z[i]
        return self.mag_x, self.mag_y, self.mag_z, total_e
