import os

import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket("dev-bbn-logs")
key = 'bamboo/Scenario5/BBN-IM:105:master:3dfa38095571817ffab587b2f0f9d28adcb95eb8:demo/artifacts.zip'
bucket.download_file(key, os.path.basename(key))
