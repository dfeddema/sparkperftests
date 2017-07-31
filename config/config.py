"""
Configuration options for running Spark performance tests.
"""

import time
import os
import os.path
import socket

from sparkperf.config_utils import FlagSet, JavaOptionSet, OptionSet, ConstantOption


# ================================ #
#  Standard Configuration Options  #
# ================================ #


SPARK_VERSION="2.1.0"
OPENSHIFT_VERSION="v3.4.1.7"
SPARK_CLUSTER_URL="spark://spark-master-1yih:7077"  
SPARK_JOB_TEMPLATE="diane-oshinko-pyspark-job"  

DOCKER_IMAGE="172.30.100.159:5000/perf-testing-d/mllibpy"
SPARK_OPTIONS="--executor-memory 32g --conf spark.default.parallelism=128 --conf spark.workers.memory=64g --conf spark.python.worker.memory=64g --conf spark.local.dir=/tmp"
OSHINKO_SPARK_DRIVER_CONFIG="oshinko-spark-driver-config"
OSHINKO_DEL_CLUSTER="true"
OSHINKO_CLUSTER_NM="dianememtst32"
COMPLETIONS="1"

PBENCH_HOME="/opt/pbench-agent/bench-scripts/" 
SPARKPERF_RUNDIR="/root/diane/spark-on-openshift-benchmarks-newtests/" 

#USE_CLUSTER_SPARK = True

# Which tests to run
RUN_SPARK_TESTS = False
#RUN_PYSPARK_TESTS = True
RUN_PYSPARK_TESTS = False
RUN_STREAMING_TESTS = False
RUN_MLLIB_TESTS = False
RUN_PYTHON_MLLIB_TESTS = True
#RUN_PYTHON_MLLIB_TESTS = False

# Which tests to prepare. Set this to true for the first
# installation or whenever you make a change to the tests.
PREP_SPARK_TESTS = False
PREP_PYSPARK_TESTS = True
PREP_STREAMING_TESTS = False
PREP_MLLIB_TESTS = False

# Whether to warm up local disks (warm-up is only necesary on EC2).
DISK_WARMUP = False

# Total number of bytes used to warm up each local directory.
DISK_WARMUP_BYTES = 200 * 1024 * 1024

# Number of files to create when warming up each local directory.
# Bytes will be evenly divided across files.
DISK_WARMUP_FILES = 200

# Prompt for confirmation when deleting temporary files.
PROMPT_FOR_DELETES = True

# Files to write results to
#SPARK_OUTPUT_FILENAME = "results/spark_perf_output" 
SPARK_OUTPUT_FILENAME = "results/spark_perf_output_%s" % (
     time.strftime("%Y-%m-%d_%H-%M-%S"))
PYSPARK_OUTPUT_FILENAME = "results/python_perf_output_%s" % (
     time.strftime("%Y-%m-%d_%H-%M-%S"))
STREAMING_OUTPUT_FILENAME = "results/streaming_perf_output" 
MLLIB_OUTPUT_FILENAME = "results/mllib_perf_output"
PYTHON_MLLIB_OUTPUT_FILENAME = "results/python_mllib_perf_output_%s_%s_%s" % (
     SPARK_VERSION, OPENSHIFT_VERSION, time.strftime("%Y-%m-%d_%H-%M-%S"))
PYTHON_MLLIB_OUTPUT_FILENAME = "results/python_mllib_perf_output_%s_%s_%s" % (
    SPARK_VERSION, OPENSHIFT_VERSION, time.strftime("%Y-%m-%d_%H-%M-%S"))


# ============================ #
#  Test Configuration Options  #
# ============================ #

# The default values configured below are appropriate for approximately 20 m1.xlarge nodes,
# in which each node has 15 GB of memory. Use this variable to scale the values (e.g.
# number of records in a generated dataset) if you are running the tests with more
# or fewer nodes. When developing new test suites, you might want to set this to a small
# value suitable for a single machine, such as 0.001.
SCALE_FACTOR = 0.05

assert SCALE_FACTOR > 0, "SCALE_FACTOR must be > 0."

# If set, removes the first N trials for each test from all reported statistics. Useful for
# tests which have outlier behavior due to JIT and other system cache warm-ups. If any test
# returns fewer N + 1 results, an exception is thrown.
IGNORED_TRIALS = 2

# Command used to launch Scala or Java.

# Set up OptionSets. Note that giant cross product is done over all JavaOptionsSets + OptionSets
# passed to each test which may be combinations of those set up here.


# The following options value sets are shared among all tests.
#COMMON_JAVA_OPTS = []

