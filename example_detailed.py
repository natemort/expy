# This example is how I generated data and graphs for PA3
# Rather than actually install expy as a python package, I just cloned it into the directory expy.
# This assumes the following directory structure:
# expy
#  |->expy
#  |  |->__init__.py, etc.
#  |->requirements.txt
# pa3.py
# pa3
#  |-> knap1
#  |-> knap2
#  |-> knap3
#  |-> k100x20M.txt

# First "expy" is the name of the directory I cloned it into, the second one is the name of the package
from expy.expy.environment import Environment
from expy.expy.graphs import *

# The directory to run everything in.  This is where I put my makefile, my source, and my binaries
env = Environment("pa3")


# We're just defining a variable we'll be using later.  This is the file I ran all my experiments on.
test_file = "k100x20M.txt"

# Expy is built around a hierarchical config.
# Environment <- Experiment <- Command <- Instance
# If a value isn't found at one level, it looks to the next one
# this means that you can set common properties at the environment level,
# but later override them for any specific command or experiment
#
# Here we're setting values for how many times to run each command,
# and the regular expression to use to extract timing data from the output of each command.
env.config["command_trials"] = 1
env.config["command_pattern"] = "Time taken : ([0-9.]+)\."

# Every variable in the config can either be a value, or a function that takes the config and returns a value
# This allows for configuration values to be dependent on each other.
# x is a special config value for the x value of the currently running instance
omp_env = lambda config: {"OMP_NUM_THREADS": config["x"]}

# Run knap2 with the specified arguments.  Everything specified as a keyword argument(such as env=omp_env) is added to the config
# with the prefix "command_"
# We're using omp_env variable we established before, so we're using the value of x for the number of threads
knap2_threads = env.command("knap2", args=[test_file, "101"], env=omp_env)
# Run knap2, but this time the arguments are generated dynamically based on the value of x that we pass in.
# The second argument to knap2 is the depth, so this command is using the values of x for depth rather than the number of threads
knap2_depth = env.command("knap2", args=lambda c: [test_file, c["x"]])
# Run knap3, and the only arguments to it are the test file.  We're using omp_env, so x is going to be used for the number of threads
knap3 = env.command("knap3", args=[test_file], env=omp_env)


# These lines are what I used when running it, but I'm going to break them down so I can explain them one part at a time.
#env.experiment("knap2_threads", knap2=knap2_threads).run(range(1,9)).presentation("knap2_threads", time(), speedup(), efficiency(), title="Knap2 Threads")
#env.experiment("knap2_depth", knap2=knap2_depth).run(range(0, 8)).presentation("knap2_depth", time(x_label="Parallel Depth"), title="Knap2 Depth")
#env.experiment("knap3", knap3=knap3).run(range(1,9)).presentation("knap3", time(), speedup(), efficiency(), title="Knap3")

# Create an experiment.  Here we have a single procedure, knap2_threads which we alias as knap2.
# You can't specify config values here since the keyword arguments are used for procedurs
experiment = env.experiment("knap2_threads", knap2=knap2_threads)
# Run the experiment with [1,2,3,4,5,6,7,8] as the values of x.  knap2_threads uses the value of
# x to set the number of threads to run, so we'll run it 5 times with each value of x
results = experiment.run(range(1,9), command_trials=5)

# Create an image called knap2_threads with graphs of the execution time, speedup, and efficiency
# time, speedup, and efficiency are all imported from expy.expy.graphs
# Presentations also have a hierarchy of config values:
# Environment <- Experiment <- Presentation <- Graph
results.presentation("knap2_threads", time(), speedup(), efficiency(), title="Knap2 Threads")

# As such, config values can be passed to the presentation and graphs.
# Here we set the x axis to have the label "Parallel Depth" rather than the default label "Threads" since we
# use the x values for depth rather than threads
env.experiment("knap2_depth", knap2=knap2_depth).run(range(0, 8)).presentation("knap2_depth", time(x_label="Parallel Depth"), title="Knap2 Depth")

# And finally, all in one line, run and generate knap3's graphs:
env.experiment("knap3", knap3=knap3).run(range(1,9)).presentation("knap3", time(), speedup(), efficiency(), title="Knap3")



