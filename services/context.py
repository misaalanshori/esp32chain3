# services/context.py - Execution Context Injected into Applications
import time
import asyncio

class AppContext:
    """Execution context injected into every running application."""
    def __init__(self, matrix, imu_service, state_service, app_manager):
        self.matrix = matrix
        self.imu_service = imu_service
        self.state = state_service
        self.app_manager = app_manager
        self._stop = False

    def request_exit(self):
        self._stop = True

    def should_stop(self):
        return self._stop or (self.app_manager.preempt_request is not None)

    async def sleep_ms(self, ms):
        await asyncio.sleep_ms(ms)

    def get_imu(self):
        return self.imu_service.get_imu()

    def poll_action(self, btn, hold_ms=450):
        if self.should_stop():
            return "exit"
        if btn.value() == 0:
            t0 = time.ticks_ms()
            while btn.value() == 0:
                if time.ticks_diff(time.ticks_ms(), t0) >= hold_ms:
                    while btn.value() == 0:
                        time.sleep_ms(10)
                    time.sleep_ms(30)
                    return "exit"
                time.sleep_ms(10)
            time.sleep_ms(20)
            return "tap"
        return None
