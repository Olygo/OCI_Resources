import oci
import os.path
import sys
import time

OPERATING_SYSTEM = 'Oracle Linux'


def get_availability_domain(identity_client, compartment_id):
    list_availability_domains_response = oci.pagination.list_call_get_all_results(
        identity_client.list_availability_domains,
        compartment_id
    )
    # For demonstration, we just return the first availability domain but for Production code you should
    # have a better way of determining what is needed
    availability_domain = list_availability_domains_response.data[0]

    print()
    print('Running in Availability Domain: {}'.format(availability_domain.name))

    return availability_domain


def get_shape(compute_client, compartment_id, availability_domain):
    list_shapes_response = oci.pagination.list_call_get_all_results(
        compute_client.list_shapes,
        compartment_id,
        availability_domain=availability_domain.name
    )
    shapes = list_shapes_response.data
    if len(shapes) == 0:
        raise RuntimeError('No available shape was found.')

    vm_shapes = list(filter(lambda shape: shape.shape.startswith("VM"), shapes))
    if len(vm_shapes) == 0:
        raise RuntimeError('No available VM shape was found.')

    # For demonstration, we just return the first shape but for Production code you should have a better
    # way of determining what is needed
    shape = vm_shapes[0]
    
#    print(vm_shapes)
#    input("pause")

    print('Found Shape: {}'.format(shape.shape))

    return shape


def get_image(compute, compartment_id, shape):
    # Listing images is a paginated call, so we can use the oci.pagination module to get all results
    # without having to manually handle page tokens
    #
    # In this case, we want to find the image for the operating system we want to run, and which can
    # be used for the shape of instance we want to launch
    list_images_response = oci.pagination.list_call_get_all_results(
        compute.list_images,
        compartment_id,
        operating_system=OPERATING_SYSTEM,
        shape="VM.Standard2.4"
#        shape=shape.shape
#        VM.Standard2.4
    )
    images = list_images_response.data
    if len(images) == 0:
        raise RuntimeError('No available image was found.')

    # For demonstration, we just return the first image but for Production code you should have a better
    # way of determining what is needed
    image = images[0]

    print('Found Image: {}'.format(image.id))
    print()

    return image


def create_vcn(virtual_network_composite_operations, compartment_id, cidr_block):
    vcn_name = 'Mushop_vcn'
    create_vcn_details = oci.core.models.CreateVcnDetails(
        cidr_block=cidr_block,
        display_name=vcn_name,
        compartment_id=compartment_id
    )
    create_vcn_response = virtual_network_composite_operations.create_vcn_and_wait_for_state(
        create_vcn_details,
        wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_AVAILABLE]
    )
    vcn = create_vcn_response.data

    print('Created VCN: {}'.format(vcn.id))
    print('{}'.format(vcn))
    print()

    return vcn


# def delete_vcn(virtual_network_composite_operations, vcn):
#     virtual_network_composite_operations.delete_vcn_and_wait_for_state(
#         vcn.id,
#         wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_TERMINATED]
#     )

#     print('Deleted VCN: {}'.format(vcn.id))
#     print()


def create_subnet(virtual_network_composite_operations, vcn, availability_domain):
    subnet_name = 'Mushop_subnet'
    create_subnet_details = oci.core.models.CreateSubnetDetails(
        compartment_id=vcn.compartment_id,
        availability_domain=availability_domain.name,
        display_name=subnet_name,
        vcn_id=vcn.id,
        cidr_block=vcn.cidr_block
    )
    create_subnet_response = virtual_network_composite_operations.create_subnet_and_wait_for_state(
        create_subnet_details,
        wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_AVAILABLE]
    )
    subnet = create_subnet_response.data

    print('Created Subnet: {}'.format(subnet.id))
    print('{}'.format(subnet))
    print()

    return subnet


# def delete_subnet(virtual_network_composite_operations, subnet):
#     virtual_network_composite_operations.delete_subnet_and_wait_for_state(
#         subnet.id,
#         wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_TERMINATED]
#     )

#     print('Deleted Subnet: {}'.format(subnet.id))
#     print()


def create_internet_gateway(virtual_network_composite_operations, vcn):
    internet_gateway_name = 'Mushop_ig'
    create_internet_gateway_details = oci.core.models.CreateInternetGatewayDetails(
        display_name=internet_gateway_name,
        compartment_id=vcn.compartment_id,
        is_enabled=True,
        vcn_id=vcn.id
    )
    create_internet_gateway_response = virtual_network_composite_operations.create_internet_gateway_and_wait_for_state(
        create_internet_gateway_details,
        wait_for_states=[oci.core.models.InternetGateway.LIFECYCLE_STATE_AVAILABLE]
    )
    internet_gateway = create_internet_gateway_response.data

    print('Created internet gateway: {}'.format(internet_gateway.id))
    print('{}'.format(internet_gateway))
    print()

    return internet_gateway


