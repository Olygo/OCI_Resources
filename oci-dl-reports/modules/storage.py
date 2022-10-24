# coding: utf-8

import oci
import os
import time
import shutil

# set colors
yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def path_expander(path):
    path = os.path.expanduser(path)
    
    return path

def check_folder(folder, **output):
    if not os.path.exists(folder):
        if output:
            print(yellow(f"creating folder: {folder}"))
        os.mkdir(folder)
    else:
        if output:
            print(green(f"folder found: {folder}"))

def check_bucket(config, signer, target_comp_id, target_bucket, tenancy_id, oci_tname):

    if target_bucket == 'default':
        target_bucket = 'reports_' + oci_tname

    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)

    my_namespace = storage.get_namespace(compartment_id=tenancy_id).data
    all_buckets = storage.list_buckets(my_namespace,target_comp_id).data
    target_bucket_etag = ""

    for bucket in all_buckets:
        if bucket.name == target_bucket:    
            print(green(f"Bucket found [{bucket.name}]"))
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
        result_response = storage.get_bucket(my_namespace, target_bucket)

        wait_until_bucket_available_response = oci.wait_until(storage,result_response,'etag',result_response.data.etag)
        print(green(f"Bucket has been created with ID: {wait_until_bucket_available_response.data.id}"))

    return target_bucket

def updload_file(config, signer, target_bucket, file2upload, tenancy_id, day_created, month_created, year_created, tree_reports, tmp_folder):
    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    namespace = storage.get_namespace(compartment_id=tenancy_id).data

    if str.upper(tree_reports) == 'TRUE':
        tag =  year_created + "/" + month_created + "/" + day_created + "/"
    else:
        tag = ''

    # upload to oci
    with open(file2upload, "rb") as in_file:
        filename = os.path.basename(file2upload)
        upload_response = storage.put_object(
            namespace,
            target_bucket,
            tag+filename,
            in_file)

    # list objects in bucket and check md5 of uploaded file
    object_list = storage.list_objects(namespace, target_bucket, fields=['md5'])

    for item in object_list.data.objects:
        if item.md5 == upload_response.headers['opc-content-md5']:
            print(green(f"File successfully uploaded: {item.name, item.md5}"))

    #purge .tmp folder before next file
    for file in os.listdir(tmp_folder):
        os.remove(os.path.join(tmp_folder, file))

    return

def move_file(file2upload, day_created, month_created, year_created, tree_reports, working_folder, tmp_folder, file):
 
    if str.upper(tree_reports) == 'TRUE':
        tag =  year_created + "/" + month_created + "/" + day_created + "/"
    else:
        tag = ''

    if str.upper(tree_reports) == 'TRUE':
        # move report to working folder using tree
        year_folder = os.path.join(working_folder, year_created)
        check_folder(year_folder)
        month_folder = os.path.join(year_folder, month_created)
        check_folder(month_folder)
        day_folder = os.path.join(month_folder, day_created)
        check_folder(day_folder)
        filename = os.path.basename(day_folder)
        source = file2upload
        destination = day_folder
        filename = os.path.basename(source)
        dest = os.path.join(destination,filename)
        shutil.move(source, dest)

    else:
        # move report to root working folder
        localfolder = os.path.join(working_folder, file)
        shutil.move(file2upload, localfolder)     

    #purge .tmp folder before next file
    for file in os.listdir(tmp_folder):
        os.remove(os.path.join(tmp_folder, file))

    return

def get_bucket_info(config, signer, target_bucket, tenancy_id):
    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    namespace = storage.get_namespace(compartment_id=tenancy_id).data 
    report_bucket_size = storage.get_bucket(namespace,target_bucket,fields=['approximateCount','approximateSize'])
    bucketfiles = report_bucket_size.data.approximate_count
    bucketsize = report_bucket_size.data.approximate_size/(1024*1024*1024)
    time.sleep(10)   

    return [bucketfiles, bucketsize]