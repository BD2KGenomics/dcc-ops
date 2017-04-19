#!/usr/bin/env bash
set -e

#"${_REDWOOD_ROOT}/bin/redwood" project create TREEHOUSE SU2C PROTECT_NBL

docker exec -i redwood-metadata-db mongo --norc --quiet <<EOF
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
)
EOF
echo done
