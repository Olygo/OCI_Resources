# coding: utf-8

import oci
import time
import csv

yellow = lambda text: '\033[0;33m' + text + '\033[0m'

Excluded_States = ['TERMINATED', 'TERMINATING', 'DELETING', 'DELETED']

def get_bucket_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.object_storage.ObjectStorageClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.object_storage.ObjectStorageClient(config=Auth["Config"])
    
    ns = object.get_namespace().data
    
    print ("\n==={ Collecting Bucket Tags }===")
    for compartment in Conf["Compartments"]:
        AllBuckets = []
        item_bucket = object.list_buckets(namespace_name=ns, compartment_id=compartment.id).data
        AllBuckets.append(item_bucket)
        for buckets in AllBuckets:
            for bucket in buckets:
                item = object.get_bucket(namespace_name=ns, bucket_name=bucket.name, fields=['approximateCount']).data
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_boot_volumes_tags(Auth, Conf, Data):
    AllItems = []

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=Auth["Signer"])
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.BlockstorageClient(config=Auth["Config"])
        identity = oci.identity.IdentityClient(config=Auth["Config"])

    print ("\n==={ Collecting Boot Volume Tags }===")
    for compartment in Conf["Compartments"]:
        ADs = identity.list_availability_domains(compartment_id=compartment.id).data
        for AD in ADs:
            items = oci.pagination.list_call_get_all_results(object.list_boot_volumes, availability_domain=AD.name, compartment_id=compartment.id).data
            for item in items:
                if (item.lifecycle_state not in Excluded_States):
                    AllItems.append(item)
                    if Data["MyTagNamespace"] in item.defined_tags:
                        MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                        MyTag = MyTags.get(Data["MyTagKey"])
                        if MyTag not in Data["OwnerTags"]:
                            Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_boot_volume_backups_tags(Auth, Conf, Data):
    AllItems = []

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.BlockstorageClient(config=Auth["Config"])

    print ("\n==={ Collecting Boot Volume Backup Tags }===")
    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_boot_volume_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)
        
    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_block_volumes_tags(Auth, Conf, Data):
    AllItems = []

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.BlockstorageClient(config=Auth["Config"])

    print ("\n==={ Collecting Block Volumes Tags }===")
    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_volumes, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]                   

def get_block_volume_backups_tags(Auth, Conf, Data):
    AllItems = []

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.BlockstorageClient(config=Auth["Config"])

    print ("\n==={ Collecting Block Volume Backup Tags }===")
    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_volume_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_custom_images_tags(Auth, Conf, Data):
    AllItems = []

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.ComputeClient(config=Auth["Config"])

    print ("\n==={ Collecting Custom Image Tags }===")

    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_images, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                if item.operating_system_version == "Custom" or item.base_image_id: 
                    if item.display_name != "Windows-Server-2008-R2-Enterprise-Edition-VM-2019.06.17-0":
                        AllItems.append(item)
                        if Data["MyTagNamespace"] in item.defined_tags:
                            MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                            MyTag = MyTags.get(Data["MyTagKey"])
                            if MyTag not in Data["OwnerTags"]:
                                Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]