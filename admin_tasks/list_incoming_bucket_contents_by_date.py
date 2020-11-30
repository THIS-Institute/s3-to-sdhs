import local.dev_config
from pprint import pprint

import thiscovery_lib.utilities as utils
from thiscovery_lib.s3_utilities import S3Client
from local.secrets import THISCOVERY_PROD_PROFILE


class BucketReporter:
    def __init__(self):
        self.s3 = S3Client(profile_name=THISCOVERY_PROD_PROFILE)
        self.s3_bucket_name = utils.get_secret("incoming-interviews-bucket", namespace_override='/prod/')['name']
        self.objs = self.get_sorted_contents()
        self.live_interviews = list()
        self.on_demand_interviews = list()

    def get_sorted_contents(self):
        objs = self.s3.list_objects(self.s3_bucket_name)['Contents']
        objs.sort(key=lambda x: x['LastModified'])
        return objs

    def filter_videos(self):
        return [x for x in self.objs if 'video' in x['Key']]

    def sort_live_and_on_demand(self):
        for o in self.objs:
            head = self.s3.head_object(self.s3_bucket_name, o['Key'])
            if head['Metadata']:
                if 'referrer' in head['Metadata'].keys():
                    self.on_demand_interviews.append({**o, **head})
                else:
                    self.live_interviews.append({**o, **head})

    def print_live_interviews_report(self):
        print('Live interviews:')
        for i in self.live_interviews:
            print(
                f"\t{i['Key']}\n"
                f"\t{i['LastModified']}\n"
                f"\t{i['Metadata']['interviewer']}\n"
                f"\t{i['Metadata']['email']}\n"
                f"\n"
            )

    def print_on_demand_interviews_report(self):
        print('On-demand interviews:')
        for i in self.on_demand_interviews:
            print(
                f"\t{i['Key']}\n"
                f"\t{i['LastModified']}\n"
                f"\t{i['Metadata']['referrer']}\n"
                f"\t{i['Metadata']['email']}\n"
                f"\n"
            )


if __name__ == '__main__':
    reporter = BucketReporter()
    reporter.sort_live_and_on_demand()
    # reporter.print_on_demand_interviews_report()
    reporter.print_live_interviews_report()