# def delete_internet_gateway(virtual_network_composite_operations, internet_gateway):
#     virtual_network_composite_operations.delete_internet_gateway_and_wait_for_state(
#         internet_gateway.id,
#         wait_for_states=[oci.core.models.InternetGateway.LIFECYCLE_STATE_TERMINATED]
#     )

#     print('Deleted Internet Gateway: {}'.format(internet_gateway.id))
#     print()


# This makes sure that we use the internet gateway for accessing the internet. See:
# https://docs.cloud.oracle.com/Content/Network/Tasks/managingIGs.htm
# for more information.
#
# As a convenience, we'll add a route rule to the default route table. However, in your
# own code you may opt to use a different route table
def add_route_rule_to_default_route_table_for_internet_gateway(
        virtual_network_client, virtual_network_composite_operations, vcn, internet_gateway):
    get_route_table_response = virtual_network_client.get_route_table(vcn.default_route_table_id)
    route_rules = get_route_table_response.data.route_rules

    print('Current Route Rules For VCN')
    print('===========================')
    print('{}'.format(route_rules))
    print()

    # Updating route rules will totally replace any current route rules with what we send through.
    # If we wish to preserve any existing route rules, we need to read them out first and then send
    # them back to the service as part of any update
    route_rule = oci.core.models.RouteRule(
        cidr_block=None,
        destination='0.0.0.0/0',
        destination_type='CIDR_BLOCK',
        network_entity_id=internet_gateway.id
    )
    route_rules.append(route_rule)
    update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=route_rules)
    update_route_table_response = virtual_network_composite_operations.update_route_table_and_wait_for_state(
        vcn.default_route_table_id,
        update_route_table_details,
        wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
    )
    route_table = update_route_table_response.data

    print('Updated Route Rules For VCN')
    print('===========================')
    print('{}'.format(route_table.route_rules))
    print()

    return route_table


def clear_route_rules_from_default_route_table(virtual_network_composite_operations, vcn):
    update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=[])
    virtual_network_composite_operations.update_route_table_and_wait_for_state(
        vcn.default_route_table_id,
        update_route_table_details,
        wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
    )

    print('Cleared Route Rules from Route Table: {}'.format(vcn.default_route_table_id))
    print()


def create_network_security_group(virtual_network_composite_operations, compartment_id, vcn):
    network_security_group_name = 'Mushop_network_security_group'
    create_network_security_group_details = oci.core.models.CreateNetworkSecurityGroupDetails(
        display_name=network_security_group_name,
        compartment_id=compartment_id,
        vcn_id=vcn.id
    )
    create_network_security_group_response = virtual_network_composite_operations.create_network_security_group_and_wait_for_state(
        create_network_security_group_details,
        wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
    )
    network_security_group = create_network_security_group_response.data

    print('Created Network Security Group: {}'.format(network_security_group.id))
    print('{}'.format(network_security_group))
    print()

    return network_security_group


# def delete_network_security_group(virtual_network_composite_operations, network_security_group):
#     virtual_network_composite_operations.delete_network_security_group_and_wait_for_state(
#         network_security_group.id,
#         wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_TERMINATED]
#     )

#     print('Deleted Network Security Group: {}'.format(network_security_group.id))
#     print()


def add_network_security_group_security_rules(virtual_network_client, network_security_group):
    list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
        network_security_group.id
    )
    security_rules = list_security_rules_response.data

    print('Current Security Rules in Network Security Group')
    print('================================================')
    print('{}'.format(security_rules))
    print()

    add_security_rule_details = oci.core.models.AddSecurityRuleDetails(
        description="Incoming HTTP connections",
        direction="INGRESS",
        is_stateless=False,
        protocol="6",  # 1: ICMP, 6: TCP, 17: UDP, 58: ICMPv6
        source="0.0.0.0/0",
        source_type="CIDR_BLOCK",
        tcp_options=oci.core.models.TcpOptions(
            destination_port_range=oci.core.models.PortRange(min=80, max=80)
        )
    )
    add_security_rules_details = oci.core.models.AddNetworkSecurityGroupSecurityRulesDetails(
        security_rules=[add_security_rule_details]
    )
    virtual_network_client.add_network_security_group_security_rules(
        network_security_group.id,
        add_security_rules_details
    )

    list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
        network_security_group.id
    )
    security_rules = list_security_rules_response.data

    print('Updated Security Rules in Network Security Group')
    print('================================================')
    print('{}'.format(security_rules))
    print()


def remove_network_security_group_security_rules(virtual_network_client, network_security_group):
    list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
        network_security_group.id
    )
    security_rules = list_security_rules_response.data
    security_rule_ids = [security_rule.id for security_rule in security_rules]
    remove_security_rules_details = oci.core.models.RemoveNetworkSecurityGroupSecurityRulesDetails(
        security_rule_ids=security_rule_ids
    )
    virtual_network_client.remove_network_security_group_security_rules(
        network_security_group.id,
        remove_security_rules_details
    )

    print('Removed all Security Rules in Network Security Group: {}'.format(network_security_group.id))
    print()


