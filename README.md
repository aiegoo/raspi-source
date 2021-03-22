# raspi-source
I was playing around with updates last night - just a little bit too much from what it seems, causing the disaster — all nodes suddenly stopped detecting network interfaces, and it was impossible to recover. Article published on Pi Day ( 14/03 ) with all-you-can-eat code attached ( at the end ).

My Home Raspberry Pi Kubernetes cluster ( credit to my wife for putting up with it )
As my pet cluster grew to six nodes in total (thanks to my wife, who knows that the best thing for my birthday is a pie, RaspberryPi), I’ve had a choice — start from the beginning following my own article on setting up the Kubernetes cluster on Raspberry Pi, or do it the DevOps and SRE way — fully automate potential rebuild and cluster management.
This article results from the direct enhancement of my previous one, Building Your Home Raspberry PI Kubernetes Cluster.

Human vs Machine | Credit: comfreak at pixabay
Time and effort thoughts
I’ve had two options at that time, and I thought them through on my way to bed. Both of them were time-consuming.
Approach #1:
Wake up early and rebuild things manually following my own article (sic!) and maybe find some room for improvements. This method, as I’ve proven to myself quite a few times, is prone to errors and mistakes, mostly typos or skipping one or two steps, then trying to figure out what on earth happened for the next half an hour, to wipe everything out and start from the beginning over and over again. I’ve done this a few times already, but after all, one more time, never hurt anyone.
Approach #2:
Wake up early and start coding from scratch; the ultimate solution to help me this time is to do it once and use it forever. Make the whole cluster rebuild and production as easy to reproduce as possible. It will, of course, mean more downtime. However, its benefits will be long-standing ones, allowing me to not worry about the cluster itself and finally treat it as a stable solution towards which I can migrate my whole home infrastructure.
Automation saga begins
Before commencing any work, I focused on the basics of the basics and established a few principles I followed during the whole process. This created a bit opinionated environment, but with plenty of logical separation in code between parts, so it should be a bit easier for you, dear reader, to change any parts of the code or comment out whole files to disable few features here and there.
Principle #1: Setting up the Kubernetes cluster on Raspberry Pi can be divided into three parts. Setting up the memory card, the nodes' configuration on the system level and finally — spinning up Kubernetes resources.
Principle #2: There’s an NFS server running on my old Intel NUC, connected to the DROBO storage. It would be nice to utilise it as permanent, shared storage for all the nodes.
Principle #3: Raspberry Pi cluster runs in my home network, within its own VLAN, hence why securing it is not my priority, and all the services together with nodes should be accessible easily, without the need for juggling with credentials.
With those in mind, I managed to sit down and started working on coding this little Frankenstein. To reproduce results ( or make it work ), you will need:
Mac ( for the card formatting part ), I may update the script with platform detection later when I have time to install the Linux VM.
Ansible ( I’m running it on 2.10.6 )
Terraform ( written in 0.13.4, works with 0.14.8 as well )
Make, which will be useful for all the runs to not fiddle with parameters
rPi cluster: Step 1
Raspberry Pi uses a memory card as its hard drive. This may not be optimal and definitely won’t give you the greatest speeds on reading and writing operations, but it should be sufficient for the playground and hobby projects.
What does step 1 take care of?
Formats memory card
Divides memory card into two partitions — 1GB + rest of the memory card
Copies the Alpine Linux image onto the memory card
Creates system overlay
System overlay takes care of setting up the eth0 in promisc mode ( necessary for the MetalLB ) and allowing the SSH connection to your Raspberry Pi hosts with no password.
Important: Check the source of 001-prepare-card.shand make sure that the memory card you just inserted is actually /dev/disk5 otherwise, you may lose data.
Result: Preparing 6 memory cards takes about a minute.
rPi cluster: Step 2
That’s the step where the real fun begins. I presume you have inserted memory cards into your Raspberry Pis, connected all the cables ( network and power ) and allowed them to boot? You will need to obtain your devices' IP addresses now — you can do it either by connecting the screen to each of them and executing ifconfig eth0 or log in to your router and check there. Adjust the pi-hosts.txt with appropriate values.

Important: Few things down the road may require the pi0 hostname.
Add the following to your ~/.ssh/config file, forcing connection as a root to all the pi* hosts.
Host pi?
  User root
  Hostname %h.local
