import oci

resource_name = 'compute instances'

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def stop_compute_instances(config, signer, compartments, Use_Tag):
    target_resources = []

    print("Listing all {}... (* is marked for stop)".format(resource_name))
    for compartment in compartments:
        print("  compartment: {}".format(compartment.name))
        resources = _get_resource_list(config, signer, compartment.id)
        for resource in resources:
            go = 1
            if (resource.lifecycle_state == 'RUNNING'):
                if Use_Tag == 'TRUE':
                    print ("\n===========================[ Tags Control Enabled ]=============================")

                    if ('CLOUD-STOP' in resource.defined_tags) and ('STOP' in resource.defined_tags['CLOUD-STOP']): 
                        if (resource.defined_tags['CLOUD-STOP']['STOP'].upper() == 'FALSE'):
                            go = 0
                    else:
                        go = 1

            if (go == 1):
                print(red("    * {} ({}) in {}".format(resource.display_name, resource.lifecycle_state, compartment.name)))
               
                target_resources.append(resource)
            else:
                print(green("      {} ({}) in {}".format(resource.display_name, resource.lifecycle_state, compartment.name)))

    print('\nStopping * marked {}...'.format(resource_name))
    for resource in target_resources:
        try:
            response = _resource_action(config, signer, resource.id, 'STOP')
        except oci.exceptions.ServiceError as e:
            print("---------> error. status: {}".format(e))
            pass
        else:
            if response.lifecycle_state == 'STOPPING':
                print("    stop requested: {} ({})".format(response.display_name, response.lifecycle_state))
            else:
                print("---------> error stopping {} ({})".format(response.display_name, response.lifecycle_state))

    print("\nAll {} stopped!".format(resource_name))


def _get_resource_list(config, signer, compartment_id):
    object = oci.core.ComputeClient(config=config, signer=signer)
    resources = oci.pagination.list_call_get_all_results(
        object.list_instances,
        compartment_id
    )
    return resources.data

def _resource_action(config, signer, resource_id, action):
    object = oci.core.ComputeClient(config=config, signer=signer)
    response = object.instance_action(
        resource_id,
        action
    )
    return response.data
