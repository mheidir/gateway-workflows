Copyright 2019 BlueCat Networks (USA) Inc. and its affiliates

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

By: Muhammad Heidir (mheidir@bluecatnetworks.com)
 Date: 6-September-2019
 Gateway Version: 19.8.1
 Description: Assign DHCP Reserved based on next available IPv4 address and
              creating host record into DNS

Combination of Chris Meyer's Service Request Host workflow and Example IPv4 
Address Worlflows.

# Device Assignment

Device Assignment is used to facilitate the allocation of DHCP Reserved
IP address to a server and adding the server hostname to the DNS for its
services to be resolvable by clients. The intended user for this workflow
is targetted to System/Server Administrators without the complexity of
having to lookup which IP address is available to use. BlueCat Address
Manager provides the single source of truth for all things IP, hence
this workflow is used to demonstrate this capability. In virtual
environments utilising VMware ESXi for example, there is a need to 
be able to provide an IP and a host record registered into the DNS, fast.
With BlueCat, the aim is to enable a much more leaner process that is
both being tracked and fast. This competency, puts BlueCat in the 
technology forefront where large enterprise customers benefit from
BlueCat's ability to integrate.

![Device Assignment Worflow Page ](https://i.ibb.co/7SbHM7Z/Device-Assignment-Workflow.png)

## Features
 - User authentication managed through BlueCat Address Manager
 - Uses default Configuration and DNS View to simplify use
 - MAC Address validation checks for incorrect entry and prevents workflow from accepting
 - User only has to select the Zone and Network for IP address to be provided
 - And provide the hostname and MAC Address information of the device
 - Deployment is optional until checked, user can choose to deploy immediately or manually from BAM (can be via scheduled deployment also on BAM)
 - Performs server deployment based on its role DHCP, DNS or both


## Minimum Workflow Requirements
 - BlueCat Address Manager - v9.1
 - BlueCat Gateway - v19.8.1


## Installation
 - Download workflow and import into Gateway
 - Assign access rights to the workflow
 
 
## Configuration
  - Ensure "Default Configuration" is set on Gateway > Administration > Configurations
  - Ensure "Default View" is set