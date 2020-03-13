# coding: utf-8

import oci
import csv
import time

red = lambda text: '\033[0;31m' + text + '\033[0m'
green = lambda text: '\033[0;32m' + text + '\033[0m'


def	create_budgets(Auth, Conf, Data, Tag):

    # Update region in config, replacing last used region with HomeRegion
    Auth['Config']['region'] = Auth["HomeRegion"]

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.budget.BudgetClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.budget.BudgetClient(config=Auth["Config"])

    if "/" in Tag:
        display_name = Tag.rsplit('/', 1)[-1]
    else:
        display_name = Tag.rsplit('.', 1)[-1]

    if "@" in display_name:
        Data["Recipients"].append(display_name)
        budget_name = display_name.split("@")[0] # Remove @xxx.xxx, illegal character for budget name
    else:
        budget_name = display_name
    
    budget_name = "." + budget_name # Adding a dot to differentiate budget created by the script
    print("Creating budget for {} ".format(green(budget_name)))

    recipients = Data["Recipients"]
    recipients = (', '.join(recipients)) # => get recipients list without brackets
    compartment_id = Auth["Tenancy_id"]
    target = Tag

    # create the budget
    create_budget_response = object.create_budget(
        oci.budget.models.CreateBudgetDetails(
            compartment_id=compartment_id,
            display_name=budget_name,
            target_type=Data["Target_type"],
            targets=[target],
            amount=float(Data["Amount"]),
            reset_period="MONTHLY"
        )
    )
    #print('Created budget:')
    #print(create_budget_response.data)

    budget_id = create_budget_response.data.id

    # create the alert rule on the budget
    print("Creating alert for {} ".format(green(budget_name)))
    create_alert_rule_response = object.create_alert_rule(
        budget_id,
        oci.budget.models.CreateAlertRuleDetails(
            type=Data["Type"],
            threshold=float(Data["Threshold"]),
            threshold_type=Data["Threshold_type"],
            recipients=recipients,
            message=Data["Message"]
        )
    )
    #print('Created AlertRule:')
    #print(create_alert_rule_response.data)

    alert_rule_id = create_alert_rule_response.data.id
    time.sleep(2)

    if "@" in display_name:
        Data["Recipients"].remove(display_name) # remove the owner email from the Recipients's list in the dict => Just keep original Recipients.

def	manage_budgets(Auth, Conf, Data):

    OwnerTags_updated = []
    Exclusions = ["logging"]
    My_Budget_Tags = []
    target_type="ALL"

    if Auth["Use_instance_principal"] == 'TRUE':
        object = oci.budget.BudgetClient(config={}, signer=Auth["Signer"])
    else:
        object = oci.budget.BudgetClient(config=Auth["Config"])
    
    print ("\n==={ Collecting existing Budgets }===")
    All_Budgets = oci.pagination.list_call_get_all_results(object.list_budgets, compartment_id=Auth["Tenancy_id"], target_type=target_type).data

    for budget in All_Budgets:
        if budget.target_type == "TAG":
            target = budget.targets[0] # get tag value without brackets
            My_Budget_Tags.append(target)

    for tag in Data["OwnerTags"]:
        full_tag = ("{}.{}.{}".format(Data["MyTagNamespace"], Data["MyTagKey"], tag))
        OwnerTags_updated.append(full_tag)

    for Tag in OwnerTags_updated:
        if Tag not in My_Budget_Tags and Tag not in Exclusions:
            print("No budget found for {}".format(Tag))
            create_budgets(Auth, Conf, Data, Tag)

    if Data["Cleanup"] == 'TRUE':
        for Tag in My_Budget_Tags:
            if Tag not in OwnerTags_updated:
                print("Deleling budget {} ".format(red(Tag)))
                print(Tag)
                for budget in All_Budgets:
                    if Tag  == budget.targets[0]:
                        delete_budget_response = object.delete_budget(
                            budget_id=budget.id)