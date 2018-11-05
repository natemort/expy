import matplotlib
# Necessary to use pyplot in a headless environment
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from collections import OrderedDict
from os import makedirs
from pathlib import Path
from typing import Dict, List, Iterable, Tuple
import pickle
from .config import Config
from .procedure import ProcedureGenerator


class ExperimentResult:

    def __init__(self, config: Config, x_data: List[int], data: Dict[str, List[float]]):
        self.config = config
        self.data = data
        self.x_data = x_data

    def __getitem__(self, proc: str) -> Dict[int, float]:
        return OrderedDict((x, self.data[proc][index]) for index, x in enumerate(self.x_data))

    def __getstate__(self) -> Tuple[List[int], Dict[str, List[float]]]:
        return (self.x_data, self.data)
    
    def __setstate__(self, state):
        self.x_data, self.data = state
        
    def presentation(self, name: str, *args, **kwargs):
        pres_config = self.config.new_child("pres", name, kwargs)
        rows = len(args)
        cols = 2
        title = pres_config["pres_title"]
        plt.figure(1)
        plt.suptitle(title, fontsize=12)
        for index, view in enumerate(args):
            # Generate each graph, then call it
            view(pres_config)((rows, cols, index * 2 + 1), self.x_data, self.data)
        plt.tight_layout()
        plt.subplots_adjust(top=0.88)
        plt.savefig(pres_config["pres_out"], dpi=1000)
        plt.clf()

    @staticmethod
    def load(path: Path) -> 'ExperimentResult':
        with path.open('rb') as f:
            return pickle.load(f)

    def save(self, path: Path):
        with path.open('wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)


class Experiment:

    def __init__(self, name: str, config: Config, procedures: Dict[str, ProcedureGenerator]):
        self.name = name
        self.env_config = config
        self.procedures = procedures

    def run(self, x_range: Iterable[int], **kwargs) -> ExperimentResult:
        exp_config = self.env_config.new_child("exp", self.name, kwargs)
        makedirs(exp_config["env_directory"], exist_ok=True)
        makedirs(exp_config["exp_out"], exist_ok=True)
        result_path = Path(exp_config["exp_out"] + "/" + self.name + ".exp")

        if result_path.is_file():
            print("Loaded results for experiment: ", self.name)
            result = ExperimentResult.load(result_path)
            result.config = exp_config
        else:
            result = self._run(x_range, exp_config)
            result.save(result_path)

        return result

    def _run(self, x_range: Iterable[int], exp_config: Config) -> ExperimentResult:
        x_data = list(x_range)
        built = OrderedDict((name, procedure.generate(exp_config)) for name, procedure in self.procedures.items())
        data = OrderedDict((name, [procedure.run(x) for x in x_range]) for name, procedure in built.items())
        return ExperimentResult(exp_config, x_data, data)
