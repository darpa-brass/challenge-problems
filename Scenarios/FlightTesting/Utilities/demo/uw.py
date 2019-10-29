import os

import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket("dev-uw-logs")
key = 'bamboo/scheduler-env-UW-UWSCHED-20-master-682205c4327b72a5fd6f1bd6cb248c689ef6495d-release-10/BambooEvaluationInput.zip'
bucket.download_file(key, os.path.basename(key))
