#! /bin/bash
oc new-app --template diane-oshinko-pyspark-job --param=APPLICATION_NAME=glmclassificationtest --param=IMAGE=172.30.100.159:5000/perf-testing-d/mllibpy --param=APP_ARGS="GLMClassificationTest --num-trials=10 --num-partitions=128 --random-seed=5 --num-examples=500000 --feature-noise=1.0 --num-features=10000 --num-iterations=20 --step-size=0.001 --reg-type=l2 --reg-param=0.1 --elastic-net-param=0.0 --per-negative=0.3 --optimizer=sgd --loss=logistic"  --param=SPARK_OPTIONS="--executor-memory 32g --conf spark.default.parallelism=128 --conf spark.workers.memory=64g --conf spark.python.worker.memory=64g --conf spark.local.dir=/tmp" --param=OSHINKO_SPARK_DRIVER_CONFIG=oshinko-spark-driver-config  --param=COMPLETIONS=1  --param=OSHINKO_CLUSTER_NAME=dianememtst32 