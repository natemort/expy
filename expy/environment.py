
from pathlib import Path
import re
from .procedure import *
from .config import Config




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
        self.config["command_args"] = []

    def command(self, command: str, **kwargs) -> ProcedureGenerator:
        def setup(config: Config) -> Procedure:
            config = config.new_child("command", command, kwargs)

            def run(x: int) -> float:
                instance = config.new_child()
                instance["x"] = x
                environment = config["command_env"]
                trials = config["command_trials"]
                pattern = config["command_pattern"]
                args = config["command_args"]
                full_command = args.copy()
                full_command.insert(0, command)
                times = []
                for trial in range(trials):
                    search = re.search(pattern, exec_command(full_command, environment, config["directory"]))
                    if not search:
                        raise RuntimeError("Unable to parse output")
                    times.append(float(search.group(1)))
                print(x, " -> ", command, " : ", mean(times))
                return mean(times)

            return CompositeProcedure(run, lambda: False)

        return setup

    def experiment(self, name: str, **kwargs) -> Experiment:
        generators = OrderedDict((name, generator for name, generator in kwargs.items()))
        return Experiment(name, self.config, generators)




