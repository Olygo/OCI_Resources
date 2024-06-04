#!/usr/bin/bash
# Version: 1.0.0

# OCI API Reference and Endpoints 
# https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apiref.htm

# How to sign Oracle Cloud Infrastructure API requests reference
# https://docs.cloud.oracle.com/iaas/Content/API/Concepts/signingrequests.htm

# Object Storage Service API Endpoints reference
# https://docs.cloud.oracle.com/iaas/api/#/en/objectstorage/20160918/

# Object Storage Service ListObjects reference
# https://docs.cloud.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/ListObjects

# Object Storage Service GetObject reference
# https://docs.cloud.oracle.com/iaas/api/#/en/objectstorage/20160918/Object/GetObject

# Usage report uses the Object Storage API. 
# Reports are stored in the tenancy home region. 
# The object storage namespace used for the reports is < bling >; 
# the bucket name is the < tenancy OCID > .

# Prerequisites 
# before using this script, you must set up the authentication
# https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apisigningkey.htm

# Where to Get the Tenancy's OCID and User's OCID
# https://docs.cloud.oracle.com/iaas/Content/API/Concepts/apisigningkey.htm#Other

#####################
# Start Config Section
#####################

    namespace="bling" # DO NOT EDIT NAMESPACE
    bucketname="ocid1.tenancy.oc1..aaaaaaaaggjbti5dslmdmsldk56qshdjxqjlqk43g4fg3ha"
    UserId="ocid1.user.oc1..aaaaaaaa2lfslkfmlskdy2hj345nhymfg45l42lkqoe3bysflsyuau"
    keyFingerprint="05:1e:74:98:33:92:36:df:af:1f:b5:56:5f:31:4b:11"
    privateKeyPath="$HOME/.oci/OCI_API_KEY.pem"
    homeregion="eu-frankfurt-1"
    reportfolder="$HOME/MyReports/"

#####################
# Check if reportfolder exists, 
# if not found create it using mkdir
#####################

[ ! -d "${reportfolder}" ] && mkdir -p "${reportfolder}"
cd $reportfolder

#####################
# oci-curl function
#####################

function oci-curl {
    
    local tenancyId=${bucketname};
    local authUserId=${UserId};        
    local keyFingerprint=${keyFingerprint};
    local privateKeyPath=${privateKeyPath};

    local alg=rsa-sha256
    local sigVersion="1"
    local now="$(LC_ALL=C \date -u "+%a, %d %h %Y %H:%M:%S GMT")"
    local host=$1
    local method=$2
    local extra_args
    local keyId="$tenancyId/$authUserId/$keyFingerprint"
    
    case $method in
                
        "get" | "GET")
        local target=$3
        extra_args=("${@: 4}")
        local curl_method="GET";
        local request_method="get";
        ;;                
                
        "delete" | "DELETE")
        local target=$3
        extra_args=("${@: 4}")
        local curl_method="DELETE";
        local request_method="delete";
        ;;        
                
        "head" | "HEAD")
        local target=$3
        extra_args=("--head" "${@: 4}")
        local curl_method="HEAD";
        local request_method="head";
        ;;
                
        "post" | "POST")
        local body=$3
        local target=$4
        extra_args=("${@: 5}")
        local curl_method="POST";
        local request_method="post";
        local content_sha256="$(openssl dgst -binary -sha256 < $body | openssl enc -e -base64)";
        local content_type="application/json";
        local content_length="$(wc -c < $body | xargs)";
        ;;        
        
        "put" | "PUT")
        local body=$3
        local target=$4
        extra_args=("${@: 5}")
        local curl_method="PUT"
        local request_method="put"
        local content_sha256="$(openssl dgst -binary -sha256 < $body | openssl enc -e -base64)";
        local content_type="application/json";
        local content_length="$(wc -c < $body | xargs)";
        ;;                
        
        *) echo "invalid method"; return;;


esac

# This line will url encode all special characters in the request target except "/", "?", "=", and "&", since those characters are used 
# in the request target to indicate path and query string structure. If you need to encode any of "/", "?", "=", or "&", such as when
# used as part of a path value or query string key or value, you will need to do that yourself in the request target you pass in.

local escaped_target="$(echo $( rawurlencode "$target" ))"    
local request_target="(request-target): $request_method $escaped_target"
local date_header="date: $now"
local host_header="host: $host"
local content_sha256_header="x-content-sha256: $content_sha256"
local content_type_header="content-type: $content_type"
local content_length_header="content-length: $content_length"
local signing_string="$request_target\n$date_header\n$host_header"
local headers="(request-target) date host"
local curl_header_args
curl_header_args=(-H "$date_header")
local body_arg
body_arg=()
                
if [ "$curl_method" = "PUT" -o "$curl_method" = "POST" ]; then
    signing_string="$signing_string\n$content_sha256_header\n$content_type_header\n$content_length_header"
    headers=$headers" x-content-sha256 content-type content-length"
    curl_header_args=("${curl_header_args[@]}" -H "$content_sha256_header" -H "$content_type_header" -H "$content_length_header")
    body_arg=(--data-binary @${body})
fi
                
local sig=$(printf '%b' "$signing_string" | \
            openssl dgst -sha256 -sign $privateKeyPath | \
            openssl enc -e -base64 | tr -d '\n')

### $dl 
### is empty by defautlt => then the query with retrieve the .csv.gz Reports list.
### When the function is used to download the Reports, $dl add output => "-o filename"

curl ${dl} "${extra_args[@]}" "${body_arg[@]}" -X $curl_method -sS https://${host}${escaped_target} "${curl_header_args[@]}" \
    -H "Authorization: Signature version=\"$sigVersion\",keyId=\"$keyId\",algorithm=\"$alg\",headers=\"${headers}\",signature=\"$sig\""
}                
# url encode all special characters except "/", "?", "=", and "&"
function rawurlencode {
  local string="${1}"
  local strlen=${#string}
  local encoded=""
  local pos c o    

  for (( pos=0 ; pos<strlen ; pos++ )); do
    c=${string:$pos:1}
    case "$c" in
        [-_.~a-zA-Z0-9] | "/" | "?" | "=" | "&" ) o="${c}" ;;
        * )               printf -v o '%%%02x' "'$c"
    esac
    encoded+="${o}"
    done

    echo "${encoded}"
}

#####################
# Get reports list
#####################

dl=""       # $dl must be empty in order to retrieve Reports list (do not use "-o filename")

# Record reports list in reports.tmp
oci-curl objectstorage.${homeregion}.oraclecloud.com get "/n/${namespace}/b/${bucketname}/o" > ${reportfolder}reports.tmp

# Extract reports name
grep -o 'reports[^"]*' < ${reportfolder}reports.tmp > ${reportfolder}reports.lst
rm ${reportfolder}reports.tmp

#####################
# Parse & Download reports
#####################

    i=1;        # init counter
    while IFS= read -r line     # read file lines
        do
            filename=$"$line"
             # echo "filename " ${filename}
            shortname=$(echo ${filename} | sed -e "s/reports\/usage-csv\///g")   # Extract only filename
            
            dl=$"-o ${shortname}"     # set $dl in order to download Reports files (use "-o filename")
            echo "Report= " ${shortname}
            
            oci-curl objectstorage.${homeregion}.oraclecloud.com get "/n/${namespace}/b/${bucketname}/o/${filename}"        # download each report
            
            gunzip ${reportfolder}${shortname}       # unzip .gz files

            i=$((i+1));     # increase counter
            done < ${reportfolder}reports.lst     # read from file reports.lst

rm ${reportfolder}reports.lst