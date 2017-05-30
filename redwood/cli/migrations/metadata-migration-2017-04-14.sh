#!/usr/bin/env bash
set -e

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mapping="${dir}/helper/mapping.csv"

# create projects
if [[ -z ${_REDWOOD_ROOT} ]]; then
    echo 'not running within redwood cli: you need to manually run `redwood project create TREEHOUSE SU2C PROTECT_NBL`'
else
    echo "adding projects"
    "${_REDWOOD_ROOT}/bin/redwood" project create TREEHOUSE SU2C PROTECT_NBL
fi

function mapping_for() {
    program="$1"
    printf '["'; cat "${mapping}" | grep "${program}" | cut -d, -f 1 | tr "\n" ',' | sed 's/,$//' | sed 's/,/","/g' | tr -d '\n'; printf '"]'
}

# json arrays of bundle_ids
treehouse_bundles="$(mapping_for Treehouse)"
wcdt_bundles="$(mapping_for SU2C)"
protect_bundles="$(mapping_for PROTECT_NBL)"

# write migration.js
tmpfile="/tmp/migration`date +%Y-%m-%d_%H-%M-%S`.js"
cat >"${tmpfile}" <<EOF
conn = new Mongo();
db = conn.getDB("dcc-metadata");
db.Entity.update(
    {},
    { \$set:
      {
          access:"controlled",
          projectCode:"UNRESOLVED"
      }
    },
    { multi: true }
);
db.Entity.bulkWrite([
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${treehouse_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"Treehouse"
              }
          }
      }
    },
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${wcdt_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"SU2C"
              }
          }
      }
    },
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${protect_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"PROTECT_NBL"
              }
          }
      }
    }
])
EOF

echo "running mongodb migration script ${tmpfile}"
docker cp "${tmpfile}" redwood-metadata-db:"${tmpfile}"
docker exec -i redwood-metadata-db mongo --norc --quiet "${tmpfile}"
# TODO: this will fail for redwood with external databases

echo done!
echo '`echo "DBQuery.shellBatchSize = 10000; db.Entity.find({projectCode:\"UNRESOLVED\"})" | docker exec -i redwood-metadata-db mongo dcc-metadata` to see unresolved bundles. You still need to resolve these bundle programs manually.'
