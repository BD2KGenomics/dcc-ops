#!/usr/bin/env bash

#
# Build ./l{1|2|3|...}.mapping files for mapping bundle_ids to program names
#

# files stored here (use /tmp for non-dev)
prefix=/tmp

echo "bundle_id to program"
#find . -name metadata.json | pv | while read -r m; do jq -c 'select(.program != null) | {bundle_id: .specimen[].samples[].analysis[].bundle_uuid, program: .program}' "$m"; done | sort | uniq | jq -sr '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' >${prefix}/l1.csv

echo "sample_id to program"
#find . -name metadata.json | pv | while read -r m; do jq -c 'select(.program != null) | {sample_id: .specimen[].samples[].sample_uuid, program: .program}' "$m"; done | sort | uniq | jq -sr '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' >${prefix}/l2.csv

echo "sample bundle_id to parent sample_id"
#find . -name metadata.json | pv | while read -r m; do jq -c 'select(.parent_uuids != null) | {bundle_id: .bundle_uuid, sample_id: .parent_uuids[0]}' "$m"; done | sort | uniq | jq -sr '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' >${prefix}/l3.csv

echo "workflow_inputs bundle_id to parent sample_id"
#find . -name metadata.json | pv | while read -r m; do jq -c 'select(.parent_uuids != null and .workflow_inputs != null) | {bundle_id: .workflow_inputs[].file_storage_bundle_id, sample_id: .parent_uuids[0]}' "$m"; done | sort | uniq | jq -sr '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' >${prefix}/l4.csv

#.import l4.csv l4
#union
#select bundle_id, program from l2, l4 where l2.sample_id = l4.sample_id;

echo "load into sqlite"
rm ${prefix}/mapping
sqlite3 ${prefix}/mapping >mapping.csv <<EOF
.mode csv
.import l1.csv l1
.import l2.csv l2
.import l3.csv l3
select bundle_id, program from l1 union select bundle_id, program from l2, l3 where l2.sample_id = l3.sample_id;
EOF

# workflow outputs?
#
#union
#select bundle_id, program from l2, l3 where l2.sample_id = l3.sample_id