COMMON_JAVA_OPTS = [
    # Fraction of JVM memory used for caching RDDs.
    #JavaOptionSet("spark.storage.memoryFraction", [0.66]),
    JavaOptionSet("spark.memory.offHeap.enabled", [True]),
    JavaOptionSet("spark.memory.offHeap.size", ["20g"]),
    JavaOptionSet("spark.executor.memory", ["64g"]),
    # JavaOptionSet("spark.executor.memory", ["2g"]),
    # Turn event logging on in order better diagnose failed tests. Off by default as it crashes
    # releases prior to 1.0.2
    # JavaOptionSet("spark.eventLog.enabled", [True]),
    # To ensure consistency across runs, we disable delay scheduling
    JavaOptionSet("spark.locality.wait", [str(60 * 1000 * 1000)])
]


COMMON_OPTS = [
    # How many times to run each experiment - used to warm up system caches.
    OptionSet("num-trials", [10]) 
]

# The following options value sets are shared among all tests of
# operations on key-value data.
SPARK_KEY_VAL_TEST_OPTS = [
    # The number of input partitions.
    OptionSet("num-partitions", [400], can_scale=True),
    # The number of reduce tasks.
    OptionSet("reduce-tasks", [400], can_scale=True),
    # A random seed to make tests reproducable.
    OptionSet("random-seed", [5]),
    # Input persistence strategy (can be "memory", "disk", or "hdfs").
    # NOTE: If "hdfs" is selected, datasets will be re-used across runs of
    #       this script. This means parameters here are effectively ignored if
    #       an existing input dataset is present.
    OptionSet("persistent-type", ["memory"]),
    # Whether to wait for input in order to exit the JVM.
    FlagSet("wait-for-exit", [False]),
    # Total number of records to create.
    OptionSet("num-records", [200 * 1000 * 1000], True),
    # Number of unique keys to sample from.
    OptionSet("unique-keys",[20 * 1000], True),
    # Length in characters of each key.
    OptionSet("key-length", [10]),
    # Number of unique values to sample from.
    OptionSet("unique-values", [1000 * 1000], True),
    # Length in characters of each value.
    OptionSet("value-length", [10]),
    # Use hashes instead of padded numbers for keys and values
    FlagSet("hash-records", [False]),
    # Storage location if HDFS persistence is used
#   OptionSet("storage-location", [
#       HDFS_URL + "/spark-perf-kv-data"])
]


# ======================= #
#  Spark Core Test Setup  #
# ======================= #

# Set up the actual tests. Each test is represtented by a tuple:
# (short_name, test_cmd, scale_factor, list<JavaOptionSet>, list<OptionSet>)

SPARK_KV_OPTS = COMMON_OPTS + SPARK_KEY_VAL_TEST_OPTS
SPARK_TESTS = []


# ==================== #
#  Pyspark Test Setup  #
# ==================== #

PYSPARK_TESTS = []

BROADCAST_TEST_OPTS = [
    # The size of broadcast
    OptionSet("broadcast-size", [200 << 20], can_scale=True),
]

#PYSPARK_TESTS += [("python-scheduling-throughput", "core_tests.py",
#    SCALE_FACTOR, COMMON_JAVA_OPTS,
#    [ConstantOption("SchedulerThroughputTest"), OptionSet("num-tasks", [5000])] + COMMON_OPTS)]
#   [ConstantOption("SchedulerThroughputTest"), OptionSet("num-tasks", [100000])] + COMMON_OPTS)]

PYSPARK_TESTS += [("python-agg-by-key", "core_tests.py", SCALE_FACTOR * 20,
     COMMON_JAVA_OPTS, [ConstantOption("AggregateByKey")] + SPARK_KV_OPTS)]

# Scale the input for this test by 2x since ints are smaller.
PYSPARK_TESTS += [("python-agg-by-key-int", "core_tests.py", SCALE_FACTOR * 20,
    COMMON_JAVA_OPTS, [ConstantOption("AggregateByKeyInt")] + SPARK_KV_OPTS)]

PYSPARK_TESTS += [("python-agg-by-key-naive", "core_tests.py", SCALE_FACTOR * 6,
    COMMON_JAVA_OPTS, [ConstantOption("AggregateByKeyNaive")] + SPARK_KV_OPTS)]

# Scale the input for this test by 0.10.
#PYSPARK_TESTS += [("python-sort-by-key", "core_tests.py", SCALE_FACTOR * 0.1,
PYSPARK_TESTS += [("python-sort-by-key", "core_tests.py", SCALE_FACTOR * 0.5,
    COMMON_JAVA_OPTS, [ConstantOption("SortByKey")] + SPARK_KV_OPTS)]

