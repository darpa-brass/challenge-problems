import os

import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket("dev-cra-logs")
key = 'bamboo/CP2/demo/output/cp2/forward_switched_02_adapted_data.txt'
bucket.download_file(key, os.path.basename(key))
