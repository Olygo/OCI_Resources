#!/bin/sh

# ===================
# initialize counter
# ===================

time=$(date +%s)

# ======================
# ask identity to user
# ======================

identity() {
    echo
    echo "========================================================================"
    echo " Welcome to OCI-Classic Storage Download & Delete, please authenticate "
    echo "========================================================================"
    echo
    read -p 'What is the name of your Domain/Tenancy ? ' mydomain
    echo
    read -p 'What is your username or Email address ? ' myusername
    echo
    read -rs -p 'What is the corresponding password ?' secret
    echo
    echo
    read -p 'What is the name of the container (case sensitive) ? ' container
    echo

    # ====================
    # lowercase variables
    # ====================

    domain=$(echo "$mydomain" | sed 'y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/')     
    username=$(echo "$myusername" | sed 'y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/')    

    # ===============
    # call cloudauth
    # ===============

    cloudauth
    }

# ===============
# get Auth-token
# ===============

cloudauth() {
  auth=$(curl -v -s -X GET -H "X-Storage-User:Storage-${domain}:${username}" -H "X-Storage-Pass:${secret}" https://${domain}.eu.storage.oraclecloud.com/auth/v1.0 --stderr -)

  	if grep -sq '< HTTP/1.1 200 OK' <<< "$auth"                                     # check if the user has been identified
        
        then
            echo
            echo -e "\033[44mSuccessfully authenticated\033[0m"
            echo
	        token=$(echo "$auth" | grep -i '^< X-Auth-Token:' | cut -b 3-)          # extract X-Auth-token from $auth
	        echo -e "\033[33mYour Token-Auth is" "$token\033[0m"
	        echo
            echo -e "\033[45mYou are processing container" "$container\033[0m"
            echo
            show_menu
    else
        echo
        echo
        echo -e "\033[41mUnable to authenticate, please verify your domain Name, username and Password\033[0m"
        echo
        identity
    fi
    
    }
# ========================================================================================================
# refreshcloudauth is used to update token in order to avoid token expiration
# ========================================================================================================

refreshcloudauth() {
      echo "Entering Refresh token..."
      time=$(date +%s) # reset count value
      echo "new count after refresh is:" "$time"
      echo -e "\033[33mYour Token-Auth is " "$token\033[0m"
      auth=""
      auth=$(curl -v -s -X GET -H "X-Storage-User:Storage-${domain}:${username}" -H "X-Storage-Pass:${secret}" https://${domain}.eu.storage.oraclecloud.com/auth/v1.0 --stderr -)
      token=$(echo "$auth" | grep -i '^< X-Auth-Token:' | cut -b 3-)                 # extract X-Auth-token from $auth
      echo -e "\033[33mNew Auth-token is" "$token\033[0m"

	  echo
      echo "opt=" "$opt" 
      if [[ $opt = 1 ]] ;       
                        then
                           echo "Back to Download..."
                           download                    # if opt=1, user wants to download
                        else 
                            if [[ $opt = 2 ]] ; 
                                then
                                echo "Back to Delete..."
                                    delete                      # if opt=2, user wants to delete
                            else
                                echo "Back to Menu..."
                                show_menu
                            fi
                    fi

}


# ==============
# download files
# ==============

download() {

    # =============================================
    # check counter history using time comparaison
    # =============================================
    timenow=$(date +%s)
    echo
    echo "previous time is " "$time" 
    echo "time now is:" "$timenow"

    time3=$(($time+180))
    echo "time+180:" "$time3"
    if (( $time3 < $timenow )); then
    echo "Need to refresh your token..."
    refreshcloudauth
    fi

    # =======================================================
    # create dynamic folder with container name + timestamp
    # =======================================================

    foldername=$(date +%Y%m%d_%H-%M)
    foldername=$container'_'$foldername
    echo
    echo -e "\033[45mYour files will be saved in" "$foldername\033[0m"
    echo
    mkdir -p  "$foldername"

    # =======================================================
    # List container's files and write output to a variable
    # =======================================================

	files=$(curl --get -H "${token}" https://${domain}.eu.storage.oraclecloud.com/v1/Storage-${domain}/${container})
    if grep -sq 'Container Metadata Not Found' <<< "$files"                             # if container is not found...
    then
    echo
    echo  -e "\033[33;5mUnable to find container\033[0m" "\033[33;5m$container\033[0m"
    echo
    read -p 'What is the name of the container ? ' container                          # ...ask again for container name
    download
    fi

	echo "$files" > files                       # Write files in a temp file in order to parse filename
	cat files | sed -e 's/ /%20/g' > files2     # Replace Spaces with %20 to avoid cURL issues

	for i in $(cat files2) ; do
        o=$(echo "$i" | sed "s/%20/ /g")        # Replace %20 with Spaces in output filenames
        echo "$o"
        curl --get -H "${token}" -o "./"$foldername"/$o" https://${domain}.eu.storage.oraclecloud.com/v1/Storage-${domain}/${container}/$i	
    done
        rm files files2
    echo
    echo -e "\033[45m$container" "objects have been downloaded in" "$foldername\033[0m"
    echo
    show_menu
    }

# =============
# delete files
# =============

delete() {

    # ==============================================================================================
    # counter allows to renew Auth-token in order to avoid token expiration
    # ==============================================================================================
    echo
    echo "time now is:" "$timenow"

    if (( $time+180 < $timenow )); then
    echo "Need to refresh your token..."
    refreshcloudauth
    fi


    # ========================================
	# List container's files and write output
    # ========================================

	files=$(curl --get -H "${token}" https://${domain}.eu.storage.oraclecloud.com/v1/Storage-${domain}/${container})

    if grep -sq 'Container Metadata Not Found' <<< "$files"                             # if container is not found...
    then
    echo  -e "\033[33;5mUnable to find container\033[0m" "\033[33;5m$container\033[0m"
    read -p 'What is the name of the container ? ' mycontainer                          # ...ask again for container name
    container=$(echo "$mycontainer" | sed 'y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/')  # lowercase containername
    delete
    fi

	echo "$files" > files                                       # Write files in a temp file in order to parse filename
	cat files | sed -e 's/ /%20/g' > files2                     # Replace Spaces with %20 to avoid cURL issues

	for i in $(cat files2) ; do
    	echo "$i"
        curl -X DELETE -H "${token}" https://${domain}.eu.storage.oraclecloud.com/v1/Storage-${domain}/${container}/$i
	done
    rm files files2
    echo
    echo -e "\033[45m$container" "objects have been deleted\033[0m"
    echo
    show_menu
    }

# =============================
# work with another container
# =============================

changecontainer() {
    read -p 'What is the name of the container ? ' mycontainer                          # ...ask for container name
    container=$(echo "$mycontainer" | sed 'y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/')  # lowercase containername
    echo
    echo -e "\033[45mYou are now processing container" "$container\033[0m"
    echo
    show_menu
}

# ============
# Launch Menu
# ============

show_menu(){   
        echo
        echo -e "\033[32m==================\033[0m"
        echo -e "\033[32m Select an option \033[0m"
        echo -e "\033[32m==================\033[0m"
        echo 
        echo ""
        echo -e "\033[32m 1. Download objects \033[0m"
        echo -e "\033[32m 2. Delete objects \033[0m"
        echo -e "\033[32m 3. Process another container \033[0m"
        echo -e "\033[32m 4. Exit \033[0m"
        echo
        read -n 1 -p " Choice [1-4] ? " opt
        echo
        choice
}
    # =================
	# Check user input 
    # =================

choice() {
    if [[ $opt = 4 ]] ;       
    then 
    clear
    exit
    elif [[ $opt = 3 ]] ;       
    then 
    changecontainer
    elif [[ $opt = 2 ]] ; 
    then
    delete                      
    elif [[ $opt = 1 ]] ;       
    then
    download
    else
    show_menu
    fi }

# ==================================================
# start here: Clear screen, authenticate & show menu
# ==================================================

clear
identity
show_menu