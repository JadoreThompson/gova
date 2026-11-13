from __future__ import annotations

import importlib
import inspect
from collections.abc import Iterable, Mapping

from fastapi import HTTPException

from config import SRC_FOLDER


class ExceptionHandler:
    """Base class for package-level exception handlers.

    Subclasses declare an ``exceptions`` mapping of service exceptions to the
    ``HTTPException`` that should be returned for them.
    """

    exceptions: Mapping[type[Exception], HTTPException] = {}

    @classmethod
    def mapping(cls) -> Mapping[type[Exception], HTTPException]:
        return cls.exceptions


def discover_exception_handlers() -> Iterable[type[ExceptionHandler]]:
    """Find ``ExceptionHandler`` subclasses in packages that have a router."""
    for path in SRC_FOLDER.iterdir():
        if not path.is_dir() or not (path / "router.py").is_file():
            continue
        if not (path / "exception.py").is_file():
            continue

        module = importlib.import_module(f"{path.name}.exception")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, ExceptionHandler)
                and obj is not ExceptionHandler
                and obj.__module__ == module.__name__
            ):
                yield obj


def load_exception_handlers(
    handlers: Iterable[type[ExceptionHandler]] | None = None,
) -> dict[type[Exception], HTTPException]:
    """Build an exception-to-HTTPException map from the given handlers."""
    handler_classes = (
        handlers if handlers is not None else discover_exception_handlers()
    )

    exception_map: dict[type[Exception], HTTPException] = {}
    for handler in handler_classes:
        exception_map.update(handler.mapping())
    return exception_map
