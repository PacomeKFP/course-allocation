"""Helpers transverses (sans dépendance métier)."""
from __future__ import annotations
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def group_by(items: Iterable[T], key: Callable[[T], K]) -> dict[K, list[T]]:
    """Regroupe ``items`` en dict ``{clé: [items...]}`` selon ``key``."""
    out: dict[K, list[T]] = {}
    for it in items:
        out.setdefault(key(it), []).append(it)
    return out
