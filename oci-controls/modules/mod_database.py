import oci
import csv

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'
yellow = lambda text: '\033[0;33m' + text + '\033[0m'

Excluded_States = ['TERMINATED', 'TERMINATING']

def get_database_instances(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=signer)
    else:
        object = oci.database.DatabaseClient(config=config)

    print ("\n==========================={ Getting all Database Instances }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_db_systems, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                if (('System_Tags' in item.defined_tags) or ('Mandatory_Tags' in item.defined_tags) and ('Owner' in item.defined_tags['Mandatory_Tags'])): 
                    print ("Owner Tag OK for: {}".format(item.display_name))
                else:
                    print ("Owner Tag Missing for: {}".format(item.display_name))
                    try:
                        if cleanup == "YES":
                            print("Deleting: {}".format(item.display_name))
                            object.terminate_db_system(item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))
                    except oci.exceptions.ServiceError as e:
                        print("error deleting Database: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")
                        pass
                    finally:
                         with open(tags_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Database_Instances', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def delete_database_backups(config, signer, use_instance_principal, tenant_name, region, compartments, tags_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=signer)
    else:
        object = oci.database.DatabaseClient(config=config)

    print ("\n==========================={ Getting all Database Backups }=============================")
    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_backups, compartment_id=compartment.id).data
        for item in items:
            if (item.lifecycle_state not in Excluded_States):
                AllItems.append(item)
                try:
                    if cleanup == "YES":
                        print("Deleting: {}".format(item.display_name))
                        object.delete_backup(item.id)
                    else:
                        print("Logging in report: {}".format(item.display_name))
                except oci.exceptions.ServiceError as e:
                    print("error deleting Database Backup: {}".format(item.display_name))
                    print("---------> error. status: {}".format(e))
                    err.write(now) 
                    err.write("\n")
                    err.write("---------> error. status: {}".format(e))
                    err.write("\n")
                    pass                    
                finally:
                     with open(tags_report, mode='a', newline='') as csvfile:
                        fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'Compartment', 'Region']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow({'Profile': tenant_name, 'Service_Type': 'Database_Backups', 'Service_Name': item.display_name, 'Compartment': compartment.name, 'Region': region})
    err.close()

def get_no_byol_databases_licences(config, signer, use_instance_principal, tenant_name, region, compartments, licenses_report, cleanup, now, errors_log):
    err = open(errors_log, mode='a')
    AllItems = []

    if use_instance_principal == 'TRUE':
        object = oci.database.DatabaseClient(config={}, signer=signer)
    else:
        object = oci.database.DatabaseClient(config=config)
    
    print ("\n==========================={ Checking all Database Instances Licenses }=============================")

    for compartment in compartments:
        items = oci.pagination.list_call_get_all_results(object.list_db_systems, compartment_id=compartment.id).data
        for item in items:
            tag = item.defined_tags
            try:
                if 'System_Tags' in tag:
                    #print(tag['System_Tags']['Owner'])
                    Owner = tag['System_Tags']['Owner'].rsplit('/', 1)[-1]
                    print("System Owner is " + Owner)

                elif 'Mandatory_Tags' in tag:
                    #print(tag['Mandatory_Tags']['Owner'])
                    Owner = tag['Mandatory_Tags']['Owner'].rsplit('/', 1)[-1]
                    print("Mandatory Owner is " + Owner)
            except oci.exceptions.ServiceError as e:
                print("error getting Owner Tag for: {}".format(item.display_name))
                print("---------> error. status: {}".format(e))
                err.write(now) 
                err.write("\n")
                err.write("---------> error. status: {}".format(e))
                err.write("\n")
                pass
            
            if (item.lifecycle_state not in Excluded_States): #test si l'état de la DB fait partie de ma liste Excluded_States
                if (item.license_model != 'LICENSE_INCLUDED'):
                    print(green("    * {} ({}) in {}".format(item.display_name, item.license_model, compartment.name)))
                else:
                    print(red("    * {} ({}) in {}".format(item.display_name, item.license_model, compartment.name)))
                    AllItems.append(item)
                    try:
                        if cleanup == "YES":
                            print("Deleting Instance: {}".format(item.display_name))
                            object.terminate_db_system(item.id)
                        else:
                            print("Logging in report: {}".format(item.display_name))

                    except oci.exceptions.ServiceError as e:
                        print("error deleting Database: {}".format(item.display_name))
                        print("---------> error. status: {}".format(e))
                        err.write(now) 
                        err.write("\n")
                        err.write("---------> error. status: {}".format(e))
                        err.write("\n")
                        pass
                    finally:
                        with open(licenses_report, mode='a', newline='') as csvfile:
                            fieldnames = ['Profile', 'Service_Type', 'Service_Name', 'License_Type', 'Compartment', 'Region', 'Owner']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writerow({'Profile': tenant_name, 'Service_Type': 'Database_Instances', 'Service_Name': item.display_name, 'License_Type': item.license_model, 'Compartment': compartment.name, 'Region': region, 'Owner': Owner})
    err.close()
