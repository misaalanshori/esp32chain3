# container.py - Lightweight Inversion of Control (IoC) & Dependency Injection Container

class Container:
    def __init__(self):
        self._singletons = {}
        self._factories = {}

    def register_singleton(self, key, instance):
        """Register an existing object as a singleton."""
        self._singletons[key] = instance
        return instance

    def register_factory(self, key, factory_fn):
        """Register a factory callable (fn(container) -> instance)."""
        self._factories[key] = factory_fn

    def resolve(self, key):
        """Resolve a registered service dependency by key."""
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            instance = self._factories[key](self)
            return instance
        raise KeyError(f"Dependency '{key}' not found in IoC container")

    def has(self, key):
        return (key in self._singletons) or (key in self._factories)

# Global default IoC Container
ioc = Container()
