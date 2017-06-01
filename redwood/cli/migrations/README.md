# redwood migrations
This directory is for redwood migration scripts, to be run via `redwood migrate`.

## Filenames
In order for `redwood migrate` to see the migration, filenames of the following format are expected:

    {auth|metadata}-migration-YYYY-MM-DD.{js|psql|sql}
    
The _YYYY-MM-DD_ is used to recommend all migrations whose dates are after the date of the backup from which redwood data was recovered, and only migrations whose prefixes match the above pattern will be considered. The migration should be more or less self-contained. This could use improvement.

## Migrations
Listing of specific migrations

### 2017-05-17
Adds `{access: controlled, projectCode: $p}` redwood metadata per record where $p is a project identifier obtained from the latest _mapping.csv_ in the _helper_ subdirectory to be associated with the mapped bundle id and to be used as its authorization group (projectCode foo requires aws.foo.download priviledge to download). The _helper/build_mapping.sh_ script builds a _mapping.csv_ from a copy of the dcc-metadata-indexer's _endpoint_metadata_ directory. This is a total hack.

Note: _mapping-2017-04-14.csv_ contains 3 lines that _mapping-2017-05-17_ wasn't generated with:
```
d0117ff1-cf53-43a0-aaab-cb15809fbb49,SU2C
d0117ff1-cf53-43a0-aaab-cb15809fbb49,Treehouse
efe617a1-ae1f-5592-b8d0-9b268d205938,Treehouse
```

I copy-pasted these into _mapping-2017-05-17_, which is otherwise a superset of the former.

There is also a _helper/blacklist-failed-uploads.csv_ which contains bundle-ids that were found to be missing from aws but present in the metadata backups. These will be deleted from the metadata-db.
