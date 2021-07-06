#!/usr/bin/env python3

import boto3
import sys
import logging
import pprint
import argparse
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser(
	description="Script to empty out and possibly delete an S3 bucket.",
	prefix_chars='-+/')
parser.my_parser.add_argument(
	"-p", "--profile",
	dest="pProfile",
	metavar="profile to use",
	default="default",
	help="To specify a profile, use this parameter.")
parser.my_parser.add_argument(
	"-b", "--bucket",
	dest="pBucketName",
	metavar="bucket to empty and delete",
	required=True,
	help="To specify a profile, use this parameter.")
parser.my_parser.add_argument(
	'+delete', '+force-delete',
	help="Whether or not to delete the bucket after it's been emptied",
	action="store_const",
	dest="pForceQuit",
	const=True,
	default=False)
parser.my_parser.add_argument(
	'-v',
	help="Be verbose",
	action="store_const",
	dest="loglevel",
	const=logging.ERROR,  # args.loglevel = 40
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-vv', '--verbose',
	help="Be MORE verbose",
	action="store_const",
	dest="loglevel",
	const=logging.WARNING,  # args.loglevel = 30
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-vvv',
	help="Print INFO level statements",
	action="store_const",
	dest="loglevel",
	const=logging.INFO,  # args.loglevel = 20
	default=logging.CRITICAL)  # args.loglevel = 50
parser.my_parser.add_argument(
	'-d', '--debug',
	help="Print LOTS of debugging statements",
	action="store_const",
	dest="loglevel",
	const=logging.DEBUG,  # args.loglevel = 10
	default=logging.CRITICAL)
args = parser.my_parser.parse_args()

pProfile = args.pProfile
pBucketDelete = args.pForceQuit
pBucketName = args.pBucketName
logging.basicConfig(level=args.loglevel, format="[%(filename)s:%(lineno)s:%(levelname)s - %(funcName)20s() ] %(message)s")


session = boto3.Session(profile_name=pProfile)
s3 = session.resource(service_name='s3')

print()
print(f"This script is about to delete all versions of all objects from bucket {pBucketName}")
print()

try:
	bucket = s3.Bucket(pBucketName)
	# print(len(list(bucket.object_versions.all)))# Deletes everything in the bucket
	bucket.object_versions.delete()
except Exception as e:
	pprint.pprint(e)
	print("Error messages here")

DeleteBucket = False
if pBucketDelete:  # They provided the parameter that said they wanted to delete the bucket
	bucket.delete()
	print(f"Bucket: {pBucketName} has been deleted")
else:
	DeleteBucket = (input("Now that the bucket is empty, do you want to delete the bucket? (y/n): ") in ["y", "Y"])
	if DeleteBucket:
		bucket.delete()
		print(f"Bucket: {pBucketName} has been deleted")
	else:
		print(f"Bucket: {pBucketName} has NOT been deleted")
print()
print("Thanks for using this script...")
print()
