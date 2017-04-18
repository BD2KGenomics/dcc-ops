#!/usr/bin/env bash
set -e

#"${_REDWOOD_ROOT}/bin/redwood" project create TREEHOUSE SU2C PROTECT_NBL

docker exec -i redwood-metadata-db mongo --norc --quiet dcc-metadata <<EOF
conn = new Mongo();
db = conn.getDB("dcc-metadata");
db.Entity.updateMany({}, {$set:{access:"controlled"}}, {})
db.Entity.updateMany({}, {$set:{projectCode:"DEV"}}, {})
EOF
echo done