#PYSPARK_TESTS += [("python-sort-by-key-int", "core_tests.py", SCALE_FACTOR * 0.2,
PYSPARK_TESTS += [("python-sort-by-key-int", "core_tests.py", SCALE_FACTOR * 0.5,
    COMMON_JAVA_OPTS, [ConstantOption("SortByKeyInt")] + SPARK_KV_OPTS)]

# Diane changed to *8
#PYSPARK_TESTS += [("python-count", "core_tests.py", SCALE_FACTOR,
PYSPARK_TESTS += [("python-count", "core_tests.py", SCALE_FACTOR * 8,
                 COMMON_JAVA_OPTS, [ConstantOption("Count")] + SPARK_KV_OPTS)]

#PYSPARK_TESTS += [("python-count-w-fltr", "core_tests.py", SCALE_FACTOR,
PYSPARK_TESTS += [("python-count-w-fltr", "core_tests.py", SCALE_FACTOR * 10,
    COMMON_JAVA_OPTS, [ConstantOption("CountWithFilter")] + SPARK_KV_OPTS)]

#PYSPARK_TESTS += [("python-broadcast-w-bytes", "core_tests.py", SCALE_FACTOR,
PYSPARK_TESTS += [("python-broadcast-w-bytes", "core_tests.py", SCALE_FACTOR * 10,
    COMMON_JAVA_OPTS, [ConstantOption("BroadcastWithBytes")] + SPARK_KV_OPTS + BROADCAST_TEST_OPTS)]

#PYSPARK_TESTS += [("python-broadcast-w-set", "core_tests.py", SCALE_FACTOR,
PYSPARK_TESTS += [("python-broadcast-w-set", "core_tests.py", SCALE_FACTOR * 10,
    COMMON_JAVA_OPTS, [ConstantOption("BroadcastWithSet")] + SPARK_KV_OPTS + BROADCAST_TEST_OPTS)]


# ============================ #
#  Spark Streaming Test Setup  #
# ============================ #

STREAMING_TESTS = []

# The following function generates options for setting batch duration in streaming tests
def streaming_batch_duration_opts(duration):
    return [OptionSet("batch-duration", [duration])]

# The following function generates options for setting window duration in streaming tests
def streaming_window_duration_opts(duration):
    return [OptionSet("window-duration", [duration])]

STREAMING_COMMON_OPTS = [
    OptionSet("total-duration", [60]) 
]
#   OptionSet("hdfs-url", [HDFS_URL]),

STREAMING_COMMON_JAVA_OPTS = [
    # Fraction of JVM memory used for caching RDDs.
    JavaOptionSet("spark.storage.memoryFraction", [0.66]),
    JavaOptionSet("spark.serializer", ["org.apache.spark.serializer.JavaSerializer"]),
    # JavaOptionSet("spark.executor.memory", ["9g"]),
    JavaOptionSet("spark.executor.extraJavaOptions", [" -XX:+UseConcMarkSweepGC "])
]

STREAMING_KEY_VAL_TEST_OPTS = STREAMING_COMMON_OPTS + streaming_batch_duration_opts(2000) + [
    # Number of input streams.
    OptionSet("num-streams", [1], can_scale=True),
    # Number of records per second per input stream
    OptionSet("records-per-sec", [10 * 1000]),
    # Number of reduce tasks.
    OptionSet("reduce-tasks", [10], can_scale=True),
    # memory serialization ("true" or "false").
    OptionSet("memory-serialization", ["true"]),
    # Number of unique keys to sample from.
    OptionSet("unique-keys",[100 * 1000], can_scale=True),
    # Length in characters of each key.
    OptionSet("unique-values", [1000 * 1000], can_scale=True),
    # Send data through receiver
    OptionSet("use-receiver", ["true"]),
]


# This test is just to see if everything is setup properly
STREAMING_TESTS += [("basic", "streaming.perf.TestRunner", SCALE_FACTOR,
    STREAMING_COMMON_JAVA_OPTS, [ConstantOption("basic")] + STREAMING_COMMON_OPTS + streaming_batch_duration_opts(1000))]

STREAMING_TESTS += [("state-by-key", "streaming.perf.TestRunner", SCALE_FACTOR,
    STREAMING_COMMON_JAVA_OPTS, [ConstantOption("state-by-key")] + STREAMING_KEY_VAL_TEST_OPTS)]

STREAMING_TESTS += [("group-by-key-and-window", "streaming.perf.TestRunner", SCALE_FACTOR,
    STREAMING_COMMON_JAVA_OPTS, [ConstantOption("group-by-key-and-window")] + STREAMING_KEY_VAL_TEST_OPTS + streaming_window_duration_opts(10000) )]

