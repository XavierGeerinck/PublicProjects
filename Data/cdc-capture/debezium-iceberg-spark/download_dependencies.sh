#!/bin/bash
# ./download_dependencies.sh

mkdir -p ./spark/jars

# Download Iceberg Spark Runtime
curl -L -o ./spark/jars/iceberg-spark-runtime-3.3_2.13-1.3.1.jar https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.3_2.13/1.3.1/iceberg-spark-runtime-3.3_2.13-1.3.1.jar

# Download Hadoop AWS
curl -L -o ./spark/jars/hadoop-aws-3.3.2.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar

# Download AWS SDK
curl -L -o ./spark/jars/aws-java-sdk-bundle-1.12.367.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar
