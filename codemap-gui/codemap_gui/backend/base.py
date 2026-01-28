from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class SymbolKind(str, Enum):
    FUNCTION = "function"
    STRUCT = "struct"
    MACRO = "macro"
    TYPEDEF = "typedef"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SymbolSummary:
    name: str
    kind: SymbolKind = SymbolKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class OneHop:
    center: str
    callers: Sequence[str]
    callees: Sequence[str]
    callsites: Sequence[str]

@dataclass(frozen=True, slots=True)
class ProjectInfo:
    root_dir: str
    workspace_dir: str
    index_json_path: str



class CodeMapBackend(ABC):
    """Backend interface for the GUI.

    GUI talks only to this. Today it's MockBackend.
    Tomorrow it's JsonBackend reading your _callgraph_callsites.json.
    """

    @abstractmethod
    def open_project(self, root_dir: str) -> ProjectInfo:
        raise NotImplementedError


    @abstractmethod
    def list_files(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_outline(self, filename: str) -> list[SymbolSummary]:
        raise NotImplementedError

    @abstractmethod
    def one_hop(self, symbol: str) -> OneHop:
        raise NotImplementedError