As we have our micro machines ( yes, I am that old ) ready, we need to prepare them for the Ansible run. You can do it easily with 001-prepare-ansible.sh script, which will ssh into every server specified in the pi-hosts file, configure the chrony for NTP and install Python interpreter.
Important: You may want to check the rpi.yaml file and adjust the vars section to your needs. I definitely would.
After this step succeeds, you can perform the Ansible run ansible-playbook rpi.yaml -f 10 which will take care of the following and in order:
COMMON:
Installs necessary packages
Partitions and formats the RPI memory card
Sets up the “bigger” partition as the system disk
Adds all the fstab entries
Commits changes
Restarts the Pi to boot from the “permanent” partition
KUBEMASTER:
Sets up a master node using kubeadm
Stores your token locally ( in static/token_file )
Sets up the root user on the Pi with access to kubectl
Saves the Kubernetes config locally ( in static/kubectl.conf )
KUBEWORKER:
Copies token to the workers' nodes
It makes the workers join your master, with the token file
Copies the kubectl.conf to workers root user
BASIC:
Removes the taint from the master, allowing it to participate in workloads
Installs py3-pip, PyYaml and helm on the nodes
If you are still reading — congratulations — you just ended up with the basic Kubernetes cluster, which does nothing and requires a bit of love. It was as easy as executing few scripts and waiting for them to finish, I believe and definitely nicer than the manual approach.
Important: You can run it as many times as you want. There’s no re-formatting of your memory cards after it’s done once.
Result: Preparing 6 nodes with basic Kubernetes install takes about a minute or two, depending on your internet connection.
rPi cluster: Step 3
After successfully executing the previous two steps, you should have the cluster of Pi’s ready for the first deployments. There are few basic setup steps required to make it work as desired, but guess what… They are AUTOMATED as well and let the Terraform take care of it.
Let’s have a look at the configuration first.

You can see that I’m running the cluster in the 192.168.50.0/24network, but by default, MetalLB will use the “end” of the network address pool with addresses200-250 . As I have my home torrent server and DNS from Adguard — I’d like them to have specific addresses — together with the Traefik balancer serving the dashboards “and stuff”.
Important: nfs_*_path values should be compatible with the settings you have updated in step 2.
Important (2): Make sure that your Kubernetes config file ~/.kube/config is updated with access details from static/kubernetes.conf— I’m using home-k8s as the context name.
What does the Terraforming do?
Networking
Installs flannel together with configuration patch for host-gw ;
Installs metalLB and sets up the network to var.network_subnet 200–250;
Traefik
Installs Traefik proxy and exposes it through the metalLB load balancer to your home network. Traefik dashboard itself can be accessed via traefik.local

Traefik dashboard running on Pi Cluster
Adguard
Installs Adguard DNS service with persistent volumes claims using NFS;
Exposes dashboard through the traefik and the service itself through the dedicated IP in your home network as adguard.local

Adguard Home running on Pi Cluster
Prometheus
Installs and deploys Prometheus monitoring stack together with grafana on all your nodes. Patches the Prometheus DaemonSet, removing the necessity for the volume mounts. It also exposes grafana through traefik as grafana.local. Default grafana user/password combination is set to admin:admin . Grafana arrives with a pre-installed plugin devopsprodigy-kubegraf-app which I found to be the best one for cluster monitoring.

Grafana Dashboard running on Pi Cluster
Kubernetes dashboard
Installs Kubernetes dashboard and exposes it via traefik on k8s.local

Kubernetes Dashboard running on the Pi Cluster
Torrent
Installs and deploys the torrent server ( rTorrent ) with Flood web interface. Exposes the dashboard via torrent.local . It uses plenty of mounts to keep both the data and configuration stored. There’s a reason for replication to be set to 1 — rTorrent have issues with lock files, and because it uses a shared directory, it simply won’t start if the lock file is detected. rTorrent is ( in my private configuration ) is set to listen on port 23340 .
Backups
As Raspberry Pi runs from a memory card which may wear off due to the constant Read-Write operations — I decided to add regular backups of etcd to the NFS. They’re running once a day, and with the configuration applied by the terraform — every backup “weights” about 32 megabytes.
Running terraform
To make things slightly easier, I have created Makefile, which should help you set things up. You may need to set the following environment variables.
TRAEFIK_API_KEY // Traefik API key
GH_USER // Github user
GH_PAT // Github Personal Access Token
Important: Github credentials are NOT used now, but I’m planning to add authentication for pulling private images from GHCR soon.

Finishing notes
The whole code is available lukaszraczylo/rpi-home-cluster-setup on GitHub, free to use and modify by anyone ( as usual — pull requests are more than welcome ). I have also published custom-built docker images ( rTorrent and Flood ) with multiarch architecture supporting the ARM64 processors.
Automation saves time, nerves and definitely — does the job. I am regularly wiping the whole cluster and starting a build from scratch using the mentioned repository to ensure it works as desired. I will keep both — this article and repository up to date with new functions and features as they arrive.
