
from .config import Config
from typing import Callable


class Procedure:

    def run(self, x: int) -> float:
        pass

    def is_outdated(self) -> bool:
        return False


class CompositeProcedure(Procedure):

    def __init__(self, runner: Callable[[int], float], outdated: Callable[[], bool]):
        self.runner = runner
        self.outdated = outdated

    def run(self, x: int) -> float:
        return self.runner(x)

    def is_outdated(self):
        return self.outdated()


# TODO - Generalize and reuse this class for GraphGenerator
class ProcedureGenerator:

    def __init__(self, config: Config, generator: Callable[[Config], Procedure]):
        self.config = config
        self._generator = generator

    def __call__(self, *args, **kwargs) -> 'ProcedureGenerator':
        return ProcedureGenerator(self.config.new_child(self.config.prefix, values=kwargs), self._generator)

    def generate(self, exp_config: Config) -> Procedure:
        return self._generator(self.config.as_child(exp_config))

