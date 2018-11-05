from collections import ChainMap
from typing import Any, Dict, Sequence

CONFIG_NS = {"env", "cmd", "exp", "pres", "view"}


class Config:
    _backing = ChainMap()
    parent = None

    def __init__(self, prefix: str, parent: 'Config' = None):
        self.prefix = prefix
        if parent:
            self._backing = parent._backing.new_child()
            self.parent = parent

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

    def defaults(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self:
                self[self.prefix + "_" + key] = value

    def add_all(self, values: Dict[str, Any]):
        for key, value in values.items():
            if key.find("_") != -1 and key[::key.find("_")] in CONFIG_NS:
                self[key] = value
            else:
                self[self.prefix + "_" + key] = value

    def new_child(self, prefix: str, root: Any = None, values: Dict[str, Any] = None) -> 'Config':
        """
        Creates a new child of this configuration with the specified prefix and values.

        All values specified are prefixed with the specified prefix followed by an underscore,
        unless their prefix matches a prefix of a Config object higher in the hierarchy.

        :param prefix: The prefix for the newly created config
        :param root: A value to be associated with exactly the prefix.  Optional.
        :param values: A Dict of values(typically coming from another method's kwargs) to place
        into the newly created config object. Optional.
        """
        config = Config(prefix, self)
        if root and prefix:
            config[prefix] = root
        if values:
            config.add_all(values)
        return config

    def as_child(self, other: 'Config') -> 'Config':
        new_child = Config(other.prefix, self)
        # Copy only values added the level of other, not values from its parents
        new_child.add_all(other._backing.maps[0])
        return new_child