STREAMING_TESTS += [("reduce-by-key-and-window", "streaming.perf.TestRunner", SCALE_FACTOR,
    STREAMING_COMMON_JAVA_OPTS, [ConstantOption("reduce-by-key-and-window")] + STREAMING_KEY_VAL_TEST_OPTS + streaming_window_duration_opts(10000) )]

STREAMING_TESTS += [("hdfs-recovery", "streaming.perf.TestRunner", SCALE_FACTOR,
    STREAMING_COMMON_JAVA_OPTS)]
#   STREAMING_COMMON_JAVA_OPTS, [ConstantOption("hdfs-recovery")] + _HDFS_RECOVERY_TEST_OPTS)]


# ================== #
#  MLlib Test Setup  #
# ================== #

MLLIB_TESTS = []
MLLIB_PERF_TEST_RUNNER = "mllib.perf.TestRunner"

# Set this to 1.0, 1.1, 1.2, ... (the major version) to test MLlib with a particular Spark version.
# Note: You should also build mllib-perf using -Dspark.version to specify the same version.
# Note: To run perf tests against a snapshot version of Spark which has not yet been packaged into a release:
#  * Build Spark locally by running `build/sbt assembly; build/sbt publishLocal` in the Spark root directory
#  * Set `USE_CLUSTER_SPARK = True` and `MLLIB_SPARK_VERSION = {desired Spark version, e.g. 1.5}`
#  * Don't use PREP_MLLIB_TESTS = True; instead manually run `cd mllib-tests; sbt/sbt -Dspark.version=1.5.0-SNAPSHOT clean assembly` to build perf tests

MLLIB_SPARK_VERSION = 2.0

MLLIB_JAVA_OPTS = COMMON_JAVA_OPTS
if MLLIB_SPARK_VERSION >= 1.1:
    MLLIB_JAVA_OPTS = MLLIB_JAVA_OPTS + [
        # Shuffle manager: SORT, HASH
        JavaOptionSet("spark.shuffle.manager", ["SORT"])
    ]

# The following options value sets are shared among all tests of
# operations on MLlib algorithms.
MLLIB_COMMON_OPTS = COMMON_OPTS + [
    # The number of input partitions.
    # The default setting is suitable for a 16-node m3.2xlarge EC2 cluster.
    OptionSet("num-partitions", [128]),
    # Diane changed this OptionSet("num-partitions", [256], can_scale=True),
    # Diane this setting above changedOptionSet("num-partitions", [128], can_scale=True),
    # A random seed to make tests reproducable.
    OptionSet("random-seed", [5])
]

# Algorithms available in Spark-1.0 #

# Regression and Classification Tests #
MLLIB_REGRESSION_CLASSIFICATION_TEST_OPTS = MLLIB_COMMON_OPTS + [
    # The number of rows or examples
    OptionSet("num-examples", [1000000], can_scale=True)
]

# Generalized Linear Model (GLM) Tests #
MLLIB_GLM_TEST_OPTS = MLLIB_REGRESSION_CLASSIFICATION_TEST_OPTS + [
    # The scale factor for the noise in feature values.
    # Currently ignored for regression.
    OptionSet("feature-noise", [1.0]),
    # The number of features per example
    OptionSet("num-features", [10000], can_scale=False),
    # The number of iterations for SGD
    OptionSet("num-iterations", [20]),
    # The step size for SGD
    OptionSet("step-size", [0.001]),
    # Regularization type: none, l1, l2
    OptionSet("reg-type", ["l2"]),
    # Regularization parameter
    OptionSet("reg-param", [0.1])
]
if MLLIB_SPARK_VERSION >= 1.5:
    MLLIB_GLM_TEST_OPTS += [
        # Ignored, but required for config
        OptionSet("elastic-net-param", [0.0])
    ]

# GLM Regression Tests #
MLLIB_GLM_REGRESSION_TEST_OPTS = MLLIB_GLM_TEST_OPTS + [
    # Optimization algorithm: sgd
    OptionSet("optimizer", ["sgd"]),
    # The intercept for the data
    OptionSet("intercept", [0.0]),
    # The scale factor for label noise
    OptionSet("label-noise", [0.1]),
    # Loss to minimize: l2 (squared error)
    OptionSet("loss", ["l2"])
]

MLLIB_TESTS += [("glm-regression", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("glm-regression")] + MLLIB_GLM_REGRESSION_TEST_OPTS)]

# Classification Tests #
MLLIB_CLASSIFICATION_TEST_OPTS = MLLIB_GLM_TEST_OPTS + [
    # Expected fraction of examples which are negative
    OptionSet("per-negative", [0.3]),
    # Optimization algorithm: sgd, l-bfgs
    #OptionSet("optimizer", ["sgd", "l-bfgs"])
    OptionSet("optimizer", ["sgd"])
]

