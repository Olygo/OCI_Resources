# OCI get_report.py
 Use get_report.py to download and extract OCI report locally.

# Prerequisites 

before using this script, you must set up OCI-CLI
https://docs.cloud.oracle.com/iaas/Content/API/SDKDocs/cliinstall.htm
 
# OCI get_report.sh

 get_report.sh will authenticate to your API Endpoint and will download all reports locally.

To download a usage report, use the Object Storage APIs. 
The reports are stored in the tenancy's home region. 
The object storage namespace used for the reports is bling; the bucket name is the tenancy OCID.

# Prerequisites 

before using this script, you must set up the authentication
https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apisigningkey.htm

 Where to Get the Tenancy's OCID and User's OCID
 https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apisigningkey.htm#Other

 Set your own Variables such as 

    namespace="bling"
    bucketname="ocid1.tenancy.oc1..aaaaaaaaggjbti5jkqshdk56qshdjxqsdkjlqk43g4fg3ha"
    UserId="ocid1.user.oc1..aaaaaaaa2lskdy27rjjdfghj345nhymfg45l42lkqoe3bysflsyuau"
    keyFingerprint="05:1e:74:98:33:92:56:ef:eb:5d:a0:67:9e:11:7b:23"
    privateKeyPath="$HOME/.oci/OCI_API_KEY.pem"
    homeregion="eu-frankfurt-1"
    reportfolder="$HOME/MyReports/"