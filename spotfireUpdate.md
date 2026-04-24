2. Infrastructure Requirements
VM specs for production and development environments

OWNER: MOODY + BUMJOON (DSK)
Below is a breakdown of the virtual machines required to support the Spotfire 14.6 deployment across both production and development environments. Specs for each component are being coordinated with the DSK team and will be confirmed prior to provisioning. We are also collecting information on required add-ons and any known configuration limitations from DSK's own deployment experience.

Application Servers (MOS 1 / MOS 2)

Prod and Dev VM specs to be provided by Bumjoon / DSK
Node Managers (Services Layer)

Node Managers host the individual Spotfire services — Web Player, Automation Services, Python Service, and R Service. Each environment will require dedicated nodes.

Prod and Dev VM specs per service node — to be confirmed with DSK
Automation Services Servers

Prod and Dev VM specs to be confirmed
Database Server

Spotfire 14.6 supports SQL Server 2022 and PostgreSQL 15. The database server hosts Spotfire's internal metadata and configuration store — this is separate from your analytical data sources.

DB engine choice and VM specs — Prod and Dev
Cloud Clients

OWNER: MUNOZ
Cloud clients allow users to connect to Spotfire from outside the core infrastructure. Beyond the VM specs themselves, we need a defined support plan from Munoz's team — particularly around how storage constraints will be managed as usage scales.

Client VM specs, support plan, and storage management approach to be confirmed
Add-ons, Configuration & DSK Learnings

OWNER: MOODY (FROM BUMJOON)
We want to capture everything DSK learned from their own upgrade, including which add-ons are required, how Information Designer is configured and what its limitations are, whether direct joins to production databases are permitted in their environment, and how long the full upgrade process took end-to-end.

Add-on list, Information Designer notes, join policy on prod DBs, and upgrade duration — from DSK via Bumjoon
3. Licensing
Seat types, tiers, and decisions needed before we proceed

Spotfire 14.6 introduces a revised licensing model aligned with its three new product tiers. We need to clarify which seat types apply to our user base, and make a decision about our current license reduction program before the upgrade moves forward.

License Types

Data Science License — targets power users such as engineers and analysts who need advanced analytics capabilities. Can be added to existing contracts without renegotiation.
Consumer License — for users who primarily view and interact with dashboards rather than build them.
Estimated seat counts per license type and total cost impact
Current License Reduction Program

DECISION NEEDED — BRIAN / SEAN
We are currently in the middle of a license reduction effort on our existing Spotfire instance. Because usage patterns will likely look different once users migrate to the new version — and because a meaningful amount of legacy content will not carry over — we believe the reduction numbers may not accurately reflect actual demand in the new environment. We recommend pausing the reduction until we have clearer post-migration data, and would like to explore whether we can engage Spotfire directly to discuss this.
4. Open Questions
Items requiring decisions before the upgrade plan is finalized

FOR: BRIAN / SEAN
The following questions surfaced during planning and need alignment from leadership before we can lock in the approach. We would like to resolve these as a group in our next review.

License reduction pause — Should we hold the current license reduction program until after migration, when we have a clearer picture of actual usage? Can we loop Spotfire in to advise on the right approach?
S2 instance sunset timeline — What is the plan for retiring the existing Spotfire instance in S2? We would prefer a long runway to give users adequate time to migrate their reports without pressure.
Data routing via S2 tunnel — Since the majority of our data lives in S2, all data flowing into the new Spotfire instance will need to pass through the tunnel. We want to confirm this is the agreed architecture before designing around it.
Trino as the preferred data access layer — Rather than allowing direct connections to production databases, our preference is to route all Spotfire data access through Trino, consistent with how Superset is set up. This means more query responsibility falls on users, but we believe it is the right tradeoff for system stability and consistency across tools.
Impact on other KS projects — This upgrade will place a hold on other Knowledge Systems initiatives, including low-code and agentic automation platforms such as n8n. Leadership should be aware of this tradeoff and aligned before we commit to the upgrade timeline.
5. User Migration
How users will move their reports to the new instance

Users will be responsible for migrating their own reports and analyses to the new Spotfire instance. This is not simply a technical constraint — the old and new instances cannot share a library directly, and the migration is an intentional opportunity to retire years of accumulated content that is no longer actively used. A clean migration means a more maintainable platform going forward.

We will provide clear guidance, tooling where available, and a generous timeline to make the process as low-friction as possible. The sunset date for the S2 instance will be set with enough lead time that no one is forced to rush.

Step-by-step migration guidance and any self-service tooling — to be documented
Final sunset date for the S2 instance — pending decision (see Open Questions)
This section will be reviewed with Wilding before it is finalized to ensure the plan is practical and that appropriate support is in place for end users.
