#!/usr/bin/env python3

"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import boto3, sys, logging, pprint
import argparse
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser(
	description="Script to empty out and possibly delete an S3 bucket.",
	prefix_chars='-+/')
parser.add_argument(
	"-p","--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a profile, use this parameter.")
parser.add_argument(
	"-b","--bucket",
	dest="pBucketName",
	metavar="bucket to empty and delete",
	required=True,
	help="To specify a profile, use this parameter.")
parser.add_argument(
	'+delete', '+force-delete',
	help="Whether or not to delete the bucket after it's been emptied",
	action="store_const",
	dest="pForceQuit",
	const=True,
	default=False)
parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR, # args.loglevel = 40
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING, # args.loglevel = 30
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,	# args.loglevel = 20
	default=logging.CRITICAL) # args.loglevel = 50
parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,	# args.loglevel = 10
	default=logging.CRITICAL)
args = parser.parse_args()

pProfile=args.pProfile
pBucketDelete=args.pForceQuit
pBucketName=args.pBucketName
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")


session = boto3.Session(profile_name=pProfile)
s3 = session.resource(service_name='s3')

print()
print("This script is about to delete all versions of all objects from bucket {}".format(pBucketName))
print()

try:
	bucket = s3.Bucket(pBucketName)
	# print(len(list(bucket.object_versions.all)))# Deletes everything in the bucket
	bucket.object_versions.delete()
except Exception as e:
	pprint.pprint(e)
	print("Error messages here")

DeleteBucket=False
if pBucketDelete:	# They provided the parameter that said they wanted to delete the bucket
	bucket.delete()
	print("Bucket: %s has been deleted" % pBucketName)
else:
	DeleteBucket = (input("Now that the bucket is empty, do you want to delete the bucket? (y/n): ") in ["y","Y"] )
	if DeleteBucket:
		bucket.delete()
		print("Bucket: %s has been deleted" % pBucketName)
	else:
		print("Bucket: %s has NOT been deleted" % pBucketName)
print()
print("Thanks for using this script...")
print()
