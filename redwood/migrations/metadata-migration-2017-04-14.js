// connection
conn = new Mongo();
db = conn.getDB("dcc-metadata");

// update
db.Entity.updateMany({}, {$set:{access:"controlled"}}, {})
db.Entity.updateMany({}, {$set:{projectCode:"DEV"}}, {})
