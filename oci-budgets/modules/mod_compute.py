# coding: utf-8

import oci
import csv

yellow = lambda text: '\033[0;33m' + text + '\033[0m'

Excluded_States = ['TERMINATED', 'TERMINATING']

def get_compute_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.ComputeClient(config=Auth["Config"])
    
    print ("\n==={ Collecting Compute Tags }===")
    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_instances, compartment_id=compartment.id).data
        for item in items:
            if Data["MyTagNamespace"] in item.defined_tags:
                MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                MyTag = MyTags.get(Data["MyTagKey"])
                if MyTag not in Data["OwnerTags"]:
                    Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_instance_pools_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.ComputeManagementClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.ComputeManagementClient(config=Auth["Config"])
    
    print ("\n==={ Collecting Intance Pool Tags }===")
    for compartment in Conf["Compartments"]:
        try:
            items = oci.pagination.list_call_get_all_results(object.list_instance_pools, compartment_id=compartment.id).data
            for item in items:
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)
        except oci.exceptions.ServiceError as e:
            #print("---------> error. status: {}".format(e))
            pass

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_instance_configurations_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.ComputeManagementClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.ComputeManagementClient(config=Auth["Config"])
    
    print ("\n==={ Collecting Intance Conf Tags }===")
    for compartment in Conf["Compartments"]:
        try:
            items = oci.pagination.list_call_get_all_results(object.list_instance_configurations, compartment_id=compartment.id).data
            for item in items:
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)
        except oci.exceptions.ServiceError as e:
            #print("---------> error. status: {}".format(e))
            pass

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

def get_dedicated_vm_hosts_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.core.ComputeClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.core.ComputeClient(config=Auth["Config"])
    
    print ("\n==={ Collecting Dedicated VM Host Tags }===")
    for compartment in Conf["Compartments"]:
        try:
            items = oci.pagination.list_call_get_all_results(object.list_dedicated_vm_hosts, compartment_id=compartment.id).data
            for item in items:
                if Data["MyTagNamespace"] in item.defined_tags:
                    MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                    MyTag = MyTags.get(Data["MyTagKey"])
                    if MyTag not in Data["OwnerTags"]:
                        Data["OwnerTags"].append(MyTag)
        except oci.exceptions.ServiceError as e:
            #print("---------> error. status: {}".format(e))
            pass
        
    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]
