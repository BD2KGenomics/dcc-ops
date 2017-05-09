from __future__ import print_function, division

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
import os
import sys
import copy

from elasticsearch import Elasticsearch

#for hack to get around non self signed certificates
import ssl

#Amazon S3 support for writing touch files to S3
from luigi.s3 import S3Target
#luigi S3 uses boto for AWS credentials
import boto

class ConsonanceTask(luigi.Task):
    redwood_host = luigi.Parameter("storage.ucsc-cgl.org")
    redwood_token = luigi.Parameter("must_be_defined")
    dockstore_tool_running_dockstore_tool = luigi.Parameter(default="quay.io/ucsc_cgl/dockstore-tool-runner:1.0.12")

    workflow_version = luigi.Parameter(default="must be defined")

    target_tool_prefix = luigi.Parameter(default="quay.io/ucsc_cgl/rnaseq-cgl-pipeline")
    

    target_tool_url = luigi.Parameter(default="https://dockstore.org/containers/quay.io/ucsc_cgl/rnaseq-cgl-pipeline")
    workflow_type = luigi.Parameter(default="rna_seq_quantification")
    image_descriptor = luigi.Parameter("must be defined")

    disable_cutadapt = luigi.Parameter(default="false")
    save_bam = luigi.Parameter(default="true")
    save_wiggle = luigi.Parameter(default="true")
    no_clean = luigi.Parameter(default="true")
    resume = luigi.Parameter(default="")
    cores = luigi.Parameter(default=36)
    bamqc = luigi.Parameter(default="true")

    paired_filenames = luigi.ListParameter(default=["must input sample files"])
    paired_file_uuids = luigi.ListParameter(default=["uuid"])
    paired_bundle_uuids = luigi.ListParameter(default=["bundle_uuid"])

    single_filenames = luigi.ListParameter(default=["must input sample files"])
    single_file_uuids = luigi.ListParameter(default=["uuid"])
    single_bundle_uuids = luigi.ListParameter(default=["bundle_uuid"])

    tar_filenames = luigi.ListParameter(default=["must input sample files"])
    tar_file_uuids = luigi.ListParameter(default=["uuid"])
    tar_bundle_uuids = luigi.ListParameter(default=["bundle_uuid"])

    parent_uuids = luigi.ListParameter(default=["parent_uuid"])

    rsem_file_name = luigi.Parameter(default="must input rsem file name")
    rsem_bundle_uuid = luigi.Parameter(default="uuid")
    rsem_file_uuid = luigi.Parameter(default="bundle_uuid")

    star_file_name = luigi.Parameter(default="must input star file name")
    star_bundle_uuid = luigi.Parameter(default="uuid")
    star_file_uuid = luigi.Parameter(default="bundle_uuid")

    kallisto_file_name = luigi.Parameter(default="must input kaillisto file name")
    kallisto_bundle_uuid = luigi.Parameter(default="uuid")
    kallisto_file_uuid = luigi.Parameter(default="bundle_uuid")


    tmp_dir = luigi.Parameter(default='/datastore')

    submitter_sample_id = luigi.Parameter(default='must input submitter sample id')
    meta_data_json = luigi.Parameter(default="must input metadata")
    touch_file_path = luigi.Parameter(default='must input touch file path')

    vm_region = luigi.Parameter(default='us-east-1')
    
    #Consonance will not be called in test mode
    test_mode = luigi.BoolParameter(default = False)


    def run(self):
        print("\n\n\n** TASK RUN **")

