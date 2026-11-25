import importlib
import sys
import uuid
from collections.abc import Iterable
from datetime import datetime, UTC
from pathlib import Path
from types import ModuleType


def get_datetime() -> datetime:
    """
    Returns the current datetime in UTC.
    """
    return datetime.now(tz=UTC)


def get_uuid() -> uuid.UUID:
    """
    Returns a new random UUID.
    """
    return uuid.uuid4()


def _import_prefix(folder: Path) -> str:
    """
    Returns the dotted prefix that maps `folder` onto `sys.path`.

    The deepest `sys.path` entry that contains `folder` wins, so `src/user`
    resolves to `user.` (not `src.user.`) when `src/` is on `sys.path`.
    """
    candidates: list[tuple[int, str]] = []

    for entry in sys.path:
        base = Path(entry or ".").resolve()
        try:
            relative = folder.relative_to(base)
        except ValueError:
            continue

        parts = relative.parts
        if not all(part.isidentifier() for part in parts):
            continue

        candidates.append((len(parts), ".".join(parts)))

    if not candidates:
        raise ValueError(
            f"{folder} is not under any sys.path entry; add the directory that "
            "should act as the import root to sys.path first."
        )

    _, prefix = min(candidates)
    return f"{prefix}." if prefix else ""


def import_all_modules(
    folder: str | Path,
    *,
    exclude: Iterable[str] = (),
) -> list[ModuleType]:
    """
    Recursively imports every Python module under `folder`.

    Module names are resolved against the deepest `sys.path` entry containing
    `folder`, so both the project root and any subfolder work:

    - `import_all_modules("src")` imports `moderator.model`, ...
    - `import_all_modules("src/user")` imports `user.model`, ...

    `exclude` accepts dotted module names or top-level names; a name also
    excludes everything below it (e.g. `{"alembic"}` skips `alembic.env`).

    Returns the imported modules in deterministic path order. Import errors are
    propagated so a broken module fails loudly instead of being silently
    skipped.
    """
    root = Path(folder).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    prefix = _import_prefix(root)

    if isinstance(exclude, str):
        exclude = (exclude,)
    excluded = {name.strip(".") for name in exclude}
    modules: list[ModuleType] = []

    for path in sorted(root.rglob("*.py")):
        parts = list(path.relative_to(root).with_suffix("").parts)

        if "__pycache__" in parts:
            continue

        is_init = parts[-1] == "__init__"
        if is_init:
            parts.pop()

        if not all(part.isidentifier() for part in parts):
            continue

        if is_init and not parts:
            # The folder itself is the package: import it as `prefix`.
            if not prefix:
                continue
            module_name = prefix.removesuffix(".")
        else:
            module_name = prefix + ".".join(parts)

        if any(
            module_name == name or module_name.startswith(f"{name}.")
            for name in excluded
        ):
            continue

        modules.append(importlib.import_module(module_name))

    return modules
