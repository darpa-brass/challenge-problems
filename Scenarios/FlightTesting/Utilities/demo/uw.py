import os

import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket("dev-uw-logs")
key = 'bamboo/scheduler-env-demo/BambooEvaluationInput.zip'
bucket.download_file(key, os.path.basename(key))
