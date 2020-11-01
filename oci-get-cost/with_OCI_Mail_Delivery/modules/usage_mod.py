# coding: utf-8

import oci
from datetime import datetime
from datetime import timedelta
from oci.usage_api import UsageapiClient
from oci.usage_api.models import RequestSummarizedUsagesDetails
from collections import OrderedDict # sort data dict by date order

def get_usage(config, signer, tenancy_id, end_at, start_at):

	usage_client = UsageapiClient(config=config, signer=signer)

	usage_detail = RequestSummarizedUsagesDetails()
	usage_detail.tenant_id = tenancy_id
	usage_detail.time_usage_ended = end_at
	usage_detail.time_usage_started = start_at
	usage_detail.group_by = ['service']
	usage_detail.query_type = "COST"
	usage_detail.granularity  = "MONTHLY"

	usages = usage_client.request_summarized_usages(
		usage_detail, 
		retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
		)
	return usages

def get_usage_details(config, signer, my_tenant, tenancy_id, usages, start_date, end_date):
    
    # init data dictionnary
    # dict will use a tuple as key (2 keys) 
    # and list as value to store multiple costs per item	
    data = {}

    # init amounts_list, store all items amount
    amounts_list = []

    for item in usages.data.items:
        if (item.computed_amount is not None):
            amount = item.computed_amount
            usage_end_date = item.time_usage_ended
            usage_end_date = str(usage_end_date)[:10]
            usage_end_date = datetime.strptime(usage_end_date, "%Y-%m-%d")
            usage_end_date = usage_end_date.strftime("%Y-%m-%d")
                
            usage_start_date = item.time_usage_started
            usage_start_date = str(usage_start_date)[:10]
            usage_start_date = datetime.strptime(usage_start_date, "%Y-%m-%d")
            usage_start_date = usage_start_date.strftime("%Y-%m-%d")

            if (usage_start_date,usage_end_date) not in data:
                data.update( {(usage_start_date,usage_end_date) : []} ) # Use a Tuple as key to add 2 keys in the Dict.
                data[(usage_start_date,usage_end_date)].append(amount)
                amounts_list.append(amount)
            else:
                data[(usage_start_date,usage_end_date)].append(amount)
                amounts_list.append(amount)
                currency = item.currency

    # init monthly dictionnary 
    # to store consumption results per month
    monthly_data = {}

    # Sort data dictionnary by date order
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))

    i = 1
    for key in data:
        total = sum(data[key])
        total = str(int(total))
        monthly_data.update( {
            i :
            '{:18s} {:12s} {:12s} {:7s} {:3s}'.format(
            my_tenant,
            key[0], # print key tuple value 0 => usage_start_date
            key[1], # print key tuple value 1 => usage_end_date
            total,
            currency)
            }
        )
        i = i + 1

    # calculate amounts_list consumption
    amounts_list = int(sum(amounts_list))
        
    # update monthly_data {Blank line}
    monthly_data.update( {
            i :
            '{:18s} {:12s} {:12s} {:7s} {:3s}'.format(
            "",
            "",
            "",
            "",
            "")
            }
        )
    i = i + 1

    # update monthly_data {Full Period}
    monthly_data.update( {
            i :
            '{:18s} {:12s} {:12s} {:7s} {:3s}'.format(
            "Full period",
            start_date,
            end_date,
            str(amounts_list),
            currency)
            }
        )
    i = i + 1

    # get weekly consumption
    this_week = datetime.today()  - timedelta(days=datetime.today().weekday() % 7)
    start_week = this_week.strftime("%Y-%m-%d")
    start_at = start_week + "T00:00:00.000Z"
    end_week = datetime.today()
    end_week = datetime.today()  + timedelta(days=1)
    end_week = end_week.strftime("%Y-%m-%d")
    end_at = end_week + "T00:00:00.000Z"

    # call get usage function for the current week
    usages = get_usage(config, signer, tenancy_id, end_at, start_at)

    amount = 0
    for item in usages.data.items:
        if (item.computed_amount is not None):
            amount += item.computed_amount

    # limit float to 2 decimal places 
    # when amount is < 10
    if amount < 10:
        amount = round(amount, 2)
    else:
        amount = int(amount)

    # update monthly_data {Current Week}
    monthly_data.update( {
            i :
            '{:18s} {:12s} {:12s} {:7s} {:3s}'.format(
            "Current week",
            start_week,
            end_week,
            str(amount),
            currency)
            }
        )
    i = i + 1

    return monthly_data