# GLM Classification Tests #
MLLIB_GLM_CLASSIFICATION_TEST_OPTS = MLLIB_CLASSIFICATION_TEST_OPTS + [
    # Loss to minimize: logistic, hinge (SVM)
    OptionSet("loss", ["logistic"])
]

MLLIB_TESTS += [("glm-classification", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
                 MLLIB_JAVA_OPTS, [ConstantOption("glm-classification")] +
                 MLLIB_GLM_CLASSIFICATION_TEST_OPTS)]

if MLLIB_SPARK_VERSION >= 1.5:
    MLLIB_GLM_ELASTIC_NET_TEST_OPTS = MLLIB_REGRESSION_CLASSIFICATION_TEST_OPTS + [
        # The max number of iterations for LBFGS/OWLQN
        OptionSet("num-iterations", [20]),
        # LBFGS/OWLQN is used with elastic-net regularization.
        OptionSet("optimizer", ["auto"]),
        # Using elastic-net regularization.
        OptionSet("reg-type", ["elastic-net"]),
        # Runs with L2 (param = 0.0), L1 (param = 1.0).
        OptionSet("elastic-net-param", [0.0, 1.0]),
        # Regularization param (lambda)
        OptionSet("reg-param", [0.01]),
        # The scale factor for the noise in feature values
        OptionSet("feature-noise", [1.0]),
        # The step size is not used in LBFGS, but this is required in parameter checking.
        OptionSet("step-size", [0.0])
    ]

    MLLIB_GLM_ELASTIC_NET_REGRESSION_TEST_OPTS = MLLIB_GLM_ELASTIC_NET_TEST_OPTS + [
        # The scale factor for the noise in label values
        OptionSet("label-noise", [0.1]),
        # The intercept for the data
        OptionSet("intercept", [0.2]),
        # Loss to minimize: l2 (squared error)
        OptionSet("loss", ["l2"])
    ]

    # Test L-BFGS
    MLLIB_TESTS += [("glm-regression", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("glm-regression")] +
        MLLIB_GLM_ELASTIC_NET_REGRESSION_TEST_OPTS +
        [OptionSet("num-features", [10000], can_scale=False)])]
    # Test normal equation solver
    MLLIB_TESTS += [("glm-regression", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
                     MLLIB_JAVA_OPTS, [ConstantOption("glm-regression")] +
                     MLLIB_GLM_ELASTIC_NET_REGRESSION_TEST_OPTS +
                     [OptionSet("num-features", [200], can_scale=False)])]

    MLLIB_GLM_ELASTIC_NET_CLASSIFICATION_TEST_OPTS = MLLIB_GLM_ELASTIC_NET_TEST_OPTS + [
        # Expected fraction of examples which are negative
        OptionSet("per-negative", [0.3]),
        # In GLM classification with elastic-net regularization, only logistic loss is supported.
        OptionSet("loss", ["logistic"])
    ]

    # Test L-BFGS
    MLLIB_TESTS += [("glm-classification", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
                     MLLIB_JAVA_OPTS, [ConstantOption("glm-classification")] +
                     MLLIB_GLM_ELASTIC_NET_CLASSIFICATION_TEST_OPTS +
                     [OptionSet("num-features", [10000], can_scale=False)])]
    # Test normal equation solver
#   MLLIB_TESTS += [("glm-classification", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
#                    MLLIB_JAVA_OPTS, [ConstantOption("glm-classification")] +
#                    MLLIB_GLM_ELASTIC_NET_CLASSIFICATION_TEST_OPTS +
#                    [OptionSet("num-features", [200], can_scale=False)])]

NAIVE_BAYES_TEST_OPTS = MLLIB_REGRESSION_CLASSIFICATION_TEST_OPTS + [
    # The number of features per example
    OptionSet("num-features", [10000], can_scale=False),
    # Expected fraction of examples which are negative
    OptionSet("per-negative", [0.3]),
    # The scale factor for the noise in feature values
    OptionSet("feature-noise", [1.0]),
    # Naive Bayes smoothing lambda.
    OptionSet("nb-lambda", [1.0]),
    # Model type: either multinomial or bernoulli (bernoulli only available in Spark 1.4+)
    OptionSet("model-type", ["multinomial"]),
]

MLLIB_TESTS += [("naive-bayes", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("naive-bayes")] +
    NAIVE_BAYES_TEST_OPTS)]

