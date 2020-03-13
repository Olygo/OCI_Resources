# coding: utf-8

import oci
import csv

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'

Excluded_States = ['TERMINATED', 'TERMINATING']

def get_autonomous_tags(Auth, Conf, Data):

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.database.DatabaseClient(config=Auth["Config"])
    
    print ("\n==={ Collecting all Autonomous Tags }===")
    for compartment in Conf["Compartments"]:
        items = oci.pagination.list_call_get_all_results(object.list_autonomous_databases, compartment_id=compartment.id).data
        for item in items:
            if Data["MyTagNamespace"] in item.defined_tags:
                MyTags = item.defined_tags.get(Data["MyTagNamespace"])
                MyTag = MyTags.get(Data["MyTagKey"])
                if MyTag not in Data["OwnerTags"]:
                    Data["OwnerTags"].append(MyTag)

    print(yellow("{} tags found: {}".format(Data["MyTagKey"],len(Data["OwnerTags"]))))
    return Data["OwnerTags"]

