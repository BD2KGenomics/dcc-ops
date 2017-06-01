#!/usr/bin/env bash
set -e

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mappings="${dir}/helper/mapping-2017-05-17.csv ${dir}/helper/mapping-manual.csv"
blacklist=$(printf '['; cat ${dir}/helper/blacklist-failed-uploads.csv | xargs printf '"%s",' | sed 's/,$/\]/')

# create projects
if [[ -z ${_REDWOOD_ROOT} ]]; then
    echo 'not running within redwood cli: you need to manually run `redwood project create TREEHOUSE SU2C PROTECT_NBL`'
else
    echo "adding projects"
    "${_REDWOOD_ROOT}/bin/redwood" project create TREEHOUSE SU2C PROTECT_NBL
fi

function mapping_for() {
    program="$1"
    printf '["'; cat ${mappings} | grep -v '^#' | sort | uniq | grep "${program}" | cut -d, -f 1 | tr "\n" ',' | sed 's/,$//' | sed 's/,/","/g' | tr -d '\n'; printf '"]'
}

# json arrays of bundle_ids
treehouse_bundles="$(mapping_for Treehouse)"
wcdt_bundles="$(mapping_for SU2C)"
protect_bundles="$(mapping_for PROTECT_NBL)"
quake_bundles="$(mapping_for "Quake Brain scRNA-Seq")"
test_bundles="$(mapping_for "TEST")"
dev_bundles="$(mapping_for "DEV")"

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
    },
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${quake_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"Quake_Brain_scRNA-Seq"
              }
          }
      }
    },
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${test_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"TEST"
              }
          }
      }
    },
    { updateMany:
      {
          "filter": {
              gnosId: {
                  \$in: ${dev_bundles}
              }
          },
          "update": {
              \$set: {
                  projectCode:"DEV"
              }
          }
      }
    }
]);
db.Entity.deleteMany({
  _id: {\$in: ${blacklist}}
})
EOF

echo "running mongodb migration script ${tmpfile}"
docker cp "${tmpfile}" redwood-metadata-db:"${tmpfile}"
docker exec -i redwood-metadata-db mongo --norc "${tmpfile}"
# TODO: this will fail for redwood with external databases

echo Done
echo '`docker exec redwood-metadata-db mongo dcc-metadata --eval ''DBQuery.shellBatchSize = 10000; db.Entity.find({projectCode:"UNRESOLVED"})''` to see unresolved bundles. You still need to resolve these bundle programs manually.'
