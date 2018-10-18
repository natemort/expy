
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


ProcedureGenerator = Callable[[Config], Procedure]
