import oci

def login(config, signer):
    identity = oci.identity.IdentityClient(config, signer=signer)
    user = identity.get_user(config['user']).data
    print("Logged in as: {} @ {}".format(user.description, config['region']))

def get_compartment_list(config, signer, compartment_id):
    identity = oci.identity.IdentityClient(config, signer=signer)

    target_compartments = []
    all_compartments = []

    top_level_compartment_response = identity.get_compartment(compartment_id)
    target_compartments.append(top_level_compartment_response.data)
    all_compartments.append(top_level_compartment_response.data)

    while len(target_compartments) > 0:
        target = target_compartments.pop(0)

        child_compartment_response = oci.pagination.list_call_get_all_results(
            identity.list_compartments,
            target.id
        )
        target_compartments.extend(child_compartment_response.data)
        all_compartments.extend(child_compartment_response.data)

    active_compartments = []
    for compartment in all_compartments:
        if compartment.lifecycle_state== 'ACTIVE':
            active_compartments.append(compartment)

    return active_compartments

def get_region_subscription_list(config, signer, tenancy_id):
    identity = oci.identity.IdentityClient(config, signer=signer)
    response = identity.list_region_subscriptions(
        tenancy_id
    )
    return response.data

