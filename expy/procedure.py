import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from typing import Callable, cast, Dict, Iterable, List, Sequence, Tuple, Union
import subprocess
import pickle
from collections import OrderedDict
from pathlib import Path


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


# rows, cols, index
GraphPosition = Tuple[int, int, int]
# Graphers create a grap
# pos: GraphPosition, x: List[int], y: List[float]
Grapher = Callable[[GraphPosition, List[int], Dict[str, List[float]]], None]


class ExperimentResult:

    def __init__(self, x_data: List[int], data: Dict[str, List[float]]):
        self.data = data
        self.x_data = x_data

    def __getitem__(self, proc: str) -> Dict[int, float]:
        return OrderedDict((x, self.data[proc][index]) for index, x in enumerate(self.x_data))

    def create_graph(self, path: str, title: str, *args):
        rows = len(args)
        cols = 2
        plt.figure(1)
        plt.suptitle(title, fontsize=12)
        for index, view in enumerate(args):
            # Every Grapher gets two index slots, the graph and the table next to it
            view((rows, cols, index * 2 + 1), self.x_data, self.data)
        plt.tight_layout()
        plt.subplots_adjust(top=0.88)
        plt.savefig(path, dpi=1000)
        plt.clf()

    @staticmethod
    def load(path: Path) -> 'ExperimentResult':
        with path.open('rb') as f:
            return pickle.load(f)

    def save(self, path: Path):
        with path.open('wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)


def run_experiment(x_range: Iterable[int], procedures: Dict[str, Procedure] = None) -> ExperimentResult:
    procedures = OrderedDict(procedures) if procedures else OrderedDict()

    x_data = list(x_range)
    data = OrderedDict((name, [experiment.run(x) for x in x_range]) for name, experiment in procedures.items())
    return ExperimentResult(x_data, data)


def mean(numbers: List[float]) -> float:
    return float(sum(numbers)) / max(len(numbers), 1)


def exec_command(command: List[str], env: Dict[str, str]) -> str:
    sub = subprocess.run(args=command, env=env, stdout=subprocess.PIPE)
    return sub.stdout.decode("utf-8")


###
# Graphing options
###
def graph_and_table(pos: GraphPosition, x_data: List[int], data: Dict[str, List[float]],
                    title: str, y_label: str = None, x_label: str = None):
    if not y_label:
        y_label = title
    if not x_label:
        x_label = 'Threads'
    plt.subplot(pos[0], pos[1], pos[2])
    plt.title(title)
    plt.locator_params(axis='y', nbins=6)
    ticks = list(range(0, len(x_data)))
    tick_labels = [str(x) for x in x_data]
    for name, y_data in data.items():
        plt.plot(ticks, y_data, label=name)
    if len(data) > 1:
        plt.legend(loc='best')

    plt.xticks(ticks, tick_labels)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.ylim(ymin=0)
    # Put it adjacent to the graph, assuming the two share a row.
    table = plt.subplot(pos[0], pos[1], pos[2]+1, frame_on=False)
    table.xaxis.set_visible(False)
    table.yaxis.set_visible(False)
    labels = [x_label]
    for key in data.keys():
        labels.append(key)
    cells = []
    for index, x in enumerate(x_data):
        cells.append([str(x)])
        for y_data in data.values():
            cells[index].append("{:0.5f}".format(y_data[index]))

    plt.table(colLabels=labels, cellText=cells, loc='center')


def simple_grapher(title: str, mapper: Callable[[List[float]], List[float]], y_label: str= None, x_label: str = None) -> Grapher:
    def apply(pos: GraphPosition, x_data: List[int], y_data: Dict[str, List[float]]):
        data = OrderedDict((key, mapper(data)) for key, data in y_data.items())
        graph_and_table(pos, x_data, data, title, y_label, x_label)
    return apply


def dependent_grapher(title: str, mapper: Callable[[List[int], List[float]], List[float]], y_label: str= None, x_label: str = None) -> Grapher:
    def apply(pos: GraphPosition, x_data: List[int], y_data: Dict[str, List[float]]):
        data = OrderedDict((key, mapper(x_data, data)) for key, data in y_data.items())
        graph_and_table(pos, x_data, data, title, y_label, x_label)
    return apply


def transformed_grapher(title: str, mapper: Callable[[int, float], float], x_label: str= None, y_label: str = None) -> Grapher:
    return dependent_grapher(title, lambda x_data, y_data: [mapper(x, y_data[index]) for index, x in enumerate(x_data)], y_label, x_label)


def speedup(x_label: str = None) -> Grapher:
    return dependent_grapher("Speedup", lambda x_data, y_data: [y_data[0] / y for y in y_data], x_label=x_label)


def identity(title: str = None, x_label: str = None, y_label: str = None) -> Grapher:
    if not title:
        title = "Execution Time"
    return simple_grapher(title, y_label=y_label, x_label=x_label, mapper=lambda data: data)


def efficiency(x_label: str = None) -> Grapher:
    return dependent_grapher("Efficiency", lambda x_data, y_data: [y_data[0] / y_data[index] / x for index, x in enumerate(x_data)], x_label=x_label)



