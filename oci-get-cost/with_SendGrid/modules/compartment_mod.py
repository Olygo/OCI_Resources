# coding: utf-8

import oci
import time

def manage_compartment(config, signer, tenancy_id, my_compartment):

    identity = oci.identity.IdentityClient(config=config, signer=signer)
    
    all_compt = identity.list_compartments(tenancy_id).data
    my_compartment_id = ""
    for compartment in all_compt:
        if compartment.name == my_compartment:    
            print("Compartment found {}".format(compartment.id))
            my_compartment_id = compartment.id

    if len(my_compartment_id) < 1:
        print("Compartment {} not found".format(my_compartment))
        print("Creating compartment {} ...".format(my_compartment))
        result = identity.create_compartment(oci.identity.models.CreateCompartmentDetails(
            compartment_id = tenancy_id,
            description = "Store billing data",
            name = my_compartment))
        my_compartment_id = result.data.id

        time.sleep(15) # need time before getting the newly created compartment ID
        get_compartment_response = identity.get_compartment(my_compartment_id)
        wait_until_compartment_available_response = oci.wait_until(identity,get_compartment_response,'lifecycle_state','ACTIVE')
        print("Compartment has been created with ID: {}\n".format(wait_until_compartment_available_response.data.id))
    
    return my_compartment_id
