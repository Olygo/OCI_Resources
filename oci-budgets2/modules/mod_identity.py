# coding: utf-8

import oci

yellow = lambda text: '\033[0;33m' + text + '\033[0m'


def login(Auth):

    if Auth["Use_instance_principal"] == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
        print("Logged in as Instance Principal: {} ".format(identity))
    else:
        identity = oci.identity.IdentityClient(config=Auth["Config"])
        user = identity.get_user(Auth["Config"]['user']).data
        print("Logged in as: {} @ {}".format(user.description, Auth["Config"]['region']))

def get_compartment_list(Auth):
    if Auth["Use_instance_principal"] == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
    else:
        identity = oci.identity.IdentityClient(config=Auth["Config"])
        
    target_compartments = []
    all_compartments = []

    top_level_compartment_response = identity.get_compartment(Auth["Top_level_compartment_id"])
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

def get_region_subscription_list(Auth, HomeRegion):
    if Auth["Use_instance_principal"] == 'TRUE':
        identity = oci.identity.IdentityClient(config={}, signer=Auth["Signer"])
    else:
        identity = oci.identity.IdentityClient(config=Auth["Config"])
    
    response = identity.list_region_subscriptions(
        Auth["Tenancy_id"]
    )

    if HomeRegion == False:
        return response.data
    else:
        # identify home region, useful for some functions (ie: create_budget)
        for region in response.data:
            if region.is_home_region == True:
                print(yellow("Your Home Region is {}".format(region.region_name)))
                Auth.update( {'HomeRegion' : region.region_name} )
                return Auth