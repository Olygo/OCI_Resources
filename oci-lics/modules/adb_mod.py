import oci

resource_name = 'autonomous databases'

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'

def change_autonomous_db_license(config, signer, compartments):
    
        target_resources = []

        print("Listing all {}... (* is marked for change)".format(resource_name))

        for compartment in compartments:
            resources = _get_resource_list(config, signer, compartment.id)
            for resource in resources:
                if (resource.is_free_tier == False ):           # Exclude Free Tier which are always 'LICENSE_INCLUDED')
                    if (resource.license_model == 'LICENSE_INCLUDED'):
                        print(red("    * {} ({}) in {}".format(resource.display_name, resource.license_model, compartment.name)))
                        
                        target_resources.append(resource)
                    else:
                        print(green("      {} ({}) in {}".format(resource.display_name, resource.license_model, compartment.name)))

        print("\nChanging * marked {}'s lisence model...".format(resource_name))
        for resource in target_resources:
            try:
                response = _change_license_model(config, signer, resource.id, 'BRING_YOUR_OWN_LICENSE')
            except oci.exceptions.ServiceError as e:
                print("---------> error. status: {}".format(e))
                pass
            else:
                if response.lifecycle_state == 'UPDATING':
                    print(red("    change requested: {} ({})".format(response.display_name, response.lifecycle_state)))
                else:
                    print("---------> error changing {} ({})".format(response.display_name, response.lifecycle_state))

        print("\nAll {} changed!".format(resource_name))

def _get_resource_list(config, signer, compartment_id):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    resources = oci.pagination.list_call_get_all_results(
        object.list_autonomous_databases,
        compartment_id=compartment_id
    )
    return resources.data

def _change_license_model(config, signer, resource_id, license_model):
    object = oci.database.DatabaseClient(config=config, signer=signer)
    details = oci.database.models.UpdateAutonomousDatabaseDetails(license_model = license_model)
    response = object.update_autonomous_database(
        resource_id,
        details
    )
    return response.data

