# services/app_manager.py - Cooperative Task Preemption & Lifecycle Manager
import machine

class AppManager:
    """Manages cooperative preemption, lifecycle, and execution of apps."""
    def __init__(self, matrix, imu_service, state_service, button_pin=9):
        self.matrix = matrix
        self.imu_service = imu_service
        self.state = state_service
        self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.catalog = [] # list of (name, async_coroutine_fn)
        self.current_idx = 0
        self.active_ctx = None
        self.preempt_request = None

    def register(self, name, handler):
        self.catalog.append((name, handler))
        self.state.registered_apps = [{"id": i+1, "name": n} for i, (n, _) in enumerate(self.catalog)]

    def request_switch(self, target):
        """Preempt running app and switch to target."""
        self.preempt_request = target
        if self.active_ctx:
            self.active_ctx.request_exit()

    def find_index(self, target):
        if isinstance(target, int):
            if 1 <= target <= len(self.catalog):
                return target - 1
        elif isinstance(target, str):
            for i, (name, _) in enumerate(self.catalog):
                if name.lower() == target.lower():
                    return i
        return None
