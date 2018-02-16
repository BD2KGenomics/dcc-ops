## Overview
Parent tool for administrating redwood. You'll probably want to add _bin/redwood_ to your PATH.

See `redwood help` for more.

## Development
For the most part, you can add functionality by copying one of the existing files in _libexec_ into _libexec-newcommand_. Make sure to update the help comment at the top of the file--that gets printed in the `redwood help` output.

For more complicated changes, it might help to see [basecamp/sub](https://github.com/basecamp/sub), which this cli is based on.
