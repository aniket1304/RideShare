---- Working on AWS ----

Create 3 instances (Ubuntu 18.04) for Users, Rides and Orchestrator respectively.

Add security group "Type : Custom TCP - Protocol : TCP - Port range : 80 - Source : Anywhere  0.0.0.0/0"

Assign elastic IP to orchestrator.

Modify ride.py and user.py - replace IP address of the orchestrator with the freshly assigned IP.

Install docker and docker-compose on each instance - https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04 https://docs.docker.com/compose/install/

Upload Ride folder, User Folder and Orchestrator folder to their respective instances.

Create two target groups for Rides and Users repectively using AWS.

Create a load balancer with Ride target group as default.

Add a listner rule - "if path is api/v1/users* then forward to User target group.

In orchestrator instance, build a docker image.

Build docker image on other two instances.

Use POSTMAN along with DNS of load balancer for testing.

Enjoy your Application.
