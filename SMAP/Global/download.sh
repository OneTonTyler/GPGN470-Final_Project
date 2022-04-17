#!/bin/bash

GREP_OPTIONS=''

cookiejar=$(mktemp cookies.XXXXXXXXXX)
netrc=$(mktemp netrc.XXXXXXXXXX)
chmod 0600 "$cookiejar" "$netrc"
function finish {
  rm -rf "$cookiejar" "$netrc"
}

trap finish EXIT
WGETRC="$wgetrc"

prompt_credentials() {
    echo "Enter your Earthdata Login or other provider supplied credentials"
    read -p "Username (tylersingleton): " username
    username=${username:-tylersingleton}
    read -s -p "Password: " password
    echo "machine urs.earthdata.nasa.gov login $username password $password" >> $netrc
    echo
}

exit_with_error() {
    echo
    echo "Unable to Retrieve Data"
    echo
    echo $1
    echo
    echo "https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.09/SMAP_L3_SM_P_20190309_R18290_001.h5"
    echo
    exit 1
}

prompt_credentials
  detect_app_approval() {
    approved=`curl -s -b "$cookiejar" -c "$cookiejar" -L --max-redirs 5 --netrc-file "$netrc" https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.09/SMAP_L3_SM_P_20190309_R18290_001.h5 -w %{http_code} | tail  -1`
    if [ "$approved" -ne "302" ]; then
        # User didn't approve the app. Direct users to approve the app in URS
        exit_with_error "Please ensure that you have authorized the remote application by visiting the link below "
    fi
}

setup_auth_curl() {
    # Firstly, check if it require URS authentication
    status=$(curl -s -z "$(date)" -w %{http_code} https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.09/SMAP_L3_SM_P_20190309_R18290_001.h5 | tail -1)
    if [[ "$status" -ne "200" && "$status" -ne "304" ]]; then
        # URS authentication is required. Now further check if the application/remote service is approved.
        detect_app_approval
    fi
}

setup_auth_wget() {
    # The safest way to auth via curl is netrc. Note: there's no checking or feedback
    # if login is unsuccessful
    touch ~/.netrc
    chmod 0600 ~/.netrc
    credentials=$(grep 'machine urs.earthdata.nasa.gov' ~/.netrc)
    if [ -z "$credentials" ]; then
        cat "$netrc" >> ~/.netrc
    fi
}

fetch_urls() {
  if command -v curl >/dev/null 2>&1; then
      setup_auth_curl
      while read -r line; do
        # Get everything after the last '/'
        filename="${line##*/}"

        # Strip everything after '?'
        stripped_query_params="${filename%%\?*}"

        curl -f -b "$cookiejar" -c "$cookiejar" -L --netrc-file "$netrc" -g -o $stripped_query_params -- $line && echo || exit_with_error "Command failed with error. Please retrieve the data manually."
      done;
  elif command -v wget >/dev/null 2>&1; then
      # We can't use wget to poke provider server to get info whether or not URS was integrated without download at least one of the files.
      echo
      echo "WARNING: Can't find curl, use wget instead."
      echo "WARNING: Script may not correctly identify Earthdata Login integrations."
      echo
      setup_auth_wget
      while read -r line; do
        # Get everything after the last '/'
        filename="${line##*/}"

        # Strip everything after '?'
        stripped_query_params="${filename%%\?*}"

        wget --load-cookies "$cookiejar" --save-cookies "$cookiejar" --output-document $stripped_query_params --keep-session-cookies -- $line && echo || exit_with_error "Command failed with error. Please retrieve the data manually."
      done;
  else
      exit_with_error "Error: Could not find a command-line downloader.  Please install curl or wget"
  fi
}

fetch_urls <<'EDSCEOF'
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.09/SMAP_L3_SM_P_20190309_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.08/SMAP_L3_SM_P_20190308_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.07/SMAP_L3_SM_P_20190307_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.06/SMAP_L3_SM_P_20190306_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.05/SMAP_L3_SM_P_20190305_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.04/SMAP_L3_SM_P_20190304_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.03/SMAP_L3_SM_P_20190303_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.02/SMAP_L3_SM_P_20190302_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.03.01/SMAP_L3_SM_P_20190301_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.28/SMAP_L3_SM_P_20190228_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.27/SMAP_L3_SM_P_20190227_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.26/SMAP_L3_SM_P_20190226_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.25/SMAP_L3_SM_P_20190225_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.24/SMAP_L3_SM_P_20190224_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.23/SMAP_L3_SM_P_20190223_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.22/SMAP_L3_SM_P_20190222_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.21/SMAP_L3_SM_P_20190221_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.20/SMAP_L3_SM_P_20190220_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.19/SMAP_L3_SM_P_20190219_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.18/SMAP_L3_SM_P_20190218_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.17/SMAP_L3_SM_P_20190217_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.16/SMAP_L3_SM_P_20190216_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.15/SMAP_L3_SM_P_20190215_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.14/SMAP_L3_SM_P_20190214_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.13/SMAP_L3_SM_P_20190213_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.12/SMAP_L3_SM_P_20190212_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.11/SMAP_L3_SM_P_20190211_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.10/SMAP_L3_SM_P_20190210_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.09/SMAP_L3_SM_P_20190209_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.08/SMAP_L3_SM_P_20190208_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.07/SMAP_L3_SM_P_20190207_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.06/SMAP_L3_SM_P_20190206_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.05/SMAP_L3_SM_P_20190205_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.04/SMAP_L3_SM_P_20190204_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.03/SMAP_L3_SM_P_20190203_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.02/SMAP_L3_SM_P_20190202_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.02.01/SMAP_L3_SM_P_20190201_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.31/SMAP_L3_SM_P_20190131_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.30/SMAP_L3_SM_P_20190130_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.29/SMAP_L3_SM_P_20190129_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.28/SMAP_L3_SM_P_20190128_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.27/SMAP_L3_SM_P_20190127_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.26/SMAP_L3_SM_P_20190126_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.25/SMAP_L3_SM_P_20190125_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.24/SMAP_L3_SM_P_20190124_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.23/SMAP_L3_SM_P_20190123_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.22/SMAP_L3_SM_P_20190122_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.21/SMAP_L3_SM_P_20190121_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.20/SMAP_L3_SM_P_20190120_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.19/SMAP_L3_SM_P_20190119_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.18/SMAP_L3_SM_P_20190118_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.17/SMAP_L3_SM_P_20190117_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.16/SMAP_L3_SM_P_20190116_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.15/SMAP_L3_SM_P_20190115_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.14/SMAP_L3_SM_P_20190114_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.13/SMAP_L3_SM_P_20190113_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.12/SMAP_L3_SM_P_20190112_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.11/SMAP_L3_SM_P_20190111_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.10/SMAP_L3_SM_P_20190110_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.09/SMAP_L3_SM_P_20190109_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.08/SMAP_L3_SM_P_20190108_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.07/SMAP_L3_SM_P_20190107_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.06/SMAP_L3_SM_P_20190106_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.05/SMAP_L3_SM_P_20190105_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.04/SMAP_L3_SM_P_20190104_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.03/SMAP_L3_SM_P_20190103_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.02/SMAP_L3_SM_P_20190102_R18290_001.h5
https://n5eil01u.ecs.nsidc.org/DP4/SMAP/SPL3SMP.008/2019.01.01/SMAP_L3_SM_P_20190101_R18290_001.h5
EDSCEOF