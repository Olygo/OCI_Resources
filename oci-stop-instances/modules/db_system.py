import oci

resource_name = 'database systems'

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def stop_database_systems(config, signer, compartments, Use_Tag):
    target_resources = []

    print("Listing all {}... (* is marked for stop)".format(resource_name))
    for compartment in compartments:
        print("  compartment: {}".format(compartment.name))
        db_systems = _get_db_system_list(config, signer, compartment.id)
        for db_system in db_systems:
            go = 1
            if (db_system.lifecycle_state == 'AVAILABLE'):
                if Use_Tag == 'TRUE':
                    print ("\n===========================[ Tags Control Enabled ]=============================")

                    if ('CLOUD-STOP' in db_system.defined_tags) and ('STOP' in db_system.defined_tags['CLOUD-STOP']): 
                        if (db_system.defined_tags['CLOUD-STOP']['STOP'].upper() == 'FALSE'):
                            go = 0

            print("      {} ({}) in {}".format(db_system.display_name, db_system.lifecycle_state, compartment.name))
            if (go == 1):
                db_nodes = _get_db_node_list(config, signer, compartment.id, db_system.id)

                for db_node in db_nodes:
                    if (db_node.lifecycle_state == 'AVAILABLE'):
                        print(red("        * node:{} ({})".format(db_node.hostname, db_node.lifecycle_state)))
                        target_resources.append(db_node)
                    else:
                        print(green("          node:{} ({})".format(db_node.hostname, db_node.lifecycle_state)))

    print('\nStopping * marked {}...'.format(resource_name))
    for resource in target_resources:
        try:
            response = _db_node_action(config, signer, resource.id, 'STOP')

        except oci.exceptions.ServiceError as e:
            print("---------> error. status: {}".format(e))
            pass
        else:
            if response.lifecycle_state == 'STOPPING':
                print(red("    stop requested: {} ({})".format(response.db_system_id, response.lifecycle_state)))
            else:
                print("---------> error stopping {} ({})".format(response.hostname, response.lifecycle_state))

    print("\nAll {} stopped!".format(resource_name))


def _get_db_system_list(config, signer, compartment_id):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    resources = oci.pagination.list_call_get_all_results(
        object.list_db_systems,
        compartment_id=compartment_id
    )
    return resources.data

def _get_db_node_list(config, signer, compartment_id, db_system_id):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    resources = oci.pagination.list_call_get_all_results(
        object.list_db_nodes,
        compartment_id = compartment_id,
        db_system_id = db_system_id
    )
    return resources.data

def _db_node_action(config, signer, resource_id, action):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    response = object.db_node_action(
        resource_id,
        action
    )
    return response.data