# Decision Trees #
MLLIB_DECISION_TREE_TEST_OPTS = MLLIB_COMMON_OPTS + [
    # The number of rows or examples
    OptionSet("num-examples", [100000], can_scale=True),
    # The number of features per example
    OptionSet("num-features", [500], can_scale=False),
    # Type of label: 0 indicates regression, 2+ indicates classification with this many classes
    # Note: multi-class (>2) is not supported in Spark 1.0.
    OptionSet("label-type", [0, 2], can_scale=False),
    # Fraction of features which are categorical
    OptionSet("frac-categorical-features", [0.5], can_scale=False),
    # Fraction of categorical features which are binary. Others have 20 categories.
    OptionSet("frac-binary-features", [0.5], can_scale=False),
    # Depth of true decision tree model used to label examples.
    # WARNING: The meaning of depth changed from Spark 1.0 to Spark 1.1:
    #          depth=N for Spark 1.0 should be depth=N-1 for Spark 1.1
    OptionSet("tree-depth", [5, 10], can_scale=False),
    # Maximum number of bins for the decision tree learning algorithm.
    OptionSet("max-bins", [32], can_scale=False),
]

if MLLIB_SPARK_VERSION >= 1.2:
    ensembleTypes = ["RandomForest"]
    if MLLIB_SPARK_VERSION >= 1.3:
        ensembleTypes.append("GradientBoostedTrees")
    if MLLIB_SPARK_VERSION >= 1.4:
        ensembleTypes.extend(["ml.RandomForest", "ml.GradientBoostedTrees"])
    MLLIB_DECISION_TREE_TEST_OPTS += [
        # Ensemble type: mllib.RandomForest, mllib.GradientBoostedTrees,
        #                ml.RandomForest, ml.GradientBoostedTrees
        OptionSet("ensemble-type", ensembleTypes),
        # Path to training dataset (if not given, use random data).
        OptionSet("training-data", [""]),
        # Path to test dataset (only used if training dataset given).
        # If not given, hold out part of training data for validation.
        OptionSet("test-data", [""]),
        # Fraction of data to hold out for testing
        #  (Ignored if given training and test dataset, or if using synthetic data.)
        OptionSet("test-data-fraction", [0.2], can_scale=False),
        # Number of trees. If 1, then run DecisionTree. If >1, then run RandomForest.
        OptionSet("num-trees", [1, 10], can_scale=False),
        # Feature subset sampling strategy: auto, all, sqrt, log2, onethird
        # (only used for RandomForest)
        OptionSet("feature-subset-strategy", ["auto"])
    ]

MLLIB_TESTS += [("decision-tree", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("decision-tree")] +
    MLLIB_DECISION_TREE_TEST_OPTS)]

# Recommendation Tests #
MLLIB_RECOMMENDATION_TEST_OPTS = MLLIB_COMMON_OPTS + [
     # The number of users
     OptionSet("num-users", [100000], can_scale=True),
     # The number of products
     OptionSet("num-products", [500000], can_scale=False),
     # The number of ratings
     OptionSet("num-ratings", [50000000], can_scale=True),
     # The number of iterations for ALS
     OptionSet("num-iterations", [10]),
     # The rank of the factorized matrix model
     OptionSet("rank", [10]),
     # The regularization parameter
     OptionSet("reg-param", [0.1]),
     # Whether to use implicit preferences or not
     FlagSet("implicit-prefs", [False])
]

MLLIB_TESTS += [("als", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("als")] +
    MLLIB_RECOMMENDATION_TEST_OPTS)]

# Clustering Tests #
MLLIB_CLUSTERING_TEST_OPTS = MLLIB_COMMON_OPTS + [
     # The number of examples
     OptionSet("num-examples", [1000000], can_scale=True),
     # The number of features per point
     OptionSet("num-features", [1000], can_scale=False),
     # The number of centers
     OptionSet("num-centers", [20]),
     # The number of iterations for KMeans
     OptionSet("num-iterations", [20])
]

MLLIB_TESTS += [("kmeans", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("kmeans")] + MLLIB_CLUSTERING_TEST_OPTS)]

MLLIB_GMM_TEST_OPTS = MLLIB_COMMON_OPTS + [
    OptionSet("num-examples", [1000000], can_scale=True),
    OptionSet("num-features", [100], can_scale=False),
    OptionSet("num-centers", [20], can_scale=False),
    OptionSet("num-iterations", [20])]

if MLLIB_SPARK_VERSION >= 1.3:
    MLLIB_TESTS += [("gmm", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("gmm")] + MLLIB_GMM_TEST_OPTS)]

MLLIB_LDA_TEST_OPTS = MLLIB_COMMON_OPTS + [
    OptionSet("num-documents", [50000], can_scale=True),
    OptionSet("num-vocab", [10000], can_scale=False),
    OptionSet("num-topics", [20], can_scale=False),
    OptionSet("num-iterations", [20]),
    OptionSet("document-length", [100]),
    OptionSet("optimizer", ["em", "online"])]

