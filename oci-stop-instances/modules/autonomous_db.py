import oci

resource_name = 'autonomous databases'

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def stop_autonomous_dbs(config, signer, compartments, use_tag, tag_value, tag_key, tag_namespace):
    target_resources = []

    print("\nListing all {}... (* is marked for stop)".format(resource_name))
    for compartment in compartments:
        # print("  compartment: {}".format(compartment.name))
        resources = _get_resource_list(config, signer, compartment.id)
        for resource in resources:
            go = 1
            if (resource.lifecycle_state == 'AVAILABLE'):
                if use_tag == 'TRUE':
                    print ("\n===========================[ Tags Control Enabled ]=============================")

                    if (tag_namespace in resource.defined_tags) and (tag_key in resource.defined_tags[tag_namespace]): 
                        if (resource.defined_tags[tag_namespace][tag_key].upper() == tag_value):
                            go = 0

            if (go == 1):
                if (resource.lifecycle_state != 'TERMINATED'):
                    print(red("    * {} ({}) in {}".format(resource.display_name, resource.lifecycle_state, compartment.name)))
                    target_resources.append(resource)
            else:
                print(green("      {} ({}) in {}".format(resource.display_name, resource.lifecycle_state, compartment.name)))

    print('\nStopping * marked {}...'.format(resource_name))
    for resource in target_resources:
        try:
            response = _resource_action(config, signer, resource.id)
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
    object = oci.database.DatabaseClient(config=config, signer=signer)
    resources = oci.pagination.list_call_get_all_results(
        object.list_autonomous_databases,
        compartment_id=compartment_id
    )
    return resources.data


def _resource_action(config, signer, resource_id):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    response = object.stop_autonomous_database(
        resource_id
    )
    return response.data
