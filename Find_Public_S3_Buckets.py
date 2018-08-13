import boto3, json
import argparse, sys

UsageMsg="You need to run this and provide the profile."
parser = argparse.ArgumentParser(description="We\'re going to find all publicly open S3 buckets.",prefix_chars='-+/')
parser.add_argument("-p","--profile", dest="pProfile", metavar="Profile", default="EmptyProfile", help="The Profile to use for access")
# parser.add_argument("-r","--region", dest="pRegion", metavar="Region", default="us-east-1", help="The Region where the VPC is located")
# parser.add_argument("-v","--vpcid", dest="pVPCId", metavar="VPCId", default="EmptyVPC",help="The ID of the VPC to forcibly delete")
# parser.add_argument("-d","--dryrun", dest="pDryRun", default=True, action='store_false', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
# parser.add_argument("+d","++dryrun", dest="pDryRun", default=True, action='store_true', help='Whether this is a DryRun or not. Default is TRUE (it\'s a dry-run), but \'-d\' will really run the script.')
# parser.add_argument("-b","--badcidr", dest="pBadSrcCIDR", metavar="BadSrcCIDR", default="0.0.0.0/0", help="The CIDR Range from which the SG is *inappropriately* open")
# parser.add_argument("-g","--goodcidr", dest="pGoodSrcCIDR", metavar="GoodSrcCIDR", nargs='+', default=["8.8.8.0/24","9.9.9.0/24"], help="The CIDR List you'd like to replace that with")

args=parser.parse_args()

# print("Profile:",args.pProfile, type(args.pProfile))
# print("Region:",args.pRegion, type(args.pRegion))
# print("VPC:",args.pVPCId, type(args.pVPCId))
# print("DryRun:",args.pDryRun, type(args.pDryRun))
if args.pProfile == 'EmptyProfile':
	print()
	print("The Profile parameter is required. Please try again")
	print()
	sys.exit("Required Parameters weren\'t set")

pProfile=args.pProfile
# pRegion=args.pRegion
# pVPCId=args.pVPCId
# pDryRun=args.pDryRun
# pBadSrcCIDR=args.pBadSrcCIDR
# pGoodSrcCIDR=args.pGoodSrcCIDR


session = boto3.session.Session(profile_name=pProfile)
s3_client_connection = session.resource(
	's3'
)

for bucket in s3_client_connection.buckets.all():
	print(bucket.name)
	acl = bucket.Acl()
	for grant in acl.grants:
	# check the grant here
		if grant['Grantee']['Type'].lower() == 'group' and grant['Grantee']['URI'] == 'http://acs.amazonaws.com/groups/global/AllUsers':
		# the grant is assigned to All Users (so it is public!!!)
			grant_permission = grant['Permission'].lower()
			if grant_permission == 'read':
				print('	Read - Public Access: List Objects')

			elif grant_permission == 'write':
				print('	Write - Public Access: Write Objects')

			elif grant_permission == 'read_acp':
				print('	Write - Public Access: Read Bucket Permissions')

			elif grant_permission == 'write_acp':
				print('	Write - Public Access: Write Bucket Permissions')

			elif grant_permission == 'full_control':
				print('	Public Access: Full Control')

		elif grant['Grantee']['Type'].lower() == 'group':	
# Get the Bucket Policy
	bucket_policy = s3_client_connection.BucketPolicy(bucket.name)
	try:
		# did not find a better way to check if a bucket has a policy using the resource object
		policy_obj = bucket_policy.policy
		print ("	Found bucket policy")
		policy = json.loads(policy_obj)
		if 'Statement' in policy:
			for p in policy['Statement']:
				if p['Principal'] == '*': # any public anonymous users!
					print(p['Action'])
	except Exception as e:
		pass # the S3 bucket does not have a bucket policy


				# You find a public S3 Action, do your stuff here (send email, post to Slack, write log and so on)

				# http://docs.aws.amazon.com/AmazonS3/latest/dev/using-with-s3-actions.html
				# Example of S3 actions/operations (in this case Object actions)

				# s3:DeleteObjectVersionTagging
				# s3:DeleteObjectVersion
				# s3:DeleteObjectTagging
				# s3:DeleteObject
				# s3:AbortMultipartUpload
				# s3:GetObjectAcl
				# s3:GetObjectTagging
				# s3:GetObjectTorrent
				# s3:GetObjectVersion
				# s3:GetObjectVersionAcl
				# s3:GetObjectVersionTagging
				# s3:GetObjectVersionTorrent
				# s3:PutObject
				# s3:PutObjectAcl
				# s3:PutObjectTagging
				# s3:PutObjectVersionAcl
				# s3:PutObjectVersionTagging
				# s3:RestoreObject