#        print "** MAKE TEMP DIR **"
       
        # create a temp dir on the local disk to hold the
        # parameterized JSON file so that consonance can read it.
        # Consonance cannot read a file on S3 so we have to have
        # a local copy of the JSON
        local_json_dir = "/tmp/" + self.touch_file_path
        cmd = ["mkdir", "-p", local_json_dir ]
        cmd_str = ''.join(cmd)
        print(cmd_str)
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            #If we get here then the called command return code was non zero
            print("\nERROR!!! MAKING LOCAL JSON DIR : " + cmd_str + " FAILED !!!", file=sys.stderr)
            print("\nReturn code:" + str(e.returncode), file=sys.stderr)
            return_code = e.returncode
            sys.exit(return_code)
        except Exception as e:
            print("\nERROR!!! MAKING LOCAL JSON DIR : " + cmd_str + " THREW AN EXCEPTION !!!", file=sys.stderr)
            print("\nException information:" + str(e), file=sys.stderr)
            #if we get here the called command threw an exception other than just
            #returning a non zero return code, so just set the return code to 1
            return_code = 1
            sys.exit(return_code)


        #convert the meta data to a python data structure
        meta_data = json.loads(self.meta_data_json)

        print("** MAKE JSON FOR WORKER **")
        # create a json for RNA-Seq which will be executed by the dockstore-tool-running-dockstore-tool and passed as base64encoded
        # will need to encode the JSON above in this: https://docs.python.org/2/library/base64.html
        # see http://luigi.readthedocs.io/en/stable/api/luigi.parameter.html?highlight=luigi.parameter
        # TODO: this is tied to the requirements of the tool being targeted
        json_str = '''
{
'''
        if len(self.paired_filenames) > 0:
            json_str += '''
"sample-paired": [
        '''
            i = 0
            while i<len(self.paired_filenames):
                # append file information
                json_str += '''
            {
              "class": "File",
              "path": "redwood://%s/%s/%s/%s"
            }''' % (self.redwood_host, self.paired_bundle_uuids[i], self.paired_file_uuids[i], self.paired_filenames[i])
                if i < len(self.paired_filenames) - 1:
                   json_str += ","
                i += 1
            json_str += '''
  ],
            '''

        if len(self.single_filenames) > 0:
            json_str += '''
"sample-single": [
        '''
            i = 0
            while i<len(self.single_filenames):
                # append file information
                json_str += '''
            {
               "class": "File",
               "path": "redwood://%s/%s/%s/%s"
            }''' % (self.redwood_host, self.single_bundle_uuids[i], self.single_file_uuids[i], self.single_filenames[i])
                if i < len(self.single_filenames) - 1:
                    json_str += ","
                i += 1
            json_str += '''
  ],
            '''

        if len(self.tar_filenames) > 0:
            json_str += '''
"sample-tar": [
        '''
            i = 0
            while i<len(self.tar_filenames):
                # append file information
                json_str += '''
            {
              "class": "File",
              "path": "redwood://%s/%s/%s/%s"
            }''' % (self.redwood_host, self.tar_bundle_uuids[i], self.tar_file_uuids[i], self.tar_filenames[i])
                if i < len(self.tar_filenames) - 1:
                    json_str += ","
                i += 1
            json_str += '''
  ],
            '''



        json_str += '''
"rsem":
  {
    "class": "File",
    "path": "redwood://%s/%s/%s/%s"
  },
            ''' %  (self.redwood_host, self.rsem_bundle_uuid, self.rsem_file_uuid, self.rsem_file_name)

        json_str += '''
"star":
  {
    "class": "File",
    "path": "redwood://%s/%s/%s/%s"
  },
            ''' % (self.redwood_host, self.star_bundle_uuid, self.star_file_uuid, self.star_file_name)


        json_str += '''
"kallisto":
  {
    "class": "File",
    "path": "redwood://%s/%s/%s/%s"
  },
            ''' % (self.redwood_host, self.kallisto_bundle_uuid, self.kallisto_file_uuid, self.kallisto_file_name)

        json_str += '''
"save-wiggle": %s,
''' % self.save_wiggle

        json_str += '''
"no-clean": %s,
''' % self.no_clean

        json_str += '''
"save-bam": %s,
''' % self.save_bam

        json_str += '''
"disable-cutadapt": %s,
''' % self.disable_cutadapt

        json_str += '''
"resume": "%s",
''' % self.resume

        json_str += '''
"cores": %d,
''' % self.cores

        json_str += '''
"work-mount": "%s",
 ''' % self.tmp_dir

        json_str += '''
"bamqc": %s,
''' % self.bamqc

        json_str += '''
"output-basename": "%s",
''' % self.submitter_sample_id

        json_str += '''
"output_files": [
        '''
        new_filename = self.submitter_sample_id + '.tar.gz'
        json_str += '''
    {
      "class": "File",
      "path": "/tmp/%s"
    }''' % (new_filename)
 

        json_str += '''
  ]'''


        # if the user wants to save the wiggle output file
        if self.save_wiggle == 'true':
            json_str += ''',

"wiggle_files": [
        '''
            new_filename = self.submitter_sample_id + '.wiggle.bg'
            json_str += '''
    {
      "class": "File",
      "path": "/tmp/%s"
    }''' % (new_filename)
 
            json_str += '''
  ]'''

        # if the user wants to save the BAM output file
        if self.save_bam == 'true':
            json_str += ''',

"bam_files": [
        '''
            new_filename = self.submitter_sample_id + '.sortedByCoord.md.bam'
            json_str += '''
    {
      "class": "File",
      "path": "/tmp/%s"
    }''' % (new_filename)
 
            json_str += '''
  ]'''


        json_str += '''
}
'''

        print("THE JSON: "+json_str)
        # now make base64 encoded version
        base64_json_str = base64.urlsafe_b64encode(json_str)
        print("** MAKE JSON FOR DOCKSTORE TOOL WRAPPER **")
        # create a json for dockstoreRunningDockstoreTool, embed the RNA-Seq JSON as a param