if MLLIB_SPARK_VERSION >= 1.4:
    MLLIB_TESTS += [("lda", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("lda")] + MLLIB_LDA_TEST_OPTS)]

MLLIB_PIC_TEST_OPTS = MLLIB_COMMON_OPTS + [
    OptionSet("num-examples", [10000000], can_scale=True),
    OptionSet("node-degree", [20], can_scale=False),
    OptionSet("num-centers", [40], can_scale=False),
    OptionSet("num-iterations", [20])]

if MLLIB_SPARK_VERSION >= 1.3:
    MLLIB_TESTS += [("pic", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("pic")] + MLLIB_PIC_TEST_OPTS)]

# Linear Algebra Tests #
MLLIB_LINALG_TEST_OPTS = MLLIB_COMMON_OPTS + [
    # The number of rows for the matrix
    OptionSet("num-rows", [1000000], can_scale=True),
    # The number of columns for the matrix
    OptionSet("num-cols", [1000], can_scale=False),
    # The number of top singular values wanted for SVD and PCA
    OptionSet("rank", [50], can_scale=False)
]
# Linear Algebra Tests which take more time (slightly smaller settings) #
MLLIB_BIG_LINALG_TEST_OPTS = MLLIB_COMMON_OPTS + [
    # The number of rows for the matrix
    OptionSet("num-rows", [1000000], can_scale=True),
    # The number of columns for the matrix
    OptionSet("num-cols", [500], can_scale=False),
    # The number of top singular values wanted for SVD and PCA
    OptionSet("rank", [10], can_scale=False)
]

MLLIB_TESTS += [("svd", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("svd")] + MLLIB_BIG_LINALG_TEST_OPTS)]

MLLIB_TESTS += [("pca", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("pca")] + MLLIB_LINALG_TEST_OPTS)]

MLLIB_TESTS += [("summary-statistics", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
    MLLIB_JAVA_OPTS, [ConstantOption("summary-statistics")] +
    MLLIB_BIG_LINALG_TEST_OPTS)]

MLLIB_BLOCK_MATRIX_MULT_TEST_OPTS = MLLIB_COMMON_OPTS + [
    OptionSet("m", [20000], can_scale=True),
    OptionSet("k", [10000], can_scale=False),
    OptionSet("n", [10000], can_scale=False),
    OptionSet("block-size", [1024], can_scale=False)]

if MLLIB_SPARK_VERSION >= 1.3:
   MLLIB_TESTS += [("block-matrix-mult", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
                   MLLIB_JAVA_OPTS, [ConstantOption("block-matrix-mult")] + MLLIB_BLOCK_MATRIX_MULT_TEST_OPTS)]

# Statistic Toolkit Tests #
MLLIB_STATS_TEST_OPTS = MLLIB_COMMON_OPTS

MLLIB_PEARSON_TEST_OPTS = MLLIB_STATS_TEST_OPTS + \
                          [OptionSet("num-rows", [1000000], can_scale=True),
                           OptionSet("num-cols", [1000], can_scale=False)]

MLLIB_SPEARMAN_TEST_OPTS = MLLIB_STATS_TEST_OPTS + \
                           [OptionSet("num-rows", [1000000], can_scale=True),
                            OptionSet("num-cols", [100], can_scale=False)]

MLLIB_CHI_SQ_FEATURE_TEST_OPTS = MLLIB_STATS_TEST_OPTS + \
                                 [OptionSet("num-rows", [2000000], can_scale=True),
                                  OptionSet("num-cols", [500], can_scale=False)]

MLLIB_CHI_SQ_GOF_TEST_OPTS = MLLIB_STATS_TEST_OPTS + \
                             [OptionSet("num-rows", [50000000], can_scale=True),
                              OptionSet("num-cols", [0], can_scale=False)]

MLLIB_CHI_SQ_MAT_TEST_OPTS = MLLIB_STATS_TEST_OPTS + \
                             [OptionSet("num-rows", [20000], can_scale=True),
                              OptionSet("num-cols", [0], can_scale=False)]

if MLLIB_SPARK_VERSION >= 1.1:
    MLLIB_TESTS += [("pearson", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("pearson")] + MLLIB_PEARSON_TEST_OPTS)]

    MLLIB_TESTS += [("spearman", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("spearman")] + MLLIB_SPEARMAN_TEST_OPTS)]

    MLLIB_TESTS += [("chi-sq-feature", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("chi-sq-feature")] + MLLIB_CHI_SQ_FEATURE_TEST_OPTS)]

    MLLIB_TESTS += [("chi-sq-gof", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("chi-sq-gof")] + MLLIB_CHI_SQ_GOF_TEST_OPTS)]

    MLLIB_TESTS += [("chi-sq-mat", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("chi-sq-mat")] + MLLIB_CHI_SQ_MAT_TEST_OPTS)]

