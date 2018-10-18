from collections import ChainMap
from typing import Any, Dict


class Config:
    _backing = ChainMap()
    _parent = None

    def __init__(self, parent: 'Config' = None):
        if parent:
            self._backing = parent._backing.new_child()
            self._parent = parent

    def __contains__(self, item: str) -> bool:
        return item in self._backing

    def __getitem__(self, item: str) -> Any:
        val = self._backing[item]
        if callable(val):
            return val(self)
        else:
            return val

    def __setitem__(self, key: str, value: Any):
        self._backing[key] = value

    def default(self, key: str, default_value: Any):
        if key not in self._backing:
            self._backing[key] = default_value

    def defaults(self, prefix: str, values: Dict[str, Any]):
        prefix = prefix if prefix else ""
        for key, value in values.items():
            self.default(prefix + "_" + key, value)

    def add_all(self, prefix: str, values: Dict[str, Any]):
        prefix = prefix if prefix else ""
        for key, value in values.items():
            self[prefix + "_" + key] = value

    def new_child(self, prefix: str = None, root: Any = None, values: Dict[str, Any] = None) -> 'Config':
        config = Config(self)
        if root and prefix:
            config[prefix] = root
        if values:
            config.add_all(prefix, values)
        return config
