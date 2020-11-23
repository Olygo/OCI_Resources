# oci-get-reports


This script downloads all CSV files and merge it into a single CSV

Download OCI Usage & Cost reports for the current month (default)

	python3 ./oci-get-reports.py

Download OCI Usage & Cost reports for a specific month (argument)

	python3 ./oci-get-reports.py 06

- Authentication is based on on OCI config file

Config file Authentication

        configfile = "/home/opc/.oci/config"

        [MYOCITENANTNAME]
        user=ocid1.user.oc1..aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        fingerprint=76:22:76:5c:33:12:1b:5c:82:95:5c:11:0a:30:a0:07
        key_file=/home/opc/.oci/config/my_api_key.pem
        pass_phrase=here_your_key_file_passphrase
        tenancy=ocid1.tenancy.oc1..aaaaaaaaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        region=eu-frankfurt-1

		ref: https://docs.cloud.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm

- Script parameters

        configfile = "/home/opc/.oci/config"
        prefix_file = ""                   #  To donwnload cost and usage files
        prefix_file = "reports/cost-csv"   #  To download cost only
        prefix_file = "reports/usage-csv"  #  To download usage only


- Prerequisites

        - Linux instance OL7+
        - Python 3.5+
        - python3 -m pip install --upgrade pip --user
        - python3 -m pip install --upgrade oci-cli --user
        - python3 -m pip install --upgrade oci --user
        - python3 -m pip install pandas --user