# Feature Transformation Tests #

MLLIB_FEATURE_TEST_OPTS = MLLIB_COMMON_OPTS

MLLIB_WORD2VEC_TEST_OPTS = MLLIB_FEATURE_TEST_OPTS + \
                           [OptionSet("num-sentences", [1000000], can_scale=True),
                            OptionSet("num-words", [10000], can_scale=False),
                            OptionSet("vector-size", [100], can_scale=False),
                            OptionSet("num-iterations", [3], can_scale=False),
                            OptionSet("min-count", [5], can_scale=False)]

if MLLIB_SPARK_VERSION >= 1.3:  
    MLLIB_TESTS += [("word2vec", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("word2vec")] + MLLIB_WORD2VEC_TEST_OPTS)]

# Frequent Pattern Matching Tests #

MLLIB_FPM_TEST_OPTS = MLLIB_COMMON_OPTS

MLLIB_FP_GROWTH_TEST_OPTS = MLLIB_FPM_TEST_OPTS + \
                            [OptionSet("num-baskets", [5000000], can_scale=True),
                             OptionSet("avg-basket-size", [10], can_scale=False),
                             OptionSet("num-items", [1000], can_scale=False),
                             OptionSet("min-support", [0.01], can_scale=False)]

if MLLIB_SPARK_VERSION >= 1.3:
    MLLIB_TESTS += [("fp-growth", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("fp-growth")] + MLLIB_FP_GROWTH_TEST_OPTS)]

MLLIB_PREFIX_SPAN_TEST_OPTS = MLLIB_FPM_TEST_OPTS + \
                            [OptionSet("num-sequences", [5000000], can_scale=True),
                             OptionSet("avg-sequence-size", [5], can_scale=False),
                             OptionSet("avg-itemset-size", [2], can_scale=False),
                             OptionSet("num-items", [500], can_scale=False),
                             OptionSet("min-support", [0.5], can_scale=False),
                             OptionSet("max-pattern-len", [10], can_scale=False),
                             OptionSet("max-local-proj-db-size", [32000000], can_scale=False)]

if MLLIB_SPARK_VERSION >= 1.5:
    MLLIB_TESTS += [("prefix-span", MLLIB_PERF_TEST_RUNNER, SCALE_FACTOR,
        MLLIB_JAVA_OPTS, [ConstantOption("prefix-span")] + MLLIB_PREFIX_SPAN_TEST_OPTS)]

# Python MLlib tests
PYTHON_MLLIB_TESTS = []

#PYTHON_MLLIB_TESTS += [("python-glm-classification", "mllib_tests.py", SCALE_FACTOR,
#                         MLLIB_JAVA_OPTS, [ConstantOption("GLMClassificationTest")] +
#                         MLLIB_GLM_CLASSIFICATION_TEST_OPTS)]

#PYTHON_MLLIB_TESTS += [("python-glm-regression", "mllib_tests.py", SCALE_FACTOR,
#                         MLLIB_JAVA_OPTS, [ConstantOption("GLMRegressionTest")] +
#                         MLLIB_GLM_REGRESSION_TEST_OPTS)]

#PYTHON_MLLIB_TESTS += [("python-naive-bayes", "mllib_tests.py", SCALE_FACTOR,
#                         MLLIB_JAVA_OPTS, [ConstantOption("NaiveBayesTest")] +
#                         NAIVE_BAYES_TEST_OPTS)]

PYTHON_MLLIB_TESTS += [("python-als", "mllib_tests.py", SCALE_FACTOR,
                         MLLIB_JAVA_OPTS, [ConstantOption("ALSTest")] +
                         MLLIB_RECOMMENDATION_TEST_OPTS)]

PYTHON_MLLIB_TESTS += [("python-kmeans", "mllib_tests.py", SCALE_FACTOR,
                         MLLIB_JAVA_OPTS, [ConstantOption("KMeansTest")] + MLLIB_CLUSTERING_TEST_OPTS)]

#if MLLIB_SPARK_VERSION >= 1.1:
#     PYTHON_MLLIB_TESTS += [("python-pearson", "mllib_tests.py", SCALE_FACTOR,
#                              MLLIB_JAVA_OPTS, [ConstantOption("PearsonCorrelationTest")] +
#                              MLLIB_PEARSON_TEST_OPTS)]

#     PYTHON_MLLIB_TESTS += [("python-spearman", "mllib_tests.py", SCALE_FACTOR,
#                              MLLIB_JAVA_OPTS, [ConstantOption("SpearmanCorrelationTest")] +
#                              MLLIB_SPEARMAN_TEST_OPTS)]

