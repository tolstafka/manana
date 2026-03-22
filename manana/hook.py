from __future__ import annotations

import importlib.util
import sys
from typing import Sequence

from manana.lazy import LazyModule, LoadMetadata, _LoadWrapper

_ALWAYS_EAGER: frozenset[str] = frozenset({
    "manana",
    "sys", "builtins", "os", "os.path", "abc", "io",
    "threading", "types", "typing", "typing_extensions",
    "functools", "operator", "itertools",
    "collections", "collections.abc",
    "importlib", "importlib.util", "importlib.abc",
    "importlib.machinery", "importlib.metadata",
    "_thread", "_warnings", "_weakref", "_weakrefset",
    "codecs", "encodings", "encodings.utf_8",
    "re", "sre_compile", "sre_parse", "sre_constants",
    "site", "sitecustomize", "usercustomize",
    "genericpath", "posixpath", "ntpath",
    "stat", "warnings", "linecache", "tokenize",
    "traceback", "inspect",
})


def _should_defer(fullname: str) -> bool:
    """
    Defer UNLESS an _ALWAYS_EAGER package or a submodule of an _ALWAYS_EAGER package
    """

    if fullname == "manana" or fullname.startswith("manana."):
        return False
    if fullname in _ALWAYS_EAGER:
        return False
    # submodules like `os.path`
    root = fullname.split(".")[0]
    if root in _ALWAYS_EAGER:
        return False
    return True


class MananaFinder:

    def __init__(self) -> None:
        self._records: dict[str, LoadMetadata] = {}
        self._loading: set[str] = set()

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target=None,
    ):
        
        # Check for modules to never defer
        if not _should_defer(fullname):
            return None

        # Check for modules currently loading
        if fullname in self._loading:
            return None

        # Check for modules already loaded
        if fullname in sys.modules:
            return None

        self._loading.add(fullname)
        try:
            sys.meta_path.remove(self)
            try:
                spec = importlib.util.find_spec(fullname)
            finally:
                sys.meta_path.insert(0, self)

            if spec is None or spec.loader is None:
                return None

            record = LoadMetadata(fullname)
            self._records[fullname] = record

            instrumented = _LoadWrapper(spec.loader, record)
            spec.loader = importlib.util.LazyLoader(instrumented)

            return spec

        except (ModuleNotFoundError, ValueError, AttributeError):
            # default to the regular Python loaders
            return None
        finally:
            self._loading.discard(fullname)


    @property
    def records(self) -> dict[str, LoadMetadata]:
        """All LoadMetadatas created by this finder, keyed by module name."""
        return dict(self._records)

    def record_for(self, name: str) -> LoadMetadata | None:
        """Return the LoadMetadata for a specific module, or None."""
        return self._records.get(name)

_finder: MananaFinder | None = None

def activate() -> MananaFinder:
    global _finder
    if _finder is not None and _finder in sys.meta_path:
        return _finder
    _finder = MananaFinder()
    sys.meta_path.insert(0, _finder)
    return _finder


def deactivate() -> None:
    global _finder
    if _finder is not None and _finder in sys.meta_path:
        sys.meta_path.remove(_finder)
    _finder = None


def is_active() -> bool:
    return _finder is not None and _finder in sys.meta_path


def get_finder() -> MananaFinder | None:
    return _finder if is_active() else None