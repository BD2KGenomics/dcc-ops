# redwood migrations
This directory is for redwood migration scripts, to be run via `redwood recover` or directly with `redwood migrate`.

## Filenames
In order for `redwood recover` to see the migration, filenames of the following format are expected:

    {auth|metadata}-backup-YYYY-MM-DD.{js|psql|sql}
    
The _YYYY-MM-DD_ is used to recommend all migrations whose dates are after the date of the backup from which redwood data was recovered, and only migrations whose prefixes match the above pattern will be considered.
