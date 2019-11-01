import os

import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket("dev-cmus-logs")
key = 'bamboo/CP1/demo/Outputs/output/haswell.output/TmnsDAU_out.pcapng'
bucket.download_file(key, os.path.basename(key))
