#!/usr/bin/env python

import argparse
import imp
import os
import logging

logger = logging.getLogger("sparkperf")
logger.setLevel(logging.DEBUG)
#logger.addHandler(logging.StreamHandler())

from sparkperf.commands import *
from sparkperf.cluster import Cluster
from sparkperf.testsuites import *
from sparkperf.build import SparkBuildManager


parser = argparse.ArgumentParser(description='Run Spark performance tests. Before running, '
    'edit the supplied configuration file.')

parser.add_argument('--config-file', help='override default location of config file, must be a '
    'python file that ends in .py', default="%s/config/config.py" % PROJ_DIR)

parser.add_argument('--additional-make-distribution-args',
    help='additional arugments to pass to make-distribution.sh when building Spark', default="")

args = parser.parse_args()
assert args.config_file.endswith(".py"), "config filename must end with .py"

# Check if the config file exists.
assert os.path.isfile(args.config_file), ("Please create a config file called %s (you probably "
    "just want to copy and then modify %s/config/config.py.template)" %
    (args.config_file, PROJ_DIR))

print "Detected project directory: %s" % PROJ_DIR
# Import the configuration settings from the config file.
print "Loading configuration from %s" % args.config_file
with open(args.config_file) as cf:
    config = imp.load_source("config", "", cf)

# Spark will always be built, assuming that any possible test run
# of this program is going to depend on Spark.
run_spark_tests = config.RUN_SPARK_TESTS and (len(config.SPARK_TESTS) > 0)
run_pyspark_tests = config.RUN_PYSPARK_TESTS and (len(config.PYSPARK_TESTS) > 0)
run_streaming_tests = config.RUN_STREAMING_TESTS and (len(config.STREAMING_TESTS) > 0)
run_mllib_tests = config.RUN_MLLIB_TESTS and (len(config.MLLIB_TESTS) > 0)
run_python_mllib_tests = config.RUN_PYTHON_MLLIB_TESTS and (len(config.PYTHON_MLLIB_TESTS) > 0)
run_tests = run_spark_tests or run_pyspark_tests or run_streaming_tests or run_mllib_tests \
    or run_python_mllib_tests

should_prep_mllib_tests = (run_mllib_tests or run_python_mllib_tests) and config.PREP_MLLIB_TESTS

print("Building perf tests...")

if should_prep_mllib_tests:
    MLlibTests.build(config.MLLIB_SPARK_VERSION)
elif run_mllib_tests:
    assert MLlibTests.is_built(), ("You tried to skip packaging the MLlib perf " +
        "tests, but %s was not already present") % MLlibTests.test_jar_path

if run_mllib_tests:
    MLlibTests.run_tests(cluster, config, config.MLLIB_TESTS, "MLlib-Tests",
                         config.MLLIB_OUTPUT_FILENAME)

if run_pyspark_tests:
    PythonTests.run_tests(config, config.PYSPARK_TESTS, "PySpark-Tests",
                          config.PYSPARK_OUTPUT_FILENAME)       

if run_python_mllib_tests:
    PythonMLlibTests.run_tests(config, config.PYTHON_MLLIB_TESTS, "Python-MLlib-Tests",
                               config.PYTHON_MLLIB_OUTPUT_FILENAME)

print("Finished running all tests.")
