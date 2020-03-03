import oci
import csv

Excluded_States = ['TERMINATED', 'TERMINATING']

def get_instance_pools(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.ComputeManagementClient(config={}, signer=signer)
    else:
        object = oci.core.ComputeManagementClient(config=config)

    print ("\n==========================={ Getting all Instance Pools }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_instance_pools, compartment_id=compartment.id).data
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
                            object.terminate_instance_pool(instance_pool_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Instance Pool: {}".format(item.display_name))
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
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Instance_Pools', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_instance_configurations(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.ComputeManagementClient(config={}, signer=signer)
    else:
        object = oci.core.ComputeManagementClient(config=config)

    print ("\n==========================={ Getting all Instance Configurations }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_instance_configurations, compartment_id=compartment.id).data
        for item in items:
            AllItems.append(item)
            if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                print ("Owner Tag OK for: {}".format(item.display_name))
            else:
                print ("Owner Tag Missing for: {}".format(item.display_name))
                try:
                    if cleanup == "YES":
                        print("Deleting: {}".format(item.display_name))
                        object.delete_instance_configuration(instance_configuration_id=item.id)
                    else:
                        print("Logging in report: {}".format(item.display_name))
                except oci.exceptions.ServiceError as e:
                    print("error deleting Instance Conf: {}".format(item.display_name))
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
                        writer.writerow({'Profile': tenant_name, 'Service_Type': 'Instance_Configurations', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_compute_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=signer)
    else:
        object = oci.core.ComputeClient(config=config)

    print ("\n==========================={ Getting all Compute Instances }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_instances, compartment_id=compartment.id).data
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
                            object.terminate_instance(instance_id=item.id)

                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting instance: {}".format(item.display_name))
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
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Compute_Instances', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_dedicated_vm_hosts(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=signer)
    else:
        object = oci.core.ComputeClient(config=config)

    print ("\n==========================={ Getting all Dedicated VM Hosts }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_dedicated_vm_hosts, compartment_id=compartment.id).data
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
                            object.delete_dedicated_vm_host(dedicated_vm_host_id=item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Dedicated VM Host: {}".format(item.display_name))
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
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Dedicated_VM_Hosts', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()