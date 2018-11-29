#!/usr/bin/env python

import boto3,sys

bucket_name=sys.argv[1]
pProfile=sys.argv[2]
session = boto3.Session(profile_name=pProfile)
s3 = session.resource(service_name='s3')
bucket = s3.Bucket(bucket_name)
bucket.object_versions.delete()
x = input("Now that the bucket is empty, do you want to delete the bucket? (y/n): ")
if (x=="y" or x=="Y"):
	bucket.delete()
	print("Bucket: %s has been deleted" % bucket_name)
else:
	print("Bucket: %s has NOT been deleted" % bucket_name)