# below used to be a list of parent UUIDs; which is correct????
#            "parent_uuids": "[%s]",
        parent_uuids = ','.join(map("{0}".format, self.parent_uuids))

        print("parent uuids:%s" % parent_uuids)

        p = self.save_dockstore_json().open('w')
        p_local = self.save_dockstore_json_local().open('w')

        target_tool= self.target_tool_prefix + ":" + self.workflow_version

        dockstore_json_str = '''{
            "program_name": "%s",
            "json_encoded": "%s",
            "docker_uri": "%s",
            "dockstore_url": "%s",
            "redwood_token": "%s",
            "redwood_host": "%s",
            "parent_uuids": "%s",
            "workflow_type": "%s",
            "tmpdir": "%s",
            "vm_instance_type": "c4.8xlarge",
            "vm_region": "%s",
            "vm_location": "aws",
            "vm_instance_cores": 36,
            "vm_instance_mem_gb": 60,
            "output_metadata_json": "/tmp/final_metadata.json"
        }''' % (meta_data["program"].replace(' ','_'), base64_json_str, target_tool, self.target_tool_url, self.redwood_token, self.redwood_host, parent_uuids, self.workflow_type, self.tmp_dir, self.vm_region )

        print(dockstore_json_str, file=p)
        p.close()
    
        # write the parameterized JSON for input to Consonance
        # to a local file since Consonance cannot read files on s3
        print(dockstore_json_str, file=p_local)
        p_local.close()

        # execute consonance run, parse the job UUID
#        cmd = ["consonance", "run", "--image-descriptor", self.image_descriptor, "--flavour", "c4.8xlarge", "--run-descriptor", self.save_dockstore_json_local().path]
        cmd = ["consonance", "run",  "--tool-dockstore-id", self.dockstore_tool_running_dockstore_tool, "--flavour", "c4.8xlarge", "--run-descriptor", self.save_dockstore_json_local().path]
        cmd_str = ' '.join(cmd)
        if self.test_mode == False:
            print("** SUBMITTING TO CONSONANCE **")
            print("executing:"+ cmd_str)
            print("** WAITING FOR CONSONANCE **")

            try:
                consonance_output_json = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                #If we get here then the called command return code was non zero
                print("\nERROR!!! CONSONANCE CALL: " + cmd_str + " FAILED !!!", file=sys.stderr)
                print("\nReturn code:" + str(e.returncode), file=sys.stderr)

                return_code = e.returncode
                sys.exit(return_code)
            except Exception as e:
                print("\nERROR!!! CONSONANCE CALL: " + cmd_str + " THREW AN EXCEPTION !!!", file=sys.stderr)
                print("\nException information:" + str(e), file=sys.stderr)
                #if we get here the called command threw an exception other than just
                #returning a non zero return code, so just set the return code to 1
                return_code = 1
                sys.exit(return_code)

            print("Consonance output is:\n\n{}\n--end consonance output---\n\n".format(consonance_output_json))

            #get consonance job uuid from output of consonance command
            consonance_output = json.loads(consonance_output_json)            
            if "job_uuid" in consonance_output:
                meta_data["consonance_job_uuid"] = consonance_output["job_uuid"]
            else:
                print("ERROR: COULD NOT FIND CONSONANCE JOB UUID IN CONSONANCE OUTPUT!", file=sys.stderr)
        else:
            print("TEST MODE: Consonance command would be:"+ cmd_str)
            meta_data["consonance_job_uuid"] = 'no consonance id in test mode'

        #remove the local parameterized JSON file that
        #was created for the Consonance call
        #since the Consonance call is finished
        self.save_dockstore_json_local().remove()

        #convert the meta data to a string and
        #save the donor metadata for the sample being processed to the touch
        # file directory
        meta_data_json = json.dumps(meta_data)
        m = self.save_metadata_json().open('w')
        print(meta_data_json, file=m)
        m.close()

            
