# SOLMAT

## Install

1. Clone the project
2. Create a virtual environment in the project folder
3. Activate the virtual environment
4. Install the dependencies from packages.txt
5. Copy settings_example.py to settings.py
6. Set up database credentials in settings.py
7. Run the project with python manage.py runserver


## How to deploy

1. SSH into the server.
2. Backup the database
3. Activate the project's virtual environment
4. Pull the changes from the main branch
5. Run the migrations
6. Restart the server by running `touch soveh.ini` in the root folder where soveh.ini is located
# solmat_vehice
