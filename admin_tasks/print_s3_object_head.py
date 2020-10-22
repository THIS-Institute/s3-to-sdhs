import local.dev_config
import local.secrets
from pprint import pprint
from thiscovery_lib.s3_utilities import S3Client


BUCKET = "s3-to-sdhs-test-afs25-mockincomingbucket"

s3 = S3Client()
objs = s3.list_objects(BUCKET)['Contents']
for o in objs:
    if o['Key'] == 'bc2c1b30-1777-49af-b93e-2d7e9e92ac99/video/ba56e21b-3b88-4ce1-a3eb-26d8d4529bd3.mp4':
        head = s3.head_object(BUCKET, o['Key'])
        pprint(head)
