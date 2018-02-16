## Admin Tools
Admin Tools for managing Redwood

### Prerequisites
In order to the use the admin tools. You must have access to the root account of this machine. 

Then, make sure your machine has the following installed:
    
    -Python 2.7+
    -VirtualEnv
    -Pip

Finally, do the following steps to create the python virtual environment.
    
    1. Use VirtualEnv create a python virtual environment in the admin folder. (<dcc-ops dir>/redwood/cli/admin)
    2. Activate the virtual environment
    3. Use Pip and requirements.txt to install the python packages
    
### Setup
Before doing any admin tasks, first do the following,
    
    1. Login as root
    2. Active the virutual environment (if it's not already activated)

### Delete
For File Deletion, all you need to do is run delete.py in <dcc-ops dir>/redwood/cli/admin with the file uuid.

Example: `python delete.py 10101010-1212-2323-3434-454545454545`

For more detailed overview of the commands, use `python delete -h`
