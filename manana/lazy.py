from __future__ import annotations

import importlib.util
import inspect
import sys
import time
from contextvars import ContextVar
from types import ModuleType

_ACTIVE_TRIGGER: ContextVar[tuple[str | None, int | None] | None] = ContextVar(
    "manana_active_trigger",
    default=None,
)

class LoadMetadata:

    __slots__ = ("name", "loaded", "load_time", "deferred_at", "trigger_file", "trigger_line")

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.loaded: bool = False
        self.load_time: float | None = None
        self.deferred_at: float = time.perf_counter()
        self.trigger_file: str | None = None
        self.trigger_line: int | None = None

    def __repr__(self) -> str:
        if self.loaded and self.load_time is not None:
            status = f"{self.load_time * 1000:.1f}ms"
        else:
            status = "not yet loaded"
        return f"<LoadMetadata {self.name!r} [{status}]>"


class _LoadWrapper:

    def __init__(self, real_loader, metadata: LoadMetadata) -> None:
        self._real = real_loader
        self._metadata = metadata

    def create_module(self, spec) -> ModuleType | None:
        if hasattr(self._real, "create_module"):
            return self._real.create_module(spec)
        return None

    def _capture_trigger_location(self) -> tuple[str | None, int | None]:
        frame = inspect.currentframe()
        try:
            current = frame.f_back if frame is not None else None
            while current is not None:
                filename = current.f_code.co_filename
                if filename != __file__ and "importlib" not in filename:
                    return filename, current.f_lineno
                current = current.f_back
        finally:
            # Avoid retaining frame references.
            del frame
        return None, None

    def exec_module(self, module: ModuleType) -> None:
        parent_trigger = _ACTIVE_TRIGGER.get()
        if parent_trigger is None:
            trigger = self._capture_trigger_location()
        else:
            trigger = parent_trigger

        self._metadata.trigger_file, self._metadata.trigger_line = trigger

        token = _ACTIVE_TRIGGER.set(trigger)
        start = time.perf_counter()
        try:
            self._real.exec_module(module)
            self._metadata.load_time = time.perf_counter() - start
            self._metadata.loaded = True
        finally:
            _ACTIVE_TRIGGER.reset(token)

class LazyModule:
    """
    `importlib.util.LazyLoader` wrapper
    """

    def __init__(self, name: str) -> None:
        metadata = LoadMetadata(name)
        object.__setattr__(self, "_lm_name", name)
        object.__setattr__(self, "_lm_metadata", metadata)

        if name in sys.modules:
            # Module was previously loaded
            metadata.loaded = True
            metadata.load_time = 0.0
            object.__setattr__(self, "_lm_module", sys.modules[name])
            return

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise ImportError(f"No module named {name!r}")

        if spec.loader is None:
            raise ImportError(f"Module {name!r} has no loader (namespace package?)")

        wrapped = _LoadWrapper(spec.loader, metadata)

        spec.loader = importlib.util.LazyLoader(wrapped)

        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module

        spec.loader.exec_module(module)

        object.__setattr__(self, "_lm_module", module)

    @property
    def _loaded(self) -> bool:
        return object.__getattribute__(self, "_lm_metadata").loaded

    @property
    def _load_time(self) -> float | None:
        return object.__getattribute__(self, "_lm_metadata").load_time

    @property
    def _metadata(self) -> LoadMetadata:
        return object.__getattribute__(self, "_lm_metadata")

    def __getattr__(self, item: str):
        module = object.__getattribute__(self, "_lm_module")
        return getattr(module, item)

    def __repr__(self) -> str:
        name = object.__getattribute__(self, "_lm_name")
        metadata = object.__getattribute__(self, "_lm_metadata")
        status = "loaded" if metadata.loaded else "deferred"
        return f"<LazyModule {name!r} [{status}]>"
