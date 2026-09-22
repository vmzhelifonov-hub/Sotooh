import time

import boto3

t0 = time.time()
import cProfile
import pstats
import io

pr = cProfile.Profile()
pr.enable()
c = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="sotoohminio",
    aws_secret_access_key="sotoohminio_secret",
    region_name="us-east-1",
)
pr.disable()
t1 = time.time()
print("client:", round(t1 - t0, 2), "s")

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats(15)
print(s.getvalue()[:2500])