"The Junk Drawer" -  An Item Catalog
by Daniel Ferguson 09/02/2015

This is a web app that provides an editable item catalog with authentication.

Modules and Frameworks Used:
  standard library
  flask
  sqlalchemy
  werkzeug
  requests
  httplib2
  oauth2
  Bootstrap
  

To run this project you must have git, virtualbox and vagrant installed. The
project uses a virtual machine (VM) to run the database and python code. You
must also be connected to the internet in order for vagrant to obtain and 
update the vm image. When the virtual machine starts it automatically creates
the database and tables needed for the project.

Additionally, you will also need to supply your own secret keys to enable 
Google and Facebook authentication. Instructions on how to setup an account 
and obtain these keys may be found online.

To enable FaceBook Authentication:
1. Populate the "app_id" and "app_secret" variables in the file
    "client_secrets_facebook.json" with your values. An example is included.

To enable Google Authentication:
1. Populate the "client_id" and "client_secret" variables in the file
    "client_secrets_google.json" with your values. An example is included.

To enable single user mode and ignore authentication:
1. Set DEV_MODE = True in the file "project.py".

Perform the following steps to start the application:
1. Extract the project files.
2. Open git and navigate to the item-catalog folder.
3. Type "vagrant up" to turn on the VM.
4. Type "vagrant ssh" to connect to the VM.
5. Type "cd /vagrant" to browse to the project folder.
6. Run "python project.py" to start a local web server.
7. You should see the following output followed by a blank line:
	 * Running on http://0.0.0.0:5000/
	 * Restarting with reloader

8. To connect to the web app, open a browser to localhost:5000
9. You should now see the catalog home page showing a list of categories.
10. To kill the web app, type Ctrl + C. This will return you to the VM prompt.
11. To exit the VM, type "exit".
12. To shut down the VM, type "vagrant halt".