#        if result == 0:
#            cmd = "rm -rf "+self.data_dir+"/"+self.bundle_uuid+"/bamstats_report.zip "+self.data_dir+"/"+self.bundle_uuid+"/datastore/"
#            print "CLEANUP CMD: "+cmd
#            result = subprocess.call(cmd, shell=True)
#            if result == 0:
#                print "CLEANUP SUCCESSFUL"

         # NOW MAke a final report
        f = self.output().open('w')
        # TODO: could print report on what was successful and what failed?  Also, provide enough details like donor ID etc
        print("Consonance task is complete", file=f) 
        f.close()
        print("\n\n\n\n** TASK RUN DONE **")

    def save_metadata_json(self):
        #task_uuid = self.get_task_uuid()
        #return luigi.LocalTarget('%s/consonance-jobs/RNASeq_3_1_x_Coordinator/fastq_gz/%s/metadata.json' % (self.tmp_dir, task_uuid))
        #return S3Target('s3://cgl-core-analysis-run-touch-files/consonance-jobs/RNASeq_3_1_x_Coordinator/%s/metadata.json' % ( task_uuid))
        return S3Target('s3://%s/%s_meta_data.json' % (self.touch_file_path, self.submitter_sample_id ))

    def save_dockstore_json_local(self):
        #task_uuid = self.get_task_uuid()
        #luigi.LocalTarget('%s/consonance-jobs/RNASeq_3_1_x_Coordinator/fastq_gz/%s/dockstore_tool.json' % (self.tmp_dir, task_uuid))
        #return S3Target('s3://cgl-core-analysis-run-touch-files/consonance-jobs/RNASeq_3_1_x_Coordinator/%s/dockstore_tool.json' % ( task_uuid))
        #return S3Target('%s/%s_dockstore_tool.json' % (self.touch_file_path, self.submitter_sample_id ))
        return luigi.LocalTarget('/tmp/%s/%s_dockstore_tool.json' % (self.touch_file_path, self.submitter_sample_id ))

    def save_dockstore_json(self):
        #task_uuid = self.get_task_uuid()
        #luigi.LocalTarget('%s/consonance-jobs/RNASeq_3_1_x_Coordinator/fastq_gz/%s/dockstore_tool.json' % (self.tmp_dir, task_uuid))
        #return S3Target('s3://cgl-core-analysis-run-touch-files/consonance-jobs/RNASeq_3_1_x_Coordinator/%s/dockstore_tool.json' % ( task_uuid))
        return S3Target('s3://%s/%s_dockstore_tool.json' % (self.touch_file_path, self.submitter_sample_id ))

    def output(self):
        #task_uuid = self.get_task_uuid()
        #return luigi.LocalTarget('%s/consonance-jobs/RNASeq_3_1_x_Coordinator/fastq_gz/%s/finished.txt' % (self.tmp_dir, task_uuid))
        #return S3Target('s3://cgl-core-analysis-run-touch-files/consonance-jobs/RNASeq_3_1_x_Coordinator/%s/finished.txt' % ( task_uuid))
        return S3Target('s3://%s/%s_finished.json' % (self.touch_file_path, self.submitter_sample_id ))

class RNASeqCoordinator(luigi.Task):

    es_index_host = luigi.Parameter(default='localhost')
    es_index_port = luigi.Parameter(default='9200')
    redwood_token = luigi.Parameter("must_be_defined")
    redwood_host = luigi.Parameter(default='storage.ucsc-cgl.org')
    image_descriptor = luigi.Parameter("must be defined")
    dockstore_tool_running_dockstore_tool = luigi.Parameter(default="quay.io/ucsc_cgl/dockstore-tool-runner:1.0.12")
    tmp_dir = luigi.Parameter(default='/datastore')
    max_jobs = luigi.Parameter(default='1')
    bundle_uuid_filename_to_file_uuid = {}
    process_sample_uuid = luigi.Parameter(default = "")

    workflow_version = luigi.Parameter(default="3.2.1-1")
    touch_file_bucket = luigi.Parameter(default="must be input") 

    vm_region = luigi.Parameter(default='us-east-1')

    #Consonance will not be called in test mode
    test_mode = luigi.BoolParameter(default = False)


    def requires(self):
        print("\n\n\n\n** COORDINATOR REQUIRES **")

        # now query the metadata service so I have the mapping of bundle_uuid & file names -> file_uuid
        print(str("metadata."+self.redwood_host+"/entities?page=0"))

#hack to get around none self signed certificates
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        json_str = urlopen(str("https://metadata."+self.redwood_host+"/entities?page=0"), context=ctx).read()

        metadata_struct = json.loads(json_str)
        print("** METADATA TOTAL PAGES: "+str(metadata_struct["totalPages"]))
        for i in range(0, metadata_struct["totalPages"]):
            print("** CURRENT METADATA TOTAL PAGES: "+str(i))
            json_str = urlopen(str("https://metadata."+self.redwood_host+"/entities?page="+str(i)), context=ctx).read()
            metadata_struct = json.loads(json_str)
            for file_hash in metadata_struct["content"]:
                self.bundle_uuid_filename_to_file_uuid[file_hash["gnosId"]+"_"+file_hash["fileName"]] = file_hash["id"]

        # now query elasticsearch
        print("setting up elastic search Elasticsearch([\"http:\/\/"+self.es_index_host+":"+self.es_index_port+"]") 
        es = Elasticsearch(['http://'+self.es_index_host+":"+self.es_index_port])
        res = es.search(index="analysis_index", body={"query" : {"bool" : {"should" : [{"term" : { "flags.normal_rna_seq_cgl_workflow_3_0_x" : "false"}},{"term" : {"flags.tumor_rna_seq_cgl_workflow_3_0_x" : "false" }}],"minimum_should_match" : 1 }}}, size=5000)

        listOfJobs = []

        print("Got %d Hits:" % res['hits']['total'])
        for hit in res['hits']['hits']:
            print("\n\n\nDonor uuid:%(donor_uuid)s Center Name:%(center_name)s Program:%(program)s Project:%(project)s" % hit["_source"])
            print("Got %d specimens:" % len(hit["_source"]["specimen"]))
            
            #DEBUGGING ONLY!!!!
