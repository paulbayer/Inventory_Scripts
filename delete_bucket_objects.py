import boto3,sys

bucket_name=sys.argv[1]
pProfile=sys.argv[2]
session = boto3.Session(profile_name=pProfile)
s3 = session.resource(service_name='s3')
bucket = s3.Bucket(bucket_name)
bucket.object_versions.delete()
bucket.delete()
