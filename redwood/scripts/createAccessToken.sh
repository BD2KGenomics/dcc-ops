#!/bin/bash
set -e

script_name=$(basename $0)

function help {
    cat <<EOF
Usage: ${script_name} [-a admin_password] [-m mgmt_password] [-s "scope1 scope2"] [-u username] [-hv]

Grant scopes and create an access token for a user

OPTIONS
  -a password for the auth-server admin user (default: secret)
  -h show this heplp message
  -m password for the auth-server mgmt user (default: pass)
  -s string of space-delimited scopes to granted (default: 'aws.DEV.upload aws.DEV.download')
  -u user name to be granted (default: testuser)
  -v show verbose output
EOF
}

admin_pass=secret
mgmt_pass=pass
scopes="aws.DEV.upload aws.DEV.download"
user=dev@gmail.com
verbose=0

while getopts ":ahm:s:u:v" opt; do
    case $opt in
        a)
            admin_pass=$OPTARG
            ;;
        h)
            help
            exit
            ;;
        m)
            mgmt_pass=$OPTARG
            ;;
        s)
            scopes="${OPTARG}"
            ;;
        u)
            user="${OPTARG}"
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

docker exec -it redwood-auth-server curl -XPUT "http://localhost:8543/admin/scopes/$user" -u admin:${admin_pass} -d"${scopes}"
token_output=$(docker exec -it redwood-auth-server curl http://localhost:8443/oauth/token -H "Accept: application/json" -dgrant_type=password -dusername="${user}" -dscope="${scopes}" -ddesc="test access token" -u mgmt:${mgmt_pass})
if [[ $verbose -eq 0 ]]
then echo $token_output | sed -e 's/^.*"access_token":"\([^"]*\)".*$/\1/'
else echo $token_output
fi
