 # See example_detailed.py for a line by line breakdown
 
from expy.expy.environment import Environment
from expy.expy.graphs import *

env = Environment("pa3")

omp_env = lambda config: {"OMP_NUM_THREADS": config["x"]}

test_file = "k100x20M.txt"

env.config["command_trials"] = 1
env.config["command_pattern"] = "Time taken : ([0-9.]+)\."

knap2_threads = env.command("knap2", args=[test_file, "101"], env=omp_env)
knap2_depth = env.command("knap2", args=lambda c: [test_file, c["x"]])
knap3 = env.command("knap3", args=[test_file], env=omp_env)

env.experiment("knap2_threads", knap2=knap2_threads).run(range(1,9)).presentation("knap2_threads", time(), speedup(), efficiency(), title="Knap2 Threads", )
env.experiment("knap2_depth", knap2=knap2_depth).run(range(0, 8)).presentation("knap2_depth", time(x_label="Parallel Depth"), title="Knap2 Depth")
env.experiment("knap3", knap3=knap3).run(range(1,9)).presentation("knap3", time(), speedup(), efficiency(), title="Knap3")


