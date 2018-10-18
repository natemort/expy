
import re
import subprocess
from collections import OrderedDict
from typing import Dict, List
from .config import Config
from .experiment import Experiment
from .procedure import CompositeProcedure, Procedure, ProcedureGenerator


class Environment:
    config = Config()

    def __init__(self, directory: str):
        self._add_defaults()
        self.config["directory"] = directory

    def _add_defaults(self):
        self.config["experiment_out"] = lambda config: config["directory"] + "/results"
        self.config["command_trials"] = 5
        self.config["command_pattern"] = ".*([0-9.]+).*"
        self.config["command_env"] = {}
        self.config["presentation_title"] = lambda config: config["presentation"]
        self.config["presentation_out"] = lambda config: config["experiment_out"] + "/" + config["presentation"]
        self.config["graph_title"] = lambda config: config["graph"]
        self.config["graph_y_label"] = "Execution Time"
        self.config["graph_x_label"] = "Threads"

    def command(self, command: str, **kwargs) -> ProcedureGenerator:
        def setup(config: Config) -> Procedure:
            config = config.new_child("command", command, kwargs)

            def run(x: int) -> float:
                instance = config.new_child("x", str(x))
                environment = instance["command_env"]
                trials = instance["command_trials"]
                pattern = instance["command_pattern"]
                args = instance["command_args"]
                full_command = args.copy()
                full_command.insert(0, command)
                times = []
                for trial in range(trials):
                    output = _exec_command(full_command, environment, instance["directory"])
                    search = re.search(pattern, output)
                    if not search:
                        raise RuntimeError("Unable to parse output: " + output)
                    try:
                        times.append(float(search.group(1)))
                    except ValueError:
                        raise RuntimeError("Failed to parse output:\n```\n" + output+"\n```\nwith '"
                                           + pattern + "'\nCaptured: '" + search.group(1) + "'")
                print("Running", command, "-", x, "->", full_command, ":", _mean(times))
                return _mean(times)

            return CompositeProcedure(run, lambda: False)

        return setup

    def experiment(self, name: str, **kwargs) -> Experiment:
        generators = OrderedDict((name, generator) for name, generator in kwargs.items())
        return Experiment(name, self.config, generators)


def _mean(numbers: List[float]) -> float:
    return float(sum(numbers)) / max(len(numbers), 1)


def _exec_command(command: List[str], env: Dict[str, str], working_dir: str) -> str:
    sub = subprocess.run(args=command, env=env, stdout=subprocess.PIPE, cwd=working_dir)
    return sub.stdout.decode("utf-8")



