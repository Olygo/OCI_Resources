# coding: utf-8

import oci
import os
from pathlib import Path
import shutil
import sys, shutil, gzip

# set colors
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def path_expander(path):
    path = os.path.expanduser(path)
    
    return path

def check_folder(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

def check_bucket(config, signer, target_comp_id, target_bucket, tenancy_id):
    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)

    my_namespace = storage.get_namespace(compartment_id=tenancy_id).data
    all_buckets = storage.list_buckets(my_namespace,target_comp_id).data
    target_bucket_etag = ""

    for bucket in all_buckets:
        if bucket.name == target_bucket:    
            print(yellow(f"Bucket found [{bucket.name}]"))
            target_bucket_etag = bucket.etag

    if len(target_bucket_etag) < 1:
        print(yellow(f"Bucket [{target_bucket}] not found"))
        print(yellow(f"Creating bucket [{target_bucket}] ..."))
        create_bucket_details = oci.object_storage.models.CreateBucketDetails(
            public_access_type = 'NoPublicAccess',
            storage_tier = 'Standard',
            versioning = 'Disabled',
            name = target_bucket,
            compartment_id = target_comp_id
            )
        result = storage.create_bucket(my_namespace, create_bucket_details)
                
        #time.sleep(10) # need time before getting the newly bucket ID
        result_response = storage.get_bucket(my_namespace, target_bucket)

        wait_until_bucket_available_response = oci.wait_until(storage,result_response,'etag',result_response.data.etag)
        print(green(f"Bucket has been created with ID: {wait_until_bucket_available_response.data.id}"))

    return

def updload_file(config, signer, target_bucket, monthly_report, tenancy_id, working_folder):
    
    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    namespace = storage.get_namespace(compartment_id=tenancy_id).data


    archive_report = monthly_report
    filename_out = monthly_report + '.tar.gz'

    with open(archive_report, "rb") as fin, gzip.open(filename_out, "wb") as fout:
        # Reads the file by chunks to avoid exhausting memory
        shutil.copyfileobj(fin, fout)
    
    print(green("\n====> Uploading file to oci"))

    # get archive size in GB
    print(f"Report Archive: {filename_out}")
    archive_size = os.path.getsize(filename_out) / (1024*1024*1024)
    print(f"Archive size: {archive_size:.2f} GB")

    # upload to oci
    with open(filename_out, "rb") as in_file:
        filename = os.path.basename(filename_out)
        upload_response = storage.put_object(
            namespace,
            target_bucket,
            filename,
            in_file)

    #print(f"upload_response ==>> \n {upload_response.headers}")
    #print(f"\n{upload_response.headers['opc-content-md5']}")

    # list objects in bucket
    object_list = storage.list_objects(namespace, target_bucket, fields=['md5'])

    for item in object_list.data.objects:
        if item.md5 == upload_response.headers['opc-content-md5']:
            print(f"File successfully uploaded: {item.name, item.md5}")

    # clean local folder
    #shutil.rmtree(working_folder)