def get_launch_instance_details(compartment_id, availability_domain, shape, image, subnet, ssh_public_key, boot_volume_id, ip, instance_name):

    # We can use instance metadata to specify the SSH keys to be included in the
    # ~/.ssh/authorized_keys file for the default user on the instance via the special "ssh_authorized_keys" key.
    #
    # We can also provide arbitrary string keys and string values. If you are providing these, you should consider
    # whether defined and freeform tags on an instance would better meet your use case. See:
    # https://docs.cloud.oracle.com/Content/Identity/Concepts/taggingoverview.htm for more information
    # on tagging
   
   
    # instance_metadata = {
    #     'ssh_authorized_keys': ssh_public_key,
    #     'some_metadata_item': 'some_item_value'
    # }

    # We can also provide a user_data key in the metadata that will be used by Cloud-Init
    # to run custom scripts or provide custom Cloud-Init configuration. The contents of this
    # key should be Base64-encoded data and the SDK offers a convenience function to transform
    # a file at a given path to that encoded data
    #
    # See: https://docs.cloud.oracle.com/api/#/en/iaas/20160918/datatypes/LaunchInstanceDetails
    # for more information
    # instance_metadata['user_data'] = oci.util.file_content_as_launch_instance_user_data(
    #     'examples/launch_instance/user_data.sh'
    # )
#    instance_metadata['user_data'] = oci.util.file_content_as_launch_instance_user_data('')

    # Extended metadata differs from normal metadata in that it can support nested maps/dicts. If you are providing
    # these, you should consider whether defined and freeform tags on an instance would better meet your use case.
    instance_extended_metadata = {
        'string_key_1': 'string_value_1',
        'map_key_1': {
            'string_key_2': 'string_value_2',
            'map_key_2': {
                'string_key_3': 'string_value_3'
            },
            'empty_map_key': {}
        }
    }

    # instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
    #     #image_id=image.id
    #     image_id="ocid1.bootvolume.oc1.eu-marseille-1.abwxeljre4wbnpnasqqnoex64wja4c6ruvnwraay2aemsdhm76ocwbwrw5ea"
    # )
    create_vnic_details = oci.core.models.CreateVnicDetails(
        subnet_id=subnet.id,
        nsg_ids=[network_security_group.id],
        private_ip= ip      
    )
    launch_instance_details = oci.core.models.LaunchInstanceDetails(
        display_name=instance_name,
        compartment_id=compartment_id,
        availability_domain=availability_domain.name,
#        shape=shape.shape,
        shape="VM.Standard.E4.Flex",
#        metadata=instance_metadata,
#        extended_metadata=instance_extended_metadata,
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=4,
            memory_in_gbs=64,
            baseline_ocpu_utilization="BASELINE_1_1"),
        source_details=oci.core.models.InstanceSourceViaBootVolumeDetails(
            source_type="bootVolume",
            boot_volume_id=boot_volume_id),
 #       source_details=instance_source_via_image_details,
        create_vnic_details=create_vnic_details
    )
    return launch_instance_details


def launch_instance(compute_client_composite_operations, launch_instance_details):
    launch_instance_response = compute_client_composite_operations.launch_instance_and_wait_for_state(
        launch_instance_details,
        wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_RUNNING]
    )
    instance = launch_instance_response.data

    print('Launched Instance: {}'.format(instance.id))
    print('{}'.format(instance))
    print()

    return instance


def launch_instance_and_wait_for_work_request(compute_client_composite_operations, launch_instance_details):
    work_request_response = compute_client_composite_operations.launch_instance_and_wait_for_work_request(
        launch_instance_details
    )
    work_request = work_request_response.data

    # Now retrieve the instance details from the information in the work request resources
    instance_id = work_request.resources[0].identifier
    get_instance_response = compute_client_composite_operations.client.get_instance(instance_id)
    instance = get_instance_response.data

    return instance, work_request.id


# def terminate_instance(compute_client_composite_operations, instance):
#     print('Terminating Instance: {}'.format(instance.id))
#     compute_client_composite_operations.terminate_instance_and_wait_for_state(
#         instance.id,
#         wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED]
#     )

#     print('Terminated Instance: {}'.format(instance.id))
#     print()


