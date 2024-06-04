# coding: utf-8

import oci
import time

yellow = lambda text: '\033[0;33m' + text + '\033[0m'
red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def check_compartment(config, signer, tenancy_id, target_comp):

    identity = oci.identity.IdentityClient(config=config, signer=signer)
    all_compt = oci.pagination.list_call_get_all_results(identity.list_compartments, tenancy_id, compartment_id_in_subtree=True)
    target_comp_id = ""

    for compartment in all_compt.data:
        if compartment.name == target_comp:    
            print(yellow(f"Compartment found {compartment.id}"))
            target_comp_id = compartment.id

    if len(target_comp_id) < 1:
        print(yellow(f"Compartment {target_comp} not found"))
        print(yellow(f"Creating compartment {target_comp}, wait a minute ..."))
        result = identity.create_compartment(oci.identity.models.CreateCompartmentDetails(
            compartment_id = tenancy_id,
            description = "Monthly cost reports",
            name = target_comp))
        target_comp_id = result.data.id        
        time.sleep(60) # delay before getting the newly created compartment ID
        get_compartment_response = identity.get_compartment(target_comp_id)

        print(green(f"Compartment has been created: {target_comp_id}\n"))

    return target_comp_id