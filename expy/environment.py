
from pathlib import Path
import re
from .procedure import *
from .config import Config


ProcedureGenerator = Callable[[Config], Procedure]


class Environment:
    config = Config()
    _runners = {}

    def __init__(self, directory: str):
        self.directory = directory
        self._add_defaults()

    def _add_defaults(self):
        self.config["experiment_out"] = self.directory + "/results"
        self.config["command_trials"] = 5
        self.config["command_pattern"] = ".*([0-9.]+).*"
        self.config["command_env"] = {}
        self.config["command_args"] = []

    def command(self, command: str, **kwargs):
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
                    search = re.search(pattern, exec_command(full_command, environment))
                    if not search:
                        raise RuntimeError("Unable to parse output")
                    times.append(float(search.group(1)))
                print(x, " -> ", command, " : ", mean(times))
                return mean(times)

            return CompositeProcedure(run, lambda: False)

        self._runners[command] = setup

    def run_experiment(self, name: str, range: Iterable[int], *args, **kwargs) -> ExperimentResult:
        exp_config = self.config.new_child("experiment", name, kwargs)
        result_path = Path(exp_config["experiment_out"] + "/" + name + ".exp")

        if result_path.is_file():
            results = ExperimentResult.load(result_path)
        else:
            procedures = OrderedDict((self._runners[command](exp_config) for command in args))
            results = run_experiment(range, procedures)
            results.save(result_path)

        return results




