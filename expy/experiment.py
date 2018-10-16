import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from typing import Callable, cast, Dict, Iterable, List, Sequence, Tuple, Union
import subprocess
import re
import os
import pickle
from collections import OrderedDict


# An experiment is simply a function that takes a number of threads, and returns how long it took
# with that number of threads
# Any details, such as how many trials to perform, is a detail of the experiment
Experiment = Callable[[int], float]
# rows, cols, index
GraphPosition = Tuple[int, int, int]
# Graphers create a grap
# pos: GraphPosition, x: List[int], y: List[float]
Grapher = Callable[[GraphPosition, List[int], Dict[str, List[float]]], None]


class ExperimentResult:

    def __init__(self, x_data: List[int], data: Dict[str, List[float]]):
        self.data = data
        self.x_data = x_data

    def __getitem__(self, exp: str) -> Dict[int, float]:
        return OrderedDict((x, self.data[exp][index]) for index, x in enumerate(self.x_data))

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
    def load(path: str) -> 'ExperimentResult':
        with open(path + '.experiment', 'rb') as f:
            return pickle.load(f)

    def save(self, path: str):
        with open(path + '.experiment', 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)


def load_or_run(name: str, x_range: Iterable[int], **kwargs) -> ExperimentResult:
    results = ExperimentResult.load(name)
    if not results:
        results = run_experiment(x_range, kwargs=kwargs)
        results.save(name)
    return results


def run_experiment(x_range: Iterable[int],  experiments: Dict[str, Experiment] = None, **kwargs) -> ExperimentResult:
    experiments = OrderedDict(experiments) if experiments else OrderedDict()
    for key, experiment in kwargs.items():
        experiments[key] = experiment
    x_data = list(x_range)
    data = OrderedDict((name, [experiment(x) for x in x_range]) for name, experiment in experiments.items())
    return ExperimentResult(x_data, data)


def mean(numbers: List[float]) -> float:
    return float(sum(numbers)) / max(len(numbers), 1)


def exec_command(command: List[str], env: Dict[str, str]) -> str:
    sub = subprocess.run(args=command, env=env, stdout=subprocess.PIPE)
    return sub.stdout.decode("utf-8")


###
# Experiment generators
###
def run_command(cmd: Union[List[str], Callable[[int], List[str]]],
                env: Union[Dict[str, str], Callable[[int], Dict[str, str]]] = None,
                trials: int = 5,
                pattern: str = ".*([0-9.]+).*") -> Experiment:
    """Runs the specified command 'trials' times, with the environment created by 'env_builder'

    Timing data is reported by the program itself, and by searching the program's output for 'pattern'.
    Because run_command only runs an arbitrary command, it has no mechanism for specifying the number of threads
    to use.  The program must be able to receive the number of threads to use from an environmental variable.
    'env_builder' is a function that receives the number of threads to use, and then generates an environment to
    call the subprocess with, and ultimately controls the number of threads that the program is run with.
    run_command reports the average of the run times.

    """
    if not env:
        env = {}

    def run(threads: int) -> float:
        times = []
        environment = env(threads) if not isinstance(env, dict) else env
        command = cmd(threads) if not isinstance(cmd, list) else cmd
        for trial in range(trials):
            search = re.search(pattern, exec_command(command, environment))
            if not search:
                raise RuntimeError("Unable to parse output")
            times.append(float(search.group(1)))
        print(threads, " -> ", command, " : ", mean(times))
        return mean(times)
    return run


def omp_env(defaults: Dict[str, str] = None) -> Callable[[int], Dict[str, str]]:
    def build_env(threads: int) -> Dict[str, str]:
        result = dict(defaults) if defaults else {}
        result["OMP_NUM_THREADS"] = str(threads)
        return result
    return build_env


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



