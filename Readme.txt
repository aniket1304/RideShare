---- Working on AWS ----

1. Create 3 instances (Ubuntu 18.04) for Users, Rides and Orchestrator respectively.

2. Assign elastic IP to orchestrator.

3. Modify ride.py and user.py - replace IP address of the orchestrator with the freshly assigned IP.

4. Install docker and docker-compose on each instance.

5. Upload Ride folder, User Folder and Orchestrator folder to their respective instances.

6. Create two target groups for Rides and Users repectively using AWS.

7. Create a load balancer with Ride target group as default.

8. Add a listner rule - "if path is api/v1/users* then forward to User target group.

9. In orchestrator instance, build a docker image.

10. Build docker image on other two instances.

11. Use POSTMAN along with DNS of load balancer for testing.

12. Enjoy your Application.