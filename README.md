Python3 and boto3 must be installed. (I use `pip3 install boto3`).

Use a command like this to create the stack(s):

`python3 ./install-replen.py replen password`

In the above `replen` will be used to name the cloud formation stacks and the aurora cluster.  It will also be the database name and username for the database in the aurora cluster.  `password` will be the password for the database.

This will create 
1. A VPC with 2 public subnets and 2 private subnets in the Oregon region (us-west-2).  
2. A serverless aurora instance in one of the private subnets.  This instance will shut down after 5 minutes of disuse, but will "wake up" again when something connects to.
3. A bastion host/web server running amazon linux in a public subnet.

The script also prints out the IP address of the bastion host. 

You can connect to the bastion host using an ssh command like this

`ssh -i replen-server.pem ec2-user@<ip-address>`.

On that host 
* There is a `connect-aurora.sh` script for connecting to the database.  
* The web server files are in /var/web/html.  
* You can become root with "sudo su - root"


You will need to change the hostname replen.io to match the IP address of the web server.
