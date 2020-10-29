# coding: utf-8

import oci
import os
import time

def manage_bucket(config, signer, my_compartment_id, my_bucket, tenancy_id):

    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)

    my_namespace = storage.get_namespace(compartment_id=tenancy_id).data
    all_buckets = storage.list_buckets(my_namespace,my_compartment_id).data
    my_bucket_etag = ""

    for bucket in all_buckets:
        if bucket.name == my_bucket:    
            print("bucket found [{}]".format(bucket.name))
            my_bucket_etag = bucket.etag

    if len(my_bucket_etag) < 1:
        print("Bucket [{}] not found".format(my_bucket))
        print("Creating bucket [{}] ...".format(my_bucket))
        create_bucket_details = oci.object_storage.models.CreateBucketDetails(
            public_access_type = 'NoPublicAccess',
            storage_tier = 'Standard',
            versioning = 'Disabled',
            name = my_bucket,
            compartment_id = my_compartment_id
            )
        result = storage.create_bucket(my_namespace, create_bucket_details)
                
        time.sleep(10) # need time before getting the newly bucket ID
        result_response = storage.get_bucket(my_namespace, my_bucket)

        wait_until_bucket_available_response = oci.wait_until(storage,result_response,'etag',result_response.data.etag)
        print("Bucket has been created with ID: {}".format(wait_until_bucket_available_response.data.id))

    return

def updload_file(config, signer, my_bucket, local_file, tenancy_id):
    
    storage = oci.object_storage.ObjectStorageClient(config=config, signer=signer)
    
    namespace = storage.get_namespace(compartment_id=tenancy_id).data

    with open(local_file, "rb") as in_file:
        name = os.path.basename(local_file)
        result = storage.put_object(
            namespace,
            my_bucket,
            name,
            in_file)

    print("File has been successfully uploaded")

    return