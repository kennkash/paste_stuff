Infra Side
	- Can we get a lsit of all VMs that you would need (Give me prod and dev)
	- With specs 
	- Moody can work with bumjoon for DSK specs (
		- Node Managers (services)
		- Automation Servers
		- APP Servers  Mos 1/2
		- DB
		- Cloud Clients (specs, but more importantly what is the plan Munoz to support)
			- storage issues


Kennedy can you look at some features of 14.6, does it have native support for S3?
	How does the licensing work?
		Data Scientist license, consumer
Is it faster, more supported with python? Can people manage their python environment?


Question for Brian/Sean
1) Do we puase the current spotfire license reduction because it will likely behave differently in new version?
2) Can we ask spotfire about this?
3) Timeline for sunsetting the one in S2 (maybe very long time to give user times for migration) 
4) All the data transfers from spotfire will go through the tunnel since most data is in S2.
5) I think we prefer just connecting to Trino and not to the prod dbs directly. Consistentcy with Superset. More work for users, but we think better for system stability
6) This will put a hold on other KS projects, so low code agentic platform such as n8n?

User Migration Side
	- User will need to move reports why? because it's the only they can co-exist, and spotfire has many of year junk that no one uses

Moody get info from Bumjoon
	specs	
	add ins
	info designer + (limitations)
	joins in prod dbs is it allowed?
	how long did it take DSK to make an upgrade?


Review with Wilding
