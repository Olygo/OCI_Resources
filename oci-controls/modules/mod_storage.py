import oci
import time
import csv

Excluded_States = ['TERMINATED', 'TERMINATING', 'DELETING', 'DELETED']

def get_buckets(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllBuckets = []

    if use_instance_principal == 'TRUE':
        object = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    else:
        object = oci.object_storage.ObjectStorageClient(config=config)

    ns = object.get_namespace().data

    print ("\n==========================[ Getting all Buckets for {} ]===========================".format(ns))
    for compartment in compartments:
        item_bucket = object.list_buckets(namespace_name=ns, compartment_id=compartment.id).data
        if len(item_bucket) > 0:
            AllBuckets.append(item_bucket)
            #print(AllBuckets)
            for buckets in AllBuckets:
                for bucket in buckets:
                    #print(bucket.name)
                    bucket_item = object.get_bucket(namespace_name=ns, bucket_name=bucket.name, fields=['approximateCount']).data
                    if (('System_Tags' in bucket_item.defined_tags) or ('Mandatory_Tags' in bucket_item.defined_tags) and ('Owner' in bucket_item.defined_tags['Mandatory_Tags'])): 
                        print ("Owner Tag OK for: {}".format(bucket_item.name))
                    else:
                        print ("Owner Tag Missing for: {}".format(bucket_item.name))

                        print ("\n==========================={ Getting all Multipart_Uploads }=============================")
                        result = object.list_multipart_uploads(namespace_name=ns, bucket_name=bucket.name)
                        items = result.data
                        for item in items:
                            try:
                                if cleanup == "YES":
                                    print ("Deleting Multiparts {}:{}".format(item.object, item.upload_id))
                                    object.abort_multipart_upload(namespace_name=ns, bucket_name=bucket.name, object_name=item.object, upload_id=item.upload_id)
                                else:
                                    print("Logging in report: {}".format(item.object))
                            except oci.exceptions.ServiceError as e:
                                print("error deleting Multipart: {}".format(item.object))
                                print("---------> error. status: {}".format(e))
                                err.write(now) 
                                err.write("\n")
                                err.write("---------> error. status: {}".format(e))
                                err.write("\n")
                                pass
                            finally:
                                with open(tags_report, mode='a', newline='') as csvfile:
                                    fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                    writer.writerow({'Profile': tenant_name, 'Service_Type': "Multipart_Upload", 'Service_Name': item.object, 'Compartment': compartment.name, 'Region': region})

                        print ("\n==========================={ Getting all Preauthenticated_Requests }=============================")
                        result = object.list_preauthenticated_requests(namespace_name=ns, bucket_name=bucket.name)
                        items = result.data
                        for item in items:
                            try:
                                if cleanup == "YES":
                                    print ("Deleting PAR {}:{}".format(bucket.name, item.name))
                                    object.delete_preauthenticated_request(namespace_name=ns, bucket_name=bucket.name, par_id=item.id)
                                else:
                                    print("Logging in report: {}".format(bucket.name))
                            except oci.exceptions.ServiceError as e:
                                print("error deleting PAR: {}".format(bucket.name))
                                print("---------> error. status: {}".format(e))
                                err.write(now) 
                                err.write("\n")
                                err.write("---------> error. status: {}".format(e))
                                err.write("\n")                                
                                pass
                            finally:
                                with open(tags_report, mode='a', newline='') as csvfile:
                                    fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                    writer.writerow({'Profile': tenant_name, 'Service_Type': "Preauthenticated_request", 'Service_Name': item.name, 'Compartment': compartment.name, 'Region': region})

                        if bucket_item.approximate_count > 0:
                            print ("\n==========================={ Getting all Objects }=============================")
                            obj = object.list_objects(namespace_name=ns, bucket_name=bucket.name, fields=['name'])
                            items = obj.data.objects
                            for item in items:
                                try:
                                    if cleanup == "YES":
                                        print ("Delete Object: {}".format(item.name))
                                        object.delete_object(namespace_name=ns, bucket_name=bucket.name, object_name=item.name)
                                    else:
                                        print("Logging in report: {}".format(item.name))
                                except oci.exceptions.ServiceError as e:
                                    print("error deleting object: {}".format(item.name))
                                    print("---------> error. status: {}".format(e))
                                    err.write(now) 
                                    err.write("\n")
                                    err.write("---------> error. status: {}".format(e))
                                    err.write("\n")                                    
                                    pass
                                finally:
                                    with open(tags_report, mode='a', newline='') as csvfile:
                                        fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                        writer.writerow({'Profile': tenant_name, 'Service_Type': "Object", 'Service_Name': item.name, 'Compartment': compartment.name, 'Region': region})

                        try:
                            if cleanup == "YES":
                                print ("Delete Bucket: {}".format(bucket.name))
                                object.delete_bucket(namespace_name=ns,bucket_name=bucket.name)
                            else:
                                print("Logging in report: {}".format(bucket.name))                               
                        except oci.exceptions.ServiceError as e:
                            print("error deleting Bucket: {}".format(bucket.name))
                            print("---------> error. status: {}".format(e))
                            err.write(now) 
                            err.write("\n")
                            err.write("---------> error. status: {}".format(e))
                            err.write("\n")                            
                            pass
                        finally:
                            with open(tags_report, mode='a', newline='') as csvfile:
                                fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow({'Profile': tenant_name, 'Service_Type': "Object Storage Bucket", 'Service_Name': bucket.name, 'Compartment': compartment.name, 'Region': region})
                        if item_bucket in AllBuckets:
                            AllBuckets.remove(item_bucket)
    err.close()

def get_boot_volumes(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
        identity = oci.identity.IdentityClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)
        identity = oci.identity.IdentityClient(config=config)

    print ("\n==========================={ Getting all Boot Volumes }=============================")
    for compartment in compartments:
        ADs = identity.list_availability_domains(compartment_id=compartment.id).data
        for AD in ADs:
            items = oci.pagination.list_call_get_all_results(object.list_boot_volumes, availability_domain=AD.name, compartment_id=compartment.id).data
            for item in items:
                if (item.lifecycle_state not in Excluded_States):
                    AllItems.append(item)
                    if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                        print ("Owner Tag OK for: {}".format(item.display_name))
                    else:
                        print ("Owner Tag Missing for: {}".format(item.display_name))
                        try:
                            if cleanup == "YES":
                                print("Deleting: {}".format(item.display_name))
                                object.delete_boot_volume(boot_volume_id=item.id)
                            else:
                                print("Logging in report: {}".format(item.display_name))
                        except oci.exceptions.ServiceError as e:
                            print("error deleting Boot Volume: {}".format(item.display_name))
                            print("---------> error. status: {}".format(e))
                            err.write(now) 
                            err.write("\n")
                            err.write("---------> error. status: {}".format(e))
                            err.write("\n")                            
                            pass
                        finally:
                            with open(tags_report, mode='a', newline='') as csvfile:
                                fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writerow({'Profile': tenant_name, 'Service_Type': 'Boot_volume', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_boot_volume_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)

    print ("\n==========================={ Getting all Boot Volume Backups }=============================")    
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_boot_volume_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.delete_boot_volume_backup(boot_volume_backup_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Boot Volume Backup: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")                        
                        pass
                    finally:
                        with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Boot_volume_backups', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
                    time.sleep(5)
    err.close()

def get_block_volumes(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)

    print ("\n==========================={ Getting all Block Volumes }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_volumes, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.delete_volume(volume_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Block Volume: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")
                        pass
                    finally:
                        with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Block_volumes', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()                            

def get_block_volume_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)

    print ("\n==========================={ Getting all Block Volume Backups }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_volume_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.delete_volume_backup(volume_backup_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Block Volume Backup: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")
                        pass
                    finally:
                        with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Block_volume_backups', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
                    time.sleep(5)
    err.close()

def get_custom_images(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=signer)
    else:
        object = oci.core.ComputeClient(config=config)

    print ("\n==========================={ Getting all Custom Images }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_images, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                if item.operating_system_version == "Custom" or item.base_image_id: 
                    if item.display_name != "Windows-Server-2008-R2-Enterprise-Edition-VM-2019.06.17-0":
                        AllItems.append(item)
                        if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                            print ("Owner Tag OK for: {}".format(item.display_name))
                        else:
                            print ("Owner Tag Missing for: {}".format(item.display_name))
                            try:
                                if cleanup == "YES":
                                    print("Deleting: {}".format(item.display_name))
                                    object.delete_image(image_id=item.id)
                                else:
                                    print("Logging in report: {}".format(item.display_name))
                            except oci.exceptions.ServiceError as e:
                                print("error deleting Image: {}".format(item.display_name))
                                print("---------> error. status: {}".format(e))
                                err.write(now) 
                                err.write("\n")
                                err.write("---------> error. status: {}".format(e))
                                err.write("\n")
                                pass
                            finally:
                                with open(tags_report, mode='a', newline='') as csvfile:
                                    fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                    writer.writerow({'Profile': tenant_name, 'Service_Type': 'Custom_images', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_volume_groups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)

    print ("\n==========================={ Getting all Volume Groups }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_volume_groups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.delete_volume_group(volume_group_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Volume Group: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")                        
                        pass
                    finally:
                         with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Volume_Groups', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_volume_group_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.BlockstorageClient(config={}, signer=signer)
    else:
        object = oci.core.BlockstorageClient(config=config)

    print ("\n==========================={ Getting all Volume Group Backups }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_volume_group_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.delete_volume_group_backup(volume_group_backup_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Volume Group Backup: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")                        
                        pass
                    finally:
                        with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Volume_Group_Backups', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()