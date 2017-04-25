import luigi
import json
import time
import re
import datetime
import subprocess
import base64
from urllib import urlopen
import uuid
from uuid import uuid4
from uuid import uuid5
from elasticsearch import Elasticsearch
#for hack to get around non self signed certificates
import ssl
import sys

# TODO
# * I think we want to use S3 for our touch files (aka lock files) since that will be better than local files that could be lost/deleted
# * I have the consonance call turned off here until I figure out why bamstats on rnaseq produces an empty report

class ConsonanceTaskV2(luigi.Task):
    redwood_host = luigi.Parameter("storage.ucsc-cgl.org")
    redwood_token = luigi.Parameter("must_be_defined")
    dockstore_tool_running_dockstore_tool = luigi.Parameter(default="quay.io/ucsc_cgl/dockstore-tool-runner:1.0.7")
    target_tool = luigi.Parameter(default="quay.io/briandoconnor/dockstore-tool-bamstats:1.25-11")
    target_tool_url = luigi.Parameter(default="https://dockstore.org/containers/quay.io/briandoconnor/dockstore-tool-bamstats")
    workflow_type = luigi.Parameter(default="alignment_qc_report")
    image_descriptor = luigi.Parameter(default="must be defined")
    filename = luigi.Parameter(default="filename")
    file_uuid = luigi.Parameter(default="uuid")
    bundle_uuid = luigi.Parameter(default="bundle_uuid")
    parent_uuids = luigi.ListParameter(default=["parent_uuid"])
    tmp_dir = luigi.Parameter(default='/tmp')

    def run(self):
        print "** EXECUTING IN CONSONANCE **"
        print "** MAKE TEMP DIR **"
        # create a unique temp dir
        cmd = '''mkdir -p %s/consonance-jobs/AlignmentQCCoordinator/%s/''' % (self.tmp_dir, self.get_task_uuid())
        print cmd
        result = subprocess.call(cmd, shell=True)
        if result != 0:
            print "PROBLEMS MAKING DIR!!"
        print "** MAKE JSON FOR WORKER **"
        # create a json for FastQC which will be executed by the dockstore-tool-running-dockstore-tool and passed as base64encoded
        # will need to encode the JSON above in this: https://docs.python.org/2/library/base64.html
        # see http://luigi.readthedocs.io/en/stable/api/luigi.parameter.html?highlight=luigi.parameter
        json_str = '''{
        "bam_input":
        {
            "class": "File",
            "path": "redwood://%s/%s/%s/%s"
        },
                    ''' % (self.redwood_host, self.bundle_uuid, self.file_uuid, self.filename)
        json_str = json_str + '''"bamstats_report" :
          {
            "class": "File",
            "path": "./tmp/bamstats_report.zip"
          }
        }
        '''
        print "THE JSON: "+json_str
        # now make base64 encoded version
        base64_json_str = base64.urlsafe_b64encode(json_str)
        print "** MAKE JSON FOR DOCKSTORE TOOL WRAPPER **"
        # create a json for dockstoreRunningDockstoreTool, embed the FastQC JSON as a param
        p = self.output().open('w')
        print >>p, '''{
            "json_encoded": "%s",
            "docker_uri": "%s",
            "dockstore_url": "%s",
            "redwood_token": "%s",
            "redwood_host": "%s",
            "parent_uuids": "%s",
            "workflow_type": "%s",
            "tmpdir": "/datastore",
            "vm_instance_type": "c4.8xlarge",
            "vm_region": "us-west-2",
            "vm_location": "aws",
            "vm_instance_cores": 36,
            "vm_instance_mem_gb": 60,
            "output_metadata_json": "/tmp/final_metadata.json"
        }''' % (base64_json_str, self.target_tool, self.target_tool_url, self.redwood_token, self.redwood_host, ','.join(map("{0}".format, self.parent_uuids)), self.workflow_type)
        p.close()
        # execute consonance run, parse the job UUID
        print "** SUBMITTING TO CONSONANCE **"
        cmd = ["consonance", "run", "--image-descriptor", self.image_descriptor, "--flavour", "c4.8xlarge", "--run-descriptor", p.path]
        print "executing:"+ ' '.join(cmd)
#        try:
#            result = subprocess.call(cmd)
#        except Exception as e:
#            print "Error in Consonance call!!!:" + e.message
#
#        if result == 0:
#            print "Consonance job return success code!"
#        else:
#            print "ERROR: Consonance job failed!!!"

    def output(self):
        return luigi.LocalTarget('%s/consonance-jobs/AlignmentQCCoordinator/%s/settings.json' % (self.tmp_dir, self.get_task_uuid()))

    def get_task_uuid(self):
        #get a unique id for this task based on the some inputs
        #this id will not change if the inputs are the same
        #This helps make the task idempotent; it that it
        #always has the same task id for the same inputs
        reload(sys)
        sys.setdefaultencoding('utf8')
        print "FILENAME: "+self.filename+" FILE UUID: "+ self.file_uuid +" TARGET TOOL: "+ self.target_tool +" Target TOOL URL "+ self.target_tool_url +" REDWOOD TOKEN: "+ self.redwood_token +" REDWOOD HOST "+ self.redwood_host
        task_uuid = uuid5(uuid.NAMESPACE_DNS, (self.filename + self.file_uuid + self.target_tool + self.target_tool_url + self.redwood_token + self.redwood_host).encode('utf-8'))
        return task_uuid

