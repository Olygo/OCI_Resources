# coding: utf-8

import oci
from oci.signer import Signer
import datetime

def get_audit_events(Auth, audit, Events):

    # list_of_audit_events = []
    list_events_response = oci.pagination.list_call_get_all_results(
        audit.list_events,
        compartment_id=Auth["Compartment_ocid"],
        start_time=Auth["Start_time"],
        end_time=Auth["End_time"]).data

    for x in list_events_response:
        action = x.data.request.action
        if action == "POST" or action == "DELETE" :
            if x.data.event_name in Events:
                if x.data.event_name == "InstanceAction":
                    What = x.data.resource_name
                    How = x.data.request.parameters
                    Who = x.data.identity.principal_name
                    When = x.event_time
                    When = When.strftime("%d-%B-%Y %H:%M:%S")
                    print("{} => {} => {} @ {}".format(Who,How,What,When))
                else:
                    What = x.data.resource_name
                    How = x.data.event_name
                    Who = x.data.identity.principal_name
                    When = x.event_time
                    When = When.strftime("%d-%B-%Y %H:%M:%S")
                    print("{} => {} => {} @ {}".format(Who,How,What,When))

    print()

    #return list_of_audit_events

