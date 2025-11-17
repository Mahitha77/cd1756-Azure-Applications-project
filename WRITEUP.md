# Write-up Template

1. Virtual Machine (VM) Analysis
Costs:

VMs require paying for the entire machine (CPU, RAM, OS disk) even when the application is idle.

Additional costs include OS patching, managed disk charges, load balancer costs, and backups.

Operational overhead increases overall cost because infrastructure maintenance is required.

Scalability:

Scaling is manual or semi-automated using VM Scale Sets.

Horizontal scaling requires load balancers, golden images, and extra configuration.

If the CMS application stores any files locally, ensuring stateless scalability becomes difficult.

Availability:

Availability depends entirely on how the environment is configured (Availability Sets, Zones, multiple VMs).

Failover and redundancy require custom setup and additional components like Azure Load Balancer.

SLA depends on the chosen VM SKU and the HA configuration created by the user.

Workflow / Deployment & Management:

Full OS access, but also full responsibility for updates, patching, security hardening, and runtime installations.

Deployment requires custom scripts, SSH/RDP access, configuration management (Ansible/Terraform), and manual environment preparation.

Monitoring and log ingestion require installing agents and configuring alerts manually.

2. Azure App Service Analysis
Costs:

You pay only for the App Service Plan tier and scale-out instances, not for OS-level infrastructure.

Platform handles patching, meaning reduced operational/maintenance cost.

For typical CMS applications, App Service is usually cheaper than maintaining a VM with similar availability.

Scalability:

Built-in autoscaling based on CPU, memory, or schedule with no manual setup.

Stateless architecture support makes horizontal scaling simple.

Scale-out happens automatically without downtime.

Availability:

High availability is built-in for most production tiers.

Platform automatically handles instance failures and replacements.

Deployment slots enable safe zero-downtime deployments.

Workflow / Deployment & Management:

Easy CI/CD support using GitHub, DevOps, or zip deploy.

No OS patching or server maintenance required.

Built-in Application Insights provides logs and monitoring without extra agents.

3. Chosen Option and Justification:

I chose Azure App Service for deploying the CMS application.
App Service provides a managed environment with significantly lower operational overhead, built-in autoscaling, and streamlined deployment workflows. This makes it ideal for a web-based CMS that does not require custom OS-level configurations. It also offers solid reliability through platform-managed availability and easy integration with monitoring tools. Overall, App Service delivers the best balance of cost efficiency, maintainability, and scalability for this project.

4. Scenario Where a VM Would Be More Appropriate:

A VM would be required if the CMS application needed features that App Service does not support—such as installing custom OS-level drivers, running background daemons, supporting GPU-based workloads, requiring very specific OS configurations, or needing full control over the network stack. In such a case, using App Service would limit the application's capabilities, making a VM the correct hosting option.

In this scenario, I would need to configure VM Scale Sets, automated patching, NSGs for custom networking, monitoring agents, and a load-balanced multi-VM setup to ensure availability. This introduces more operational complexity but provides full infrastructure control.

5. How the Application and Infrastructure Would Change Based on the Decision:
If using App Service (chosen option):

The application must follow a stateless architecture, moving file storage to Azure Blob Storage and sessions to Redis Cache.

Long-running tasks should be moved to Azure Functions or WebJobs.

Deployment pipeline would use deployment slots for zero-downtime releases.

If using a VM instead:

The application could use local OS-level dependencies, background processes, or custom libraries.

Infrastructure would require VM hardening, NSG rules, load balancers, backup policies, and manual patching workflows.

Monitoring would rely on installing Azure Monitor agents and maintaining VM health manually.
