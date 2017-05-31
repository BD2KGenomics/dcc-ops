README
======

this readme is a scripting guide


all indexer 404s are UNRESOLVED
-------------------------------

404 indexer object ids::
  docker exec -it boardwalk_dcc-metadata-indexer_1 cat metadata_indexer_v2.log | grep -I error | grep -v "Please check" | grep java | sed -E 's/.*(\{.*\}).*/\1/' | jq -s .[].message | sed -E 's/"(.*)"/\1/' > indexer404.txt

look up all indexer object ids in metadata-db::
  cat indexer404.txt | while read id; do echo "db.Entity.find({_id: \"${id}\"}, {projectCode: 1})"; done | docker exec -i redwood-metadata-db mongo dcc-metadata --quiet | jq -s .[].projectCode


some UNRESOLVED files are in s3
---------------------------------

get all UNRESOLVED records::
  docker exec -i redwood-metadata-db mongo dcc-metadata --quiet --eval 'DBQuery.shellBatchSize = 30000; db.Entity.find({projectCode: "UNRESOLVED"}, {gnosId: 1, fileName: 1})' | tee unresolved.txt

get all UNRESOLVED object ids::
  cat unresolved.txt | jq -s .[]._id | sed -E 's/"(.*)"/\1/' | sort | uniq | tee unresolved-ids.txt

get all UNRESOLVED filenames::
  cat unresolved.txt | jq -s .[].fileName | sed -E 's/"(.*)"/\1/' | sort | uniq | tee unresolved-files.txt

look up unresolved objects on aws::
  cat unresolved.txt | jq -s .[]._id | sed -E 's/"(.*)"/\1/' | while read id; do aws s3 ls s3://redwood-2.0.1/data/${id}; done | grep -v '.meta$' | awk '{print $4}' | sort | uniq | tee aws-unresolved.txt

see which object ids are not in s3 and UNRESOLVED::
  diff -y --suppress-common-lines unresolved-ids.txt aws-unresolved.txt

see which object ids are in s3 but still UNRESOLVED::
  diff -y --left-column unresolved-ids.txt aws-unresolved.txt | grep -v '<'

look up filenames of all aws-unresolved object ids in metadata-db::
  cat aws-unresolved.txt | while read id; do echo "db.Entity.find({_id: \"${id}\"}, {fileName: 1})"; done | docker exec -i redwood-metadata-db mongo dcc-metadata --quiet | jq -s .[].fileName | sed 's/"//g' | tee aws-unresolved.files.txt
  paste aws-unresolved.txt aws-unresolved.files.txt





Download each UNRESOLVED metadata.json:
---------------------------------------
This is a separate flow from the above. First::
  mkdir data

get all UNRESOLVED metadata.json::
  docker exec -i redwood-metadata-db mongo dcc-metadata --quiet --eval 'DBQuery.shellBatchSize = 30000; db.Entity.find({fileName: "metadata.json", projectCode: "UNRESOLVED"}, {gnosId: 1, fileName: 1})' | jq -s .[]._id | sed -E 's/"(.*)"/\1/' | tee unresolved-metadata-ids.json

download them::
  cat unresolved-metadata-ids.json | xargs printf 'download %s /dcc/data\n' | docker run --rm -i -e ACCESS_TOKEN=b5f29c2b-cc96-4f6d-b017-408242ffbfad -e REDWOOD_ENDPOINT=storage.ucsc-cgl.org -v `pwd`/data:/dcc/data quay.io/ucsc_cgl/core-client:1.0.4 bash | tee download.log

find the gnosIds of all metadata.json with program TEST and DEV (cd ./data first) and output mapping lines::
  grep -r '"program": "TEST",' * | cut -d: -f 1 | while read f; do echo "$(dirname "${f}")"; done | sed -E 's/(.*)/\1,TEST/'
  grep -r '"program": "DEV",' * | cut -d: -f 1 | while read f; do echo "$(dirname "${f}")"; done | sed -E 's/(.*)/\1,DEV/'

get the other gnosIds: TODO - actually hunt these down::
  grep -cr '"program": ".*",' * | grep :0 | cut -d/ -f 1


get the download failed object ids::
  cat download.log | grep 'Storage client error' | sed -E 's/.*(\{.*\})/\1/' | jq -s .[].message | sed 's/"//g'
