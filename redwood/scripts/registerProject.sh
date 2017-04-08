#!/bin/bash
set -e
script_name=$(basename $0)

function help {
    cat <<EOF
Usage: ${script_name} [-s "site"] [-hv] PROJECT...

Register new projects to be managed by the mgmt client

OPTIONS
  -h show this help message
  -s site where project code is to be used (e.g. aws)
  -v verbose output
EOF
}

project=DEV
site=aws
verbose=0

while getopts ":hs:v" opt; do
    case $opt in
        h)
            help
            exit
            ;;
        s)
            site="${OPTARG}"
            ;;
        v)
            set -x
            verbose=1
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done
shift "$((OPTIND - 1))"

for project in "$@"; do
    sudo docker exec -it redwood-auth-db psql -d dcc -U dcc_auth -c "update oauth_client_details set scope = '${site}.${project}.upload,${site}.${project}.download,' || scope where client_id='mgmt';"
done