def print_instance_details(compute_client, virtual_network_client, instance):
    # We can find the private and public IP address of the instance by getting information on its VNIC(s). This
    # relationship is indirect, via the VnicAttachments of an instance

    # Note that listing VNIC attachments is a paginated operation so we can use the oci.pagination module to avoid
    # having to manually deal with page tokens.
    #
    # Since we're only interested in our specific instance, we can pass that as a filter to the list operation
    list_vnic_attachments_response = oci.pagination.list_call_get_all_results(
        compute_client.list_vnic_attachments,
        compartment_id,
        instance_id=instance.id
    )
    vnic_attachments = list_vnic_attachments_response.data

    vnic_attachment = vnic_attachments[0]
    get_vnic_response = virtual_network_client.get_vnic(vnic_attachment.vnic_id)
    vnic = get_vnic_response.data

    print('Virtual Network Interface Card')
    print('==============================')
    print('{}'.format(vnic))
    print()

    return vnic


def print_work_request_details(work_request_client, work_request_id):
    get_work_request_response = work_request_client.get_work_request(work_request_id)
    work_request_details = get_work_request_response.data

    list_errors_response = work_request_client.list_work_request_errors(work_request_id)
    work_request_errors = list_errors_response.data

    print('Work Request Details')
    print('====================')
    print('{}'.format(work_request_details))
    print()

    print('Work Request Errors')
    print('===================')
    if len(work_request_errors) > 0:
        print('{}'.format(work_request_errors))
    else:
        print('No errors occurred.')
    print()

    print('Work Request Logs')
    print('=================')

    # Limit to 20 log entries
    log_limit = 20
    page_size = 5
    resp = oci.pagination.list_call_get_up_to_limit(work_request_client.list_work_request_logs, log_limit, page_size, work_request_id)
    for work_request_log in resp.data:
        print('{}'.format(work_request_log))
    print()


if __name__ == "__main__":
    # if len(sys.argv) != 4:
    #     raise RuntimeError('Invalid number of arguments provided to the script. '
    #                        'Consult the script header for required arguments')

#    compartment_id = sys.argv[1]
#    cidr_block = sys.argv[2]

    compartment_id = "ocid1.compartment.oc1..aaaaaaaak4lbrnxsffqwtyuw477drvtnvaiycup4besyqolkiq7ekbyn4ara"
    cidr_block = "10.1.21.0/24"
    ssh_public_key = None
    instance_name_0 = 'Mushop_0'
    instance_name_1 = 'Mushop_1'
    boot_volume_id_0="ocid1.bootvolume.oc1.eu-marseille-1.abwxeljrj7wh3lfzctz7tkwsdblcji3m2fo7kzuy427arc53skuz75pgud4a"
    boot_volume_id_1="ocid1.bootvolume.oc1.eu-marseille-1.abwxeljrih2eg5jlglk4mj73djp3e4ok5sywfj5deqxgpokpx225lvmc4auq"
    ip_0 = '10.1.21.129'
    ip_1 = '10.1.21.64'
    shape = "VM.Standard2.4"
#    with open(os.path.expandvars(os.path.expanduser(sys.argv[3])), mode='r') as file:
#        ssh_public_key = file.read()

################################    CLOUDSHELL AUTH   ################################

    # Default config file and profile
    # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use it
    env_config_file = os.environ.get('OCI_CONFIG_FILE')
    env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

    # check if file exist
    if env_config_file is None or env_config_section is None:
        print("This is not a Cloud Shell instance, abort...")
        raise SystemExit

    config = oci.config.from_file(env_config_file, env_config_section)
    delegation_token_location = config["delegation_token_file"]

    with open(delegation_token_location, 'r') as delegation_token_file:
        delegation_token = delegation_token_file.read().strip()
        # get signer from delegation token
        signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)
        print(f"Successfuly authenticated through Cloud Shell: {signer}")

################################    SET VARs   ################################

    #config = oci.config.from_file()
    identity_client = oci.identity.IdentityClient(config)
    compute_client = oci.core.ComputeClient(config)
    compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(compute_client)
    virtual_network_client = oci.core.VirtualNetworkClient(config)
    virtual_network_composite_operations = oci.core.VirtualNetworkClientCompositeOperations(virtual_network_client)
    work_request_client = oci.work_requests.WorkRequestClient(config)

    availability_domain = get_availability_domain(identity_client, compartment_id)
#    shape = get_shape(compute_client, compartment_id, availability_domain)
    shape=shape
    image = get_image(compute_client, compartment_id, shape)

    vcn = None
    subnet = None
    internet_gateway = None
    network_security_group = None
    instance = None
    instance_via_work_requests = None
    instance_with_network_security_group = None

    try:

################################    CREATE THE VCN   ################################

        vcn = create_vcn(virtual_network_composite_operations, compartment_id, cidr_block)
        subnet = create_subnet(virtual_network_composite_operations, vcn, availability_domain)
        internet_gateway = create_internet_gateway(virtual_network_composite_operations, vcn)
        add_route_rule_to_default_route_table_for_internet_gateway(
            virtual_network_client, virtual_network_composite_operations, vcn, internet_gateway
        )
        network_security_group = create_network_security_group(virtual_network_composite_operations, compartment_id, vcn)
        add_network_security_group_security_rules(virtual_network_client, network_security_group)

################################    CREATE THE LOADBALANCER   ################################

        load_balancer_client = oci.load_balancer.LoadBalancerClient(config)

        create_load_balancer_response = load_balancer_client.create_load_balancer(
            create_load_balancer_details=oci.load_balancer.models.CreateLoadBalancerDetails(
            compartment_id=compartment_id,
            display_name="Mushop_LB",
            shape_name="flexible",   ##### CLI => 'oci lb shape list -c ocid1.compartment.oc1..aaxxxxx....'
            subnet_ids=[subnet.id],
            shape_details=oci.load_balancer.models.ShapeDetails(
                minimum_bandwidth_in_mbps=100,
                maximum_bandwidth_in_mbps=200),
            is_private=False,
            ip_mode="IPV4",
            reserved_ips=[                                # Comment line to remove PIP
                oci.load_balancer.models.ReservedIP(      # Comment line to remove PIP
                    id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqa7iuqm5itzwi54k3eflhihc3wymopo63y3dlonlnsenea")],  # Comment line to remove PIP
            listeners={
                'My_Listener': {
                    'defaultBackendSetName': 'My_Backend_Set',
                    'port': 80,
                    'protocol': 'HTTP'
                    # 'hostnameNames': ['EXAMPLE--Value'],
                    # 'pathRouteSetName': 'EXAMPLE-pathRouteSetName-Value',
                    # 'sslConfiguration': {
                    # 'verifyDepth': 13,
                    # 'verifyPeerCertificate': True,
                    # 'trustedCertificateAuthorityIds': ['EXAMPLE--Value'],
                    # 'certificateIds': ['EXAMPLE--Value'],
                    # 'certificateName': 'EXAMPLE-certificateName-Value',
                    # 'protocols': ['EXAMPLE--Value'],
                    # 'cipherSuiteName': 'EXAMPLE-cipherSuiteName-Value',
                    # 'serverOrderPreference': 'DISABLED'},
                    # 'connectionConfiguration': {
                    # 'idleTimeout': 902,
                    # 'backendTcpProxyProtocolVersion': 1},
                    # 'routingPolicyName': 'EXAMPLE-routingPolicyName-Value',
                    # 'ruleSetNames': ['EXAMPLE--Value']
                    }},
            hostnames={
                'EXAMPLE_KEY_LjEsE': {
                    'name': 'EXAMPLE-name-Value',
                    'hostname': 'EXAMPLE-hostname-Value'}},
            backend_sets={
                'My_Backend_Set': {
                    'policy': 'ROUND_ROBIN',   ##### CLI => 'oci lb policy list -c ocid1.compartment.oc1..aaxxxxx....'
                    'healthChecker': {
                        'protocol': 'HTTP',
                        'urlPath': '/',
                        'port': 80,
                        # 'returnCode': 629,
                         'retries': 999,    # Max Retry to connect to Instances
                         'timeoutInMillis': 10000, # Retry Every 10s
                         'intervalInMillis': 10000 #, Retry Every 10s
                        # 'responseBodyRegex': 'EXAMPLE-responseBodyRegex-Value'
                        },
                    'backends': [
                        {
                            'ipAddress': ip_0,
                            'port': 80,
                            'weight': 1,
                            'backup': False,
                            'drain': False,
                            'offline': False},
                            {
                            'ipAddress': ip_1,
                            'port': 80,
                            'weight': 1,
                            'backup': False,
                            'drain': False,
                            'offline': False}
                            ]#,
                    # 'sslConfiguration': {
                    #     'verifyDepth': 633,
                    #     'verifyPeerCertificate': False,
                    #     'trustedCertificateAuthorityIds': ['EXAMPLE--Value'],
                    #     'certificateIds': ['EXAMPLE--Value'],
                    #     'certificateName': 'EXAMPLE-certificateName-Value',
                    #     'protocols': ['EXAMPLE--Value'],
                    #     'cipherSuiteName': 'EXAMPLE-cipherSuiteName-Value',
                    #     'serverOrderPreference': 'ENABLED'},
                    # 'sessionPersistenceConfiguration': {
                    #     'cookieName': 'EXAMPLE-cookieName-Value',
                    #     'disableFallback': True},
                    # 'lbCookieSessionPersistenceConfiguration': {
                    #     'cookieName': 'EXAMPLE-cookieName-Value',
                    #     'disableFallback': True,
                    #     'domain': 'EXAMPLE-domain-Value',
                    #     'path': 'EXAMPLE-path-Value',
                    #     'maxAgeInSeconds': 22,
                    #     'isSecure': False,
                    #     'isHttpOnly': True}}
                        }},
            network_security_group_ids=[network_security_group.id]
            ))
        #     certificates={
        #         'EXAMPLE_KEY_rGoqj': {
        #             'certificateName': 'EXAMPLE-certificateName-Value',
        #             'passphrase': 'EXAMPLE-passphrase-Value',
        #             'privateKey': 'EXAMPLE-privateKey-Value',
        #             'publicCertificate': 'EXAMPLE-publicCertificate-Value',
        #             'caCertificate': 'EXAMPLE-caCertificate-Value'}},
        #     ssl_cipher_suites={
        #         'EXAMPLE_KEY_ubJmH': {
        #             'name': 'EXAMPLE-name-Value',
        #             'ciphers': ['EXAMPLE--Value']}},
        #     path_route_sets={
        #         'EXAMPLE_KEY_uogso': {
        #             'pathRoutes': [
        #                 {
        #                     'path': 'EXAMPLE-path-Value',
        #                     'pathMatchType': {
        #                         'matchType': 'EXACT_MATCH'},
        #                     'backendSetName': 'EXAMPLE-backendSetName-Value'}]}},
        #     freeform_tags={
        #         'EXAMPLE_KEY_hVx4F': 'EXAMPLE_VALUE_gTyVgJkt1etO3hD4iN2I'},
        #     defined_tags={
        #         'EXAMPLE_KEY_ax88e': {
        #             'EXAMPLE_KEY_FfSs3': 'EXAMPLE--Value'}},
        #     rule_sets={
        #         'EXAMPLE_KEY_3uLsQ': {
        #             'items': [
        #                 {
        #                     'action': 'REDIRECT',
        #                     'conditions': [
        #                         {
        #                             'attributeName': 'PATH',
        #                             'attributeValue': 'EXAMPLE-attributeValue-Value',
        #                             'operator': 'EXACT_MATCH'}],
        #                     'responseCode': 306,
        #                     'redirectUri': {
        #                         'protocol': 'EXAMPLE-protocol-Value',
        #                         'host': 'EXAMPLE-host-Value',
        #                         'port': 14115,
        #                         'path': 'EXAMPLE-path-Value',
        #                         'query': 'EXAMPLE-query-Value'}}]}}),
        # opc_request_id="IMXUHDNLHHJFB7RMX7VC<unique_ID>",
        # opc_retry_token="EXAMPLE-opcRetryToken-Value")

        # Get the data from response
        print(create_load_balancer_response.headers)
        print()

################################    CREATE THE INSTANCE 1   ################################

        print('Launching Mushop_0 ...')
        launch_instance_details = get_launch_instance_details(
            compartment_id, availability_domain, shape, image, subnet, ssh_public_key, boot_volume_id_0, ip_0, instance_name_0
            )
        instance = launch_instance(compute_client_composite_operations, launch_instance_details)
        print_instance_details(compute_client, virtual_network_client, instance)

        # try:
        #     print(print_instance_details)
        #     print(print_instance_details.data)
        #     input("pause")
        # except:
        #     input("pause ELSE")


        #print('Launching Instance and waiting on work request ...')
#        time.sleep(10)
# 01:22        launch_instance_details = get_launch_instance_details(
# 01:22            compartment_id, availability_domain, shape, image, subnet, ssh_public_key
# 01:22        )
#        instance_via_work_requests, work_request_id = launch_instance_and_wait_for_work_request(
#            compute_client_composite_operations, launch_instance_details
#       )
#        print_work_request_details(work_request_client, work_request_id)
#        print_instance_details(compute_client, virtual_network_client) #instance_via_work_requests)

################################    ASSIGN NSG INSTANCE 1   ################################

        print('Updating Network Security Group ...')

        Vnic = print_instance_details(compute_client, virtual_network_client, instance)
        virtual_network_client.update_vnic(
            Vnic.id,
            update_vnic_details=oci.core.models.UpdateVnicDetails(
            nsg_ids=[network_security_group.id],
        )
        )

        # try:
        #     print(Vnic)
        #     print(Vnic.data)
        #     input("pause")
        # except:
        #     input("pause ELSE")


################################    ASSIGN PIP INSTANCE 1   ################################

        # # Initialize service client with default config file
        # core_client = oci.core.VirtualNetworkClient(config)

        # update_public_ip_response = core_client.update_public_ip(
        #     public_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaiogxlmmoyvcu3yjh42gr2ctzwjj632gf2gvr7yqvzpka",
        #     update_public_ip_details=oci.core.models.UpdatePublicIpDetails(
        #     display_name="PIP_MRS_VM0",
        #     private_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaiogxlmmoyvcu3yjh42gr2ctzwjj632gf2gvr7yqvzpka"),
        # )

        # # Get the data from response
        # print(update_public_ip_response.data)

        # We'll now assign the public IP to the private IP from the instance we launched earlier. First we'll need to
        # get the ID of the private IP
        public_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaiogxlmmoyvcu3yjh42gr2ctzwjj632gf2gvr7yqvzpka"
        # LIST VNIC ATTACHMENT
        vnic_attachments = compute_client.list_vnic_attachments(compartment_id, instance_id=instance.id).data
        # print("vnic_attachments IS:")
        # print(vnic_attachments)
        # input("vnic_attachments")
        vnic_id = vnic_attachments[0].vnic_id
        # print("vnic_attachments[0].vnic_id IS:")
        # print(vnic_id)
        # input("vnic_attachments[0].vnic_id")
        private_ip_id = virtual_network_client.list_private_ips(vnic_id=vnic_id).data[0].id
        # GET VNIC ATTACHMENT
        VMvnicAttachment = compute_client.get_vnic_attachment(vnic_attachments[0].id)

        list_public_ips_response = virtual_network_client.list_public_ips(
        scope="REGION",
        compartment_id=compartment_id,
        lifetime="EPHEMERAL"
        )
        # Get Public IP data from Public IP itself
        get_public_ip_by_ip_address_response = virtual_network_client.get_public_ip_by_ip_address(
            get_public_ip_by_ip_address_details=oci.core.models.GetPublicIpByIpAddressDetails(
                ip_address=Vnic.public_ip))

        # Get the data from response
        print(get_public_ip_by_ip_address_response.data)

        public_ip_data = get_public_ip_by_ip_address_response.data

        # # We can also unassign the public IP from any private IP by passing an empty string as the private_ip_id
        # # when doing the update. Note that the states we wait on after the update has been requested
        # #### UNASSIGN A RESERVED PUBLIC IP
        # virtual_network_client.update_public_ip(
        #     public_ip_data.id,
        #     oci.core.models.UpdatePublicIpDetails(
        #         private_ip_id=''
        #         )
        #         )
        # updated_public_ip = oci.wait_until(
        #     virtual_network_client,
        #     virtual_network_client.get_public_ip(VMvnicAttachment),
        #     evaluate_response=lambda r: r.data.lifecycle_state in ['AVAILABLE', 'UNASSIGNED']
        #     )

        ##### UNASSIGN EPHERAL PUBLIC IP
        delete_public_ip_response = virtual_network_client.delete_public_ip(
            public_ip_id=public_ip_data.id)#,
#            if_match=Vnic.public_ip)

        # Get the data from response
        print(delete_public_ip_response.headers) 
        time.sleep(10)       

        # Now we can update the public IP to link it to the private IP. Once the update has been requested, we can
                # use a waiter to wait until the public IP enters the appropriate state
        PIP_ID_0 = "ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaiogxlmmoyvcu3yjh42gr2ctzwjj632gf2gvr7yqvzpka"
        PIP_ID_1 = "ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaogcqfft7sge7ebg3zezrv63ocklto34q5zzesevcj7xa"
        virtual_network_client.update_public_ip(
            PIP_ID_0,
            oci.core.models.UpdatePublicIpDetails(
            private_ip_id=private_ip_id
            )
            )
        # updated_public_ip = oci.wait_until(
        #     virtual_network_client,
        #     virtual_network_client.get_public_ip(public_ip_id,
        #     evaluate_response=lambda r: r.data.lifecycle_state in ['AVAILABLE', 'ASSIGNED']
        # ))
        # print('Updated public IP: {}'.format(updated_public_ip.data))
        # print('\n================================\n')
        # input("PAUSE")
        time.sleep(10)


################################    CREATE THE INSTANCE 2   ################################

        print('Launching Mushop_1 ...')
        launch_instance_details = get_launch_instance_details(
            compartment_id, availability_domain, shape, image, subnet, ssh_public_key, boot_volume_id_1, ip_1, instance_name_1
            )
        instance = launch_instance(compute_client_composite_operations, launch_instance_details)
        print_instance_details(compute_client, virtual_network_client, instance)

################################    ASSIGN NSG INSTANCE 2   ################################

        print('Updating Network Security Group ...')

        Vnic = print_instance_details(compute_client, virtual_network_client, instance)
        virtual_network_client.update_vnic(
            Vnic.id,
            update_vnic_details=oci.core.models.UpdateVnicDetails(
            nsg_ids=[network_security_group.id],
        )
        )

    #    launch_instance_details.create_vnic_details.nsg_ids = [network_security_group.id]
    #    instance_with_network_security_group = launch_instance(
    #         compute_client_composite_operations, launch_instance_details
    #     )
    #    print_instance_details(compute_client, virtual_network_client, instance_with_network_security_group)

################################    ASSIGN PIP INSTANCE 2   ################################

        # # Initialize service client with default config file
        # core_client = oci.core.VirtualNetworkClient(config)

        # update_public_ip_response = core_client.update_public_ip(
        #     public_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaogcqfft7sge7ebg3zezrv63ocklto34q5zzesevcj7xa",
        #     update_public_ip_details=oci.core.models.UpdatePublicIpDetails(
        #     display_name="PIP_MRS_VM1",
        #     private_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaogcqfft7sge7ebg3zezrv63ocklto34q5zzesevcj7xa"),
        # )

        # # Get the data from response
        # print(update_public_ip_response.data)

        # We'll now assign the public IP to the private IP from the instance we launched earlier. First we'll need to
        # get the ID of the private IP
        public_ip_id="ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaogcqfft7sge7ebg3zezrv63ocklto34q5zzesevcj7xa"
        # LIST VNIC ATTACHMENT
        vnic_attachments = compute_client.list_vnic_attachments(compartment_id, instance_id=instance.id).data
        # print("vnic_attachments IS:")
        # print(vnic_attachments)
        # input("vnic_attachments")
        vnic_id = vnic_attachments[0].vnic_id
        # print("vnic_attachments[0].vnic_id IS:")
        # print(vnic_id)
        # input("vnic_attachments[0].vnic_id")
        private_ip_id = virtual_network_client.list_private_ips(vnic_id=vnic_id).data[0].id
        # GET VNIC ATTACHMENT
        VMvnicAttachment = compute_client.get_vnic_attachment(vnic_attachments[0].id)

        list_public_ips_response = virtual_network_client.list_public_ips(
        scope="REGION",
        compartment_id=compartment_id,
        lifetime="EPHEMERAL"
        )
        # Get Public IP data from Public IP itself
        get_public_ip_by_ip_address_response = virtual_network_client.get_public_ip_by_ip_address(
            get_public_ip_by_ip_address_details=oci.core.models.GetPublicIpByIpAddressDetails(
                ip_address=Vnic.public_ip))

        # Get the data from response
        print(get_public_ip_by_ip_address_response.data)

        public_ip_data = get_public_ip_by_ip_address_response.data

        # # We can also unassign the public IP from any private IP by passing an empty string as the private_ip_id
        # # when doing the update. Note that the states we wait on after the update has been requested
        # #### UNASSIGN A RESERVED PUBLIC IP
        # virtual_network_client.update_public_ip(
        #     public_ip_data.id,
        #     oci.core.models.UpdatePublicIpDetails(
        #         private_ip_id=''
        #         )
        #         )
        # updated_public_ip = oci.wait_until(
        #     virtual_network_client,
        #     virtual_network_client.get_public_ip(VMvnicAttachment),
        #     evaluate_response=lambda r: r.data.lifecycle_state in ['AVAILABLE', 'UNASSIGNED']
        #     )

        ##### UNASSIGN EPHERAL PUBLIC IP
        delete_public_ip_response = virtual_network_client.delete_public_ip(
            public_ip_id=public_ip_data.id)#,
#            if_match=Vnic.public_ip)

        # Get the data from response
        print(delete_public_ip_response.headers) 
        time.sleep(10)       

        # Now we can update the public IP to link it to the private IP. Once the update has been requested, we can
                # use a waiter to wait until the public IP enters the appropriate state
        PIP_ID_0 = "ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaiogxlmmoyvcu3yjh42gr2ctzwjj632gf2gvr7yqvzpka"
        PIP_ID_1 = "ocid1.publicip.oc1.eu-marseille-1.amaaaaaaowy4maqaogcqfft7sge7ebg3zezrv63ocklto34q5zzesevcj7xa"
        virtual_network_client.update_public_ip(
            PIP_ID_1,
            oci.core.models.UpdatePublicIpDetails(
            private_ip_id=private_ip_id
            )
            )
        # updated_public_ip = oci.wait_until(
        #     virtual_network_client,
        #     virtual_network_client.get_public_ip(public_ip_id,
        #     evaluate_response=lambda r: r.data.lifecycle_state in ['AVAILABLE', 'ASSIGNED']
        # ))
        # print('Updated public IP: {}'.format(updated_public_ip.data))
        # print('\n================================\n')
        # input("PAUSE")
        time.sleep(10)

    finally:
        print("---DONE---")
        # if instance_with_network_security_group:
        #     terminate_instance(compute_client_composite_operations, instance_with_network_security_group)
        # if instance_via_work_requests:
        #     terminate_instance(compute_client_composite_operations, instance_via_work_requests)
        # if instance:
        #     terminate_instance(compute_client_composite_operations, instance)

        # # The network security group needs to be deleted before we can remove the subnet and vcn
        # if network_security_group:
        #     remove_network_security_group_security_rules(virtual_network_client, network_security_group)
        #     delete_network_security_group(virtual_network_composite_operations, network_security_group)

        # if internet_gateway:
        #     # Because the internet gateway is referenced by a route rule, the rule needs to be deleted before
        #     # we can remove the internet gateway
        #     clear_route_rules_from_default_route_table(virtual_network_composite_operations, vcn)
        #     delete_internet_gateway(virtual_network_composite_operations, internet_gateway)

        # if subnet:
        #     delete_subnet(virtual_network_composite_operations, subnet)

        # if vcn:
        #     delete_vcn(virtual_network_composite_operations, vcn)