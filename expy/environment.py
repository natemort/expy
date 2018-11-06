
import re
import subprocess
from collections import OrderedDict
from typing import Any, Dict, List
from .config import Config
from .experiment import Experiment
from .procedure import CompositeProcedure, Procedure, ProcedureGenerator

OSP_ENV = lambda config: {"OMP_NUM_THREADS": config["x"]}


class Environment:
    config = Config("env")

    def __init__(self, directory: str):
        self._add_defaults()
        self.config["env_directory"] = directory

    def _add_defaults(self):

        self.config["exp_out"] = lambda config: config["env_directory"] + "/results"
        self.config["cmd_trials"] = 5
        self.config["cmd_pattern"] = ".*([0-9.]+).*"
        self.config["cmd_shell"] = False
        self.config["cmd_full"] = lambda config: config["cmd"] + config["cmd_args"]
        self.config["cmd_env"] = {}
        self.config["pres_title"] = lambda config: config["pres"]
        self.config["pres_out"] = lambda config: config["exp_out"] + "/" + config["pres"]
        self.config["view_title"] = lambda config: config["view"]
        self.config["view_y_label"] = "Execution Time"
        self.config["view_x_label"] = "Threads"

    def command(self, command: str, **kwargs) -> ProcedureGenerator:
        config = self.config.new_child("cmd", command, kwargs)

        def setup(instance: Config) -> Procedure:
            def run(x: int) -> float:
                instance["x"] = str(x)
                environment = instance["cmd_env"]
                trials = instance["cmd_trials"]
                pattern = instance["cmd_pattern"]
                full_command = instance["cmd_full"]
                times = []
                for trial in range(trials):
                    output = _exec_command(full_command, environment, instance["env_directory"], instance["cmd_shell"])
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

        return ProcedureGenerator(config, setup)

    def experiment(self, name: str, **kwargs) -> Experiment:
        generators = OrderedDict((name, generator) for name, generator in kwargs.items())
        return Experiment(name, self.config, generators)


def _mean(numbers: List[float]) -> float:
    return float(sum(numbers)) / max(len(numbers), 1)


def _exec_command(command: List[str], env: Dict[str, str], working_dir: str, shell: bool) -> str:
    sub = subprocess.run(args=command, env=env, stdout=subprocess.PIPE, cwd=working_dir, shell=shell)
    return sub.stdout.decode("utf-8")



