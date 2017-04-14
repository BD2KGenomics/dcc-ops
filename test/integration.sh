#!/usr/bin/env bash
source $(dirname $( realpath ${BASH_SOURCE[0]} ) )/lib/b-log.sh

function check_setup {
    [[ $(sudo docker ps | tail -n +2 | wc -l) -ge 8 ]] || (echo "the required docker containers don't seem to be running" && exit 1)
    # TODO count number of dashboard containers
    # TODO more rigorous checking
}

function main {
    check_setup
    cd "$(dirname "${BASH_SOURCE[0]}")"
    LOG_LEVEL_ALL

    [[ -d outputs ]] && sudo rm -rf outputs && INFO "deleted old outputs"
    
    access_token=$(../redwood/admin/bin/redwood token create)
    INFO "generated testing access token: ${access_token}"

    redwood_endpoint=$(cat ../redwood/.env | grep 'base_url=' | sed 's/[^=]*=//')
    INFO "got redwood endpoint from dcc-ops/redwood/.env: ${redwood_endpoint}"

    INFO "doing upload with $(pwd)/manifest.tsv"
    sudo docker run --rm -it -e ACCESS_TOKEN=${access_token} -e REDWOOD_ENDPOINT=${redwood_endpoint} \
         -v $(pwd)/manifest.tsv:/dcc/manifest.tsv -v $(pwd)/samples:/samples -v $(pwd)/outputs:/outputs \
         quay.io/ucsc_cgl/core-client:1.1.0-alpha spinnaker-upload --force-upload /dcc/manifest.tsv

    object_id=$(cat outputs/receipt.tsv | tail -n +3 | head -n 1 | cut -f 20)
    bundle_id=$(cat outputs/receipt.tsv | tail -n +3 | head -n 1 | cut -f 19)
    INFO "the uploaded bundle with id ${bundle_id} has metadata.json with object id ${object_id}"

    INFO "downloading metadata.json with object id ${object_id}"
    sudo mkdir outputs/test_download
    sudo docker run --rm -it -e ACCESS_TOKEN=${access_token} -e REDWOOD_ENDPOINT=${redwood_endpoint} \
         -v $(pwd)/outputs:/outputs quay.io/ucsc_cgl/core-client:1.1.0-alpha download ${object_id} /outputs/test_download

    [[ ! -f outputs/test_download/${bundle_id}/metadata.json ]] && printf "%s: no such file" "outputs/test_download/${bundle_id}/metadata.json" | FATAL && exit 1

    sudo rm -rf outputs

    # TODO: run indexer, etc.
    
    INFO "TEST SUCCESS"
}

main "$@"
