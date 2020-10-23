import local.dev_config
import local.secrets
from pprint import pprint
from thiscovery_lib.s3_utilities import S3Client


BUCKET = "s3-to-sdhs-test-afs25-mockincomingbucket"

s3 = S3Client()
objs = s3.list_objects(BUCKET)['Contents']
for o in objs:
    if o['Key'] == '427ff1f2-f0cf-4719-a1cf-1a561c1ba496/video/8a1fdf5a-061b-41a6-bee9-36ac3fba3fee.mp4':
        head = s3.head_object(BUCKET, o['Key'])
        pprint(head)