#            if(hit["_source"]["program"] != "RNA-Seq-CHR6-TEST"):
#                continue

            disable_cutadapt = 'false'
            if(hit["_source"]["project"] == "CHR6"):
                rsem_json = urlopen(str("https://metadata."+self.redwood_host+"/entities?fileName=rsem_ref_chr6.tar.gz"), context=ctx).read()
                star_json = urlopen(str("https://metadata."+self.redwood_host+"/entities?fileName=starIndex_chr6.tar.gz"), context=ctx).read()
                disable_cutadapt = 'true'
                print("project is:CHR6")
            else:
                rsem_json = urlopen(str("https://metadata."+self.redwood_host+"/entities?fileName=rsem_ref_hg38_no_alt.tar.gz"), context=ctx).read()
                star_json = urlopen(str("https://metadata."+self.redwood_host+"/entities?fileName=starIndex_hg38_no_alt.tar.gz"), context=ctx).read()

            kallisto_json = urlopen(str("https://metadata."+self.redwood_host+"/entities?fileName=kallisto_hg38.idx"), context=ctx).read()

            kallisto_data = json.loads(kallisto_json)
            print(str(kallisto_data))
            kallisto_bundle_uuid = kallisto_data["content"][0]["gnosId"]
            kallisto_file_uuid = kallisto_data["content"][0]["id"]
            kallisto_file_name = kallisto_data["content"][0]["fileName"]

            rsem_data = json.loads(rsem_json)
            print(str(rsem_data))
            rsem_bundle_uuid = rsem_data["content"][0]["gnosId"]
            rsem_file_uuid = rsem_data["content"][0]["id"]
            rsem_file_name = rsem_data["content"][0]["fileName"]

            star_data = json.loads(star_json)
            print(str(star_data))
            star_bundle_uuid = star_data["content"][0]["gnosId"]
            star_file_uuid = star_data["content"][0]["id"]
            star_file_name = star_data["content"][0]["fileName"]

            for specimen in hit["_source"]["specimen"]:
               print("Next sample of %d samples:" % len(specimen["samples"]))
               for sample in specimen["samples"]:
                   print("Next analysis of %d analysis:" % len(sample["analysis"]))
                   #if a particular sample uuid is requested for processing and
                   #the current sample uuid does not match go on to the next sample
                   if self.process_sample_uuid and (self.process_sample_uuid != sample["sample_uuid"]):
			continue

                   for analysis in sample["analysis"]:
                        print("\nMetadata:submitter specimen id:" + specimen["submitter_specimen_id"]
                                    +" submitter sample id:" + sample["submitter_sample_id"] +" sample uuid:" 
                                    + sample["sample_uuid"] + " analysis type:" + analysis["analysis_type"]) 
                        print("normal RNA Seq quant:" + str(hit["_source"]["flags"]["normal_rna_seq_quantification"])
                                    +" tumor RNA Seq quant:" + str(hit["_source"]["flags"]["tumor_rna_seq_quantification"]))
                        print("Specimen type:" + specimen["submitter_specimen_type"] + " Experimental design:"
                                    + str(specimen["submitter_experimental_design"] + " Analysis bundle uuid:"+analysis["bundle_uuid"]))
                        print("Normal RNASeq 3.0.x flag:" + str(hit["_source"]["flags"]["normal_rna_seq_cgl_workflow_3_0_x"])
                                    +" Tumor RNASeq 3.0.x flag:" + str(hit["_source"]["flags"]["tumor_rna_seq_cgl_workflow_3_0_x"]))
                        print("Normal missing items RNASeq 3.0.x:" + str(sample["sample_uuid"] in hit["_source"]["missing_items"]["normal_rna_seq_cgl_workflow_3_0_x"]))
                        print("Tumor missing items RNASeq 3.0.x:" + str(sample["sample_uuid"] in hit["_source"]["missing_items"]["tumor_rna_seq_cgl_workflow_3_0_x"]))
                        print("work flow outputs:")
                        for output in analysis["workflow_outputs"]:
                            print(output)
 
                        #find out if there were result files from the last RNA Seq pipeline
                        #run on this sample 
                        rna_seq_outputs_len = 0
                        for filter_analysis in sample["analysis"]:
                                if filter_analysis["analysis_type"] == "rna_seq_quantification":
                                    rna_seq_outputs = filter_analysis["workflow_outputs"] 
                                    print("rna seq workflow outputs:")
                                    print(rna_seq_outputs)
                                    rna_seq_outputs_len = len(filter_analysis["workflow_outputs"])
                                    rna_seq_workflow_version = filter_analysis["workflow_version"] 
                                    print("len of rna_seq outputs is:"+str(rna_seq_outputs_len))

                        if ( (analysis["analysis_type"] == "sequence_upload" and 
                              ((hit["_source"]["flags"]["normal_rna_seq_cgl_workflow_3_0_x"] == False and 
                                   (rna_seq_outputs_len == 0 or (rna_seq_workflow_version != self.workflow_version)) and 
                                   sample["sample_uuid"] in hit["_source"]["missing_items"]["normal_rna_seq_cgl_workflow_3_0_x"] and 
                                   re.match("^Normal - ", specimen["submitter_specimen_type"]) and 
                                   re.match("^RNA-Seq$", specimen["submitter_experimental_design"])) or 
                               (hit["_source"]["flags"]["tumor_rna_seq_cgl_workflow_3_0_x"] == False and 
                                   (rna_seq_outputs_len == 0 or rna_seq_workflow_version != self.workflow_version) and 
                                   sample["sample_uuid"] in hit["_source"]["missing_items"]["tumor_rna_seq_cgl_workflow_3_0_x"] and 
                                   re.match("^Primary tumour - |^Recurrent tumour - |^Metastatic tumour - |^Cell line -", specimen["submitter_specimen_type"]) and 
                                   re.match("^RNA-Seq$", specimen["submitter_experimental_design"])))) or 

                             #if the workload has already been run but we have no
                             #output from the workload run it again
                             (analysis["analysis_type"] == "sequence_upload" and \
                              ((hit["_source"]["flags"]["normal_rna_seq_cgl_workflow_3_0_x"] == True and \
                                   (sample["sample_uuid"] in hit["_source"]["missing_items"]["normal_rna_seq_cgl_workflow_3_0_x"] or \
                                   (sample["sample_uuid"] in hit["_source"]["present_items"]["normal_rna_seq_cgl_workflow_3_0_x"] and 
                                                                                         (rna_seq_outputs_len == 0 or rna_seq_workflow_version != self.workflow_version))) and \
                                   re.match("^Normal - ", specimen["submitter_specimen_type"]) and \
                                   re.match("^RNA-Seq$", specimen["submitter_experimental_design"])) or \
                               (hit["_source"]["flags"]["tumor_rna_seq_cgl_workflow_3_0_x"] == True and \
                                   (sample["sample_uuid"] in hit["_source"]["missing_items"]["tumor_rna_seq_cgl_workflow_3_0_x"] or \
                                   (sample["sample_uuid"] in hit["_source"]["present_items"]["tumor_rna_seq_cgl_workflow_3_0_x"] and 
                                                                                         (rna_seq_outputs_len == 0 or rna_seq_workflow_version != self.workflow_version))) and \
                                   re.match("^Primary tumour - |^Recurrent tumour - |^Metastatic tumour - |^Cell line -", specimen["submitter_specimen_type"]) and \
                                   re.match("^RNA-Seq$", specimen["submitter_experimental_design"])))) ):


                            workflow_version_dir = self.workflow_version.replace('.', '_') 
                            touch_file_path_prefix = self.touch_file_bucket+"/consonance-jobs/RNASeq_Coordinator/" + workflow_version_dir
                            touch_file_path = touch_file_path_prefix+"/"+hit["_source"]["center_name"]+"_"+hit["_source"]["program"] \
                                                                    +"_"+hit["_source"]["project"]+"_"+hit["_source"]["submitter_donor_id"] \
                                                                    +"_"+specimen["submitter_specimen_id"]
                            #should we remove all white space from the path in the case where i.e. the program name is two works separated by blanks?
                            # remove all whitespace from touch file path
                            #touch_file_path = ''.join(touch_file_path.split())

                            submitter_sample_id = sample["submitter_sample_id"]

                            #This metadata will be passed to the Consonance Task and some
                            #some of the meta data will be used in the Luigi status page for the job
                            meta_data = {}
                            meta_data["program"] = hit["_source"]["program"]
                            meta_data["project"] = hit["_source"]["project"]
                            meta_data["center_name"] = hit["_source"]["center_name"]
                            meta_data["submitter_donor_id"] = hit["_source"]["submitter_donor_id"]
                            meta_data["donor_uuid"] = hit["_source"]["donor_uuid"]
                            if "submitter_donor_primary_site" in hit["_source"]:
                                meta_data["submitter_donor_primary_site"] = hit["_source"]["submitter_donor_primary_site"]
                            else:
                                meta_data["submitter_donor_primary_site"] = "not provided"
                            meta_data["submitter_specimen_id"] = specimen["submitter_specimen_id"]
                            meta_data["specimen_uuid"] = specimen["specimen_uuid"]
                            meta_data["submitter_specimen_type"] = specimen["submitter_specimen_type"]
                            meta_data["submitter_experimental_design"] = specimen["submitter_experimental_design"]
                            meta_data["submitter_sample_id"] = sample["submitter_sample_id"]
                            meta_data["sample_uuid"] = sample["sample_uuid"]
                            meta_data["analysis_type"] = "rna_seq_quantification"
                            meta_data["workflow_name"] = "quay.io/ucsc_cgl/rnaseq-cgl-pipeline"
                            meta_data["workflow_version"] = self.workflow_version

                            meta_data_json = json.dumps(meta_data)
                            print("meta data:")
                            print(meta_data_json)


                            #print analysis
                            print("HIT!!!! " + analysis["analysis_type"] + " " + str(hit["_source"]["flags"]["normal_rna_seq_quantification"]) 
                                           + " " + str(hit["_source"]["flags"]["tumor_rna_seq_quantification"]) + " " 
                                           + specimen["submitter_specimen_type"]+" "+str(specimen["submitter_experimental_design"]))


                            paired_files = []
                            paired_file_uuids = []
                            paired_bundle_uuids = []

                            single_files = []
                            single_file_uuids = []
                            single_bundle_uuids = []

                            tar_files = []
                            tar_file_uuids = []
                            tar_bundle_uuids = []

                            parent_uuids = {}

                            for file in analysis["workflow_outputs"]:
                                print("file type:"+file["file_type"])
                                print("file name:"+file["file_path"])

                                if (file["file_type"] == "fastq" or
                                    file["file_type"] == "fastq.gz"):
                                        #if there is only one sequenc upload output then this must
                                        #be a single read sample
                                        if( len(analysis["workflow_outputs"]) == 1): 
                                            print("adding %s of file type %s to files list" % (file["file_path"], file["file_type"]))
                                            single_files.append(file["file_path"])
                                            single_file_uuids.append(self.fileToUUID(file["file_path"], analysis["bundle_uuid"]))
                                            single_bundle_uuids.append(analysis["bundle_uuid"])
                                            parent_uuids[sample["sample_uuid"]] = True
                                        #otherwise we must be dealing with paired reads
                                        else: 
                                            print("adding %s of file type %s to files list" % (file["file_path"], file["file_type"]))
                                            paired_files.append(file["file_path"])
                                            paired_file_uuids.append(self.fileToUUID(file["file_path"], analysis["bundle_uuid"]))
                                            paired_bundle_uuids.append(analysis["bundle_uuid"])
                                            parent_uuids[sample["sample_uuid"]] = True
                                elif (file["file_type"] == "fastq.tar"):
                                    print("adding %s of file type %s to files list" % (file["file_path"], file["file_type"]))
                                    tar_files.append(file["file_path"])
                                    tar_file_uuids.append(self.fileToUUID(file["file_path"], analysis["bundle_uuid"]))
                                    tar_bundle_uuids.append(analysis["bundle_uuid"])
                                    parent_uuids[sample["sample_uuid"]] = True

                            if len(listOfJobs) < int(self.max_jobs) and (len(paired_files) + len(tar_files) + len(single_files)) > 0:

                                 if len(tar_files) > 0 and (len(paired_files) > 0 or len(single_files) > 0):
                                     print(('\n\nWARNING: mix of tar files and fastq(.gz) files submitted for' 
                                                        ' input for one sample! This is probably an error!'), file=sys.stderr)
                                     print('WARNING: files were\n paired {}\n tar: {}\n single:{}'.format(', '.join(map(str, paired_files)),
                                                                                                          ', '.join(map(str, tar_files)),
                                                                                                          ', '.join(map(str, single_files))), file=sys.stderr)
                                     print('WARNING: sample uuid:{}'.format(parent_uuids.keys()[0]), file=sys.stderr)
                                     print('WARNING: Skipping this job!\n\n', file=sys.stderr)
                                     continue

                                 elif len(paired_files) > 0 and len(single_files) > 0:
                                     print('\n\nWARNING: mix of single and paired fastq(.gz) files submitted for'
                                                    ' input for one sample! This is probably an error!', file=sys.stderr)
                                     print('WARNING: files were\n paired {}\n single:{}'.format(', '.join(map(str, paired_files)),
                                                                                                ', '.join(map(str, single_files))), file=sys.stderr)
                                     print('WARNING: sample uuid:{}\n'.format(parent_uuids.keys()[0]), file=sys.stderr)
                                     print('WARNING: Skipping this job!\n\n', file=stderr)
                                     continue
 
                                 elif len(tar_files) > 1:
                                     print('\n\nWARNING: More than one tar file submitted for'
                                                    ' input for one sample! This is probably an error!', file=sys.stderr)
                                     print('WARNING: files were\n tar: %s'.format(', '.join(map(str, tar_files))), file=sys.stderr)
                                     print('WARNING: sample uuid:%s'.format(parent_uuids.keys()[0]), file=sys.stderr)
                                     print('WARNING: Skipping this job!\n\n', file=sys.stderr)
                                     continue 

                                 elif len(paired_files) % 2 != 0:
                                     print('\n\nWARNING: Odd number of paired files submitted for'
                                                    ' input for one sample! This is probably an error!', file=sys.stderr)
                                     print('WARNING: files were\n paired: %s'.format(', '.join(map(str, paired_files))), file=sys.stderr)
                                     print('WARNING: sample uuid:%s'.format(parent_uuids.keys()[0]), file=sys.stderr)
                                     print('WARNING: Skipping this job!\n\n', file=sys.stderr)
                                     continue 

                                 else:
                                    print("will run report for {} and {} and {}".format(', '.join(map(str, paired_files)), 
                                                                                        ', '.join(map(str, tar_files)), 
                                                                                        ', '.join(map(str, single_files))))
                                    print("total of {} files in this {} job; job {} of {}".format(str(len(paired_files) + (len(tar_files) + len(single_files))), 
                                                                                             hit["_source"]["program"], str(len(listOfJobs)+1), str(self.max_jobs)))
                                    listOfJobs.append(ConsonanceTask(redwood_host=self.redwood_host, redwood_token=self.redwood_token, \
                                         image_descriptor=self.image_descriptor, vm_region=self.vm_region, \
                                         dockstore_tool_running_dockstore_tool=self.dockstore_tool_running_dockstore_tool, \
                                         parent_uuids = parent_uuids.keys(), \

                                         rsem_file_name = rsem_file_name, rsem_bundle_uuid = rsem_bundle_uuid, rsem_file_uuid = rsem_file_uuid, \
                                         star_file_name = star_file_name, star_bundle_uuid = star_bundle_uuid, star_file_uuid = star_file_uuid, \
                                         kallisto_file_name = kallisto_file_name, kallisto_bundle_uuid = kallisto_bundle_uuid, kallisto_file_uuid = kallisto_file_uuid, \
                                         disable_cutadapt = disable_cutadapt, \
                                         single_filenames=single_files, single_file_uuids = single_file_uuids, single_bundle_uuids = single_bundle_uuids, \
                                         paired_filenames=paired_files, paired_file_uuids = paired_file_uuids, paired_bundle_uuids = paired_bundle_uuids, \
                                         tar_filenames=tar_files, tar_file_uuids = tar_file_uuids, tar_bundle_uuids = tar_bundle_uuids, \
                                         tmp_dir=self.tmp_dir, submitter_sample_id = submitter_sample_id, meta_data_json = meta_data_json, \
                                         touch_file_path = touch_file_path, workflow_version = self.workflow_version, test_mode = self.test_mode))

        print("total of {} jobs; max jobs allowed is {}\n\n".format(str(len(listOfJobs)), self.max_jobs))

        # these jobs are yielded to
        print("\n\n** COORDINATOR REQUIRES DONE!!! **")
        return listOfJobs

    def run(self):
        print("\n\n\n\n** COORDINATOR RUN **")
         # now make a final report
        f = self.output().open('w')
        # TODO: could print report on what was successful and what failed?  Also, provide enough details like donor ID etc
        print("batch is complete", file=f)
        f.close()
        print("\n\n\n\n** COORDINATOR RUN DONE **")

    def output(self):
        print("\n\n\n\n** COORDINATOR OUTPUT **")
        # the final report
        ts = time.time()
        ts_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')
        #return luigi.LocalTarget('%s/consonance-jobs/RNASeq_3_1_x_Coordinator/RNASeqTask-%s.txt' % (self.tmp_dir, ts_str))
        workflow_version_dir = self.workflow_version.replace('.', '_') 
        return S3Target('s3://'+self.touch_file_bucket+'/consonance-jobs/RNASeq_Coordinator/{}/RNASeqTask-{}.txt'.format(workflow_version_dir, ts_str))

    def fileToUUID(self, input, bundle_uuid):
        return self.bundle_uuid_filename_to_file_uuid[bundle_uuid+"_"+input]
        #"afb54dff-41ad-50e5-9c66-8671c53a278b"


if __name__ == '__main__':
    luigi.run()
