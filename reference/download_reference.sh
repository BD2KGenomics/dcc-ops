#!/bin/bash
set -e
echo "Downloading Reference files to /home/ubuntu/dcc-ops/reference/samples"

mkdir /home/ubuntu/dcc-ops/reference/samples

wget -P /home/ubuntu/dcc-ops/reference/samples/ https://s3.amazonaws.com/oconnor-test-bucket/sample-data/rsem_ref_hg38_no_alt.tar.gz
wget -P /home/ubuntu/dcc-ops/reference/samples/ https://s3.amazonaws.com/oconnor-test-bucket/sample-data/starIndex_hg38_no_alt.tar.gz
wget -P /home/ubuntu/dcc-ops/reference/samples/ https://s3.amazonaws.com/oconnor-test-bucket/sample-data/kallisto_hg38.idx

echo "You can find the reference files under /home/ubuntu/dcc-ops/reference/ ; run the core client using the manifest.tsv under /home/ubuntu/dcc-ops/reference/"