class AlignmentQCCoordinatorV2(luigi.Task):

    es_index_host = luigi.Parameter(default='localhost')
    es_index_port = luigi.Parameter(default='9200')
    redwood_token = luigi.Parameter("must_be_defined")
    redwood_client_path = luigi.Parameter(default='../ucsc-storage-client')
    redwood_host = luigi.Parameter(default='storage.ucsc-cgl.org')
    image_descriptor = luigi.Parameter(default="must be defined")
    dockstore_tool_running_dockstore_tool = luigi.Parameter(default="quay.io/ucsc_cgl/dockstore-tool-runner:1.0.7")
    tmp_dir = luigi.Parameter(default='/tmp')
    data_dir = luigi.Parameter(default='/tmp/data_dir')
    max_jobs = luigi.Parameter(default='1')
    bundle_uuid_filename_to_file_uuid = {}

    def requires(self):
        print "** COORDINATOR **"
        # now query the metadata service so I have the mapping of bundle_uuid & file names -> file_uuid
        print str("https://"+self.redwood_host+":8444/entities?page=0")
        #hack to get around none self signed certificates
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        json_str = urlopen(str("https://"+self.redwood_host+":8444/entities?page=0"), context=ctx).read()
        metadata_struct = json.loads(json_str)
        print "** METADATA TOTAL PAGES: "+str(metadata_struct["totalPages"])
        for i in range(0, metadata_struct["totalPages"]):
            print "** CURRENT METADATA TOTAL PAGES: "+str(i)
            json_str = urlopen(str("https://"+self.redwood_host+":8444/entities?page="+str(i)), context=ctx).read()
            metadata_struct = json.loads(json_str)
            for file_hash in metadata_struct["content"]:
                self.bundle_uuid_filename_to_file_uuid[file_hash["gnosId"]+"_"+file_hash["fileName"]] = file_hash["id"]

        # now query elasticsearch
        es = Elasticsearch([{'host': self.es_index_host, 'port': self.es_index_port}])
        # see jqueryflag_alignment_qc
        # curl -XPOST http://localhost:9200/analysis_index/_search?pretty -d @jqueryflag_alignment_qc
        res = es.search(index="analysis_index", body={"query" : {"bool" : {"should" : [{"term" : { "flags.normal_alignment_qc_report" : "false"}},{"term" : {"flags.tumor_alignment_qc_report" : "false" }}],"minimum_should_match" : 1 }}}, size=5000)

        listOfJobs = []

        print("Got %d Hits:" % res['hits']['total'])
        for hit in res['hits']['hits']:
            print("\n\n\n%(donor_uuid)s %(submitter_donor_id)s %(center_name)s %(project)s" % hit["_source"])
            for specimen in hit["_source"]["specimen"]:
                for sample in specimen["samples"]:
                    for analysis in sample["analysis"]:
                        if (analysis["analysis_type"] == "alignment" or analysis["analysis_type"] == "rna_seq_quantification") and \
                              ((hit["_source"]["flags"]["normal_alignment_qc_report"] == False and \
                                   re.match("^Normal - ", specimen["submitter_specimen_type"]) and \
                                   sample["sample_uuid"] in hit["_source"]["missing_items"]["normal_alignment_qc_report"]) or \
                               (hit["_source"]["flags"]["tumor_alignment_qc_report"] == False and \
                                   re.match("^Primary tumour - |^Recurrent tumour - |^Metastatic tumour - |^Xenograft - |^Cell line - ", specimen["submitter_specimen_type"]) and \
                                   sample["sample_uuid"] in hit["_source"]["missing_items"]["tumor_alignment_qc_report"])):
                            print "HIT!!!! "+analysis["analysis_type"]+" "+str(hit["_source"]["flags"]["normal_alignment_qc_report"])+" "+specimen["submitter_specimen_type"]
                            parent_uuids = []
                            parent_uuids.append(sample["sample_uuid"])
                            for file in analysis["workflow_outputs"]:
                                if file["file_type"] == "bam":
                                    print "  + will run report for %s file" % (file["file_path"])
                                    if len(listOfJobs) < int(self.max_jobs):
                                        listOfJobs.append(ConsonanceTaskV2(redwood_host=self.redwood_host, redwood_token=self.redwood_token, dockstore_tool_running_dockstore_tool=self.dockstore_tool_running_dockstore_tool, filename=file["file_path"], file_uuid = self.fileToUUID(file["file_path"], analysis["bundle_uuid"]), bundle_uuid = analysis["bundle_uuid"], parent_uuids = parent_uuids, tmp_dir=self.tmp_dir, image_descriptor=self.image_descriptor))
        # these jobs are yielded to
        return listOfJobs

    def run(self):
        # now make a final report
        f = self.output().open('w')
        # TODO: could print report on what was successful and what failed?  Also, provide enough details like donor ID etc
        print >>f, "batch is complete"
        f.close()

    def output(self):
        # the final report
        ts = time.time()
        ts_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
        return luigi.LocalTarget('%s/consonance-jobs/AlignmentQCCoordinator/AlignmentQCTask-%s.txt' % (self.tmp_dir, ts_str))

    def fileToUUID(self, input, bundle_uuid):
        return self.bundle_uuid_filename_to_file_uuid[bundle_uuid+"_"+input]

if __name__ == '__main__':
    luigi.run()
