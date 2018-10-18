import matplotlib

# Necessary to use pyplot in a headless environment
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from typing import Callable, Dict, List, Tuple
from collections import OrderedDict
from .config import Config

# rows, cols, index
GraphPosition = Tuple[int, int, int]
# A Graph takes a position, the x values, and the y values, and renders it via matplotlib
# There's probably a nice object oriented way to interface with matplotlib but god damn
# is it complicated
# pos: GraphPosition, x: List[int], Dict[str, List[float]]
Graph = Callable[[GraphPosition, List[int], Dict[str, List[float]]], None]
GraphGenerator = Callable[[Config], Graph]


###
# Used by all the graphs to actually render the data.
# Currently makes generating a semi-log or log plot pretty difficult
###
def _graph_and_table(pos: GraphPosition, x_data: List[int], data: Dict[str, List[float]],
                     config: Config):
    y_label = config["graph_y_label"]
    x_label = config["graph_x_label"]
    title = config["graph_title"]
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
    table = plt.subplot(pos[0], pos[1], pos[2] + 1, frame_on=False)
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


def graph(title: str, transformation: Callable[[List[int], List[float]], List[float]], **kwargs) -> GraphGenerator:
    def generate(config: Config) -> Graph:
        graph_config = config.new_child("graph", title, kwargs)

        def apply(pos: GraphPosition, x_data: List[int], y_data: Dict[str, List[float]]):
            data = OrderedDict((key, transformation(x_data, data)) for key, data in y_data.items())
            _graph_and_table(pos, x_data, data, graph_config)

        return apply

    return generate


def speedup(**kwargs) -> GraphGenerator:
    return graph("Speedup", _speedup, **kwargs)


def _speedup(x_data: List[int], y_data: List[float]) -> List[float]:
    return [y_data[0] / y for y in y_data]


def time(**kwargs) -> GraphGenerator:
    return graph("Execution Time", lambda x, y: y, **kwargs)


def efficiency(**kwargs) -> GraphGenerator:
    return graph("Efficiency", _efficiency, **kwargs)


def _efficiency(x_data: List[int], y_data: List[float]) -> List[float]:
    return [y_data[0] / y_data[index] / x for index, x in enumerate(x_data)]
