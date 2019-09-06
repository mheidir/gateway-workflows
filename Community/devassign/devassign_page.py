# Copyright 2019 BlueCat Networks (USA) Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import sys
import time
import re

import requests
from flask import url_for, redirect, render_template, flash, g, request, jsonify, json

from main_app import app
from bluecat import route, util
import config.default_config as config
from bluecat.constants import IPAssignmentActionValues, DNSDeploymentRoleType, DHCPDeploymentRoleType
from bluecat.deployment_role import DeploymentRole, DNSDHCPDeploymentRole
from bluecat.api_exception import APIException, PortalException, BAMException
from bluecat.bdds_server import Server
from .devassign_form import GenericFormTemplate
from bluecat.server_endpoints import get_result_template, empty_decorator

headers = {"Content-Type": "application/json", "Accept": "application/json"}

# Regular Expression for Validation MAC Address
MACREGEX = re.compile('(^([a-fA-F0-9]{2}[-]{1}){5}[a-fA-F0-9]{2}$)|(^([a-fA-F0-9]{2}[:]{1}){5}[a-fA-F0-9]{2}$)|(^[a-fA-F0-9]{12}$)')

def isMacValid(macAddress):
    """ Returns True for a valid Mac Address, False otherwise """
    if MACREGEX.match(macAddress):
        return True
    return False


def convertMac(macAddress):
    """ Performs conversion of Mac Address format to the bar type and return as string """
  # Reference: https://forums.freebsd.org/threads/python-inserting-a-sign-after-every-n-th-character.26881/
 
  # Convert to CAPS
    stdMac = str(macAddress).upper()
  
  # Checks if contains ':' character and replace with '-'
    if ":" in stdMac:
        return stdMac.replace(':', '-')
    elif "-" in stdMac:
        return stdMac
    else:
        return '-'.join([ i+j for i,j in zip(stdMac[::2],stdMac[1::2])])


def readProperties(propertyObject):
    if len(propertyObject) > 0:
        stripPropertyObject = propertyObject['properties'].split('|')
        
        properties = {}
      
        for prop in stripPropertyObject:
            if len(prop) > 0:
                equalId = prop.index('=')
                propIndex = prop[:equalId]
                propValue = prop[equalId+1:]
                
                properties[propIndex] = propValue
        return properties


def joinProperties(properties):
    """give a dict made from properties, return a property string"""
    return "|".join([
        "%s=%s" % (a[0], a[1].replace("\\", "\\\\").replace("|","\\|"))
        #for a in properties.items() ]) + "|"
        for a in list(properties.items()) ]) + "|"


def get_server_role(roles, types=None):
    # Initialize variables
    dhcp_servers = []
    dns_servers = []

    # Check for requested role type matches dhcp
    if types is 'dhcp' or types is None:
        dhcp_role = []
        for role in roles:
            if 'DHCP' in role.get_service():
                dhcp_role = role

        # Primary DHCP Role
        dhcp_servers.append(int(role.get_server_interface_id()))

        # Secondary DHCP Role
        properties = role.get_properties()
        if properties['secondaryServerInterfaceId']:
            dhcp_servers.append(int(properties['secondaryServerInterfaceId']))

        if types is 'dhcp':
            return dhcp_servers

    # Check for requested role type matches dns
    if types is 'dns' or types is None:
        dns_servers = []
        for role in roles:
            if 'DNS' in role.get_service() and 'MASTER' in role.get_type():
                dns_servers.append(int(role.get_server_interface_id()))
        if types is 'dns':
            return dns_servers

    # Checks if both contains the same values, then just return a combined list
    if set(dhcp_servers) & set(dns_servers):
        return list(set(dhcp_servers + dns_servers))
    return (dhcp_servers, dns_servers)
        

def ismatchEntity(server_role, server_entity):
    for entity in server_entity:
        if server_role == entity.get_id():
            return True
    return False



def module_path():
    encoding = sys.getfilesystemencoding()
    return os.path.dirname(os.path.abspath(__file__))


# The workflow name must be the first part of any endpoints defined in this file.
# If you break this rule, you will trip up on other people's endpoint names and
# chaos will ensue.
@route(app, '/devassign/devassign_page')
@util.workflow_permission_required('devassign_page')
@util.exception_catcher
def devassign_devassign_page():
    """
    Renders the form the user would first see when selecting the workflow.
    :return:
    """
    form = GenericFormTemplate()
    return render_template(
        'devassign_page.html',
        form=form,
        text=util.get_text(module_path(), config.language),
        options=g.user.get_options()
    )


@route(app, '/devassign/form', methods=['POST'])
@util.workflow_permission_required('devassign_page')
@util.exception_catcher
def devassign_devassign_page_form():
    """
    Processes the final form after the user has input all the required data.
    :return:
    """
    form = GenericFormTemplate()

    # Retrieve the configuration object
    try:
        # Retrieve form attributes
        absolute_name = form.hostname.data + '.' + request.form['zone']
        macaddr = form.macaddress.data
        if isMacValid(macaddr):
            configuration = g.user.get_api().get_configuration(config.default_configuration)
            view = configuration.get_view(config.default_view)
            hostinfo = "%s,%s,true,false" % (absolute_name, view.get_id())
            properties = 'name=' + form.hostname.data
            
            g.user.logger.info('View:' + str(view) + ' Absolute Name:' + str(absolute_name))
            ip4_object = configuration.assign_ip4_address(form.ip4_address.data, 
                                                convertMac(macaddr), 
                                                hostinfo, 
                                                IPAssignmentActionValues.MAKE_DHCP_RESERVED,
                                                properties
                                                )
            
            # Put form processing code here
            g.user.logger.info('Success - DHCP Reserved IP4 Address ' + util.safe_str(request.form.get('ip4_address', '')) + 'Assigned with Object ID: ' + util.safe_str(ip4_object.get_id()) + ' Host Record: ' + util.safe_str(absolute_name))
            flash('Success - DHCP Reserved IP4 Address ' + util.safe_str(request.form.get('ip4_address', '')) + ' Assigned with Object ID: ' + util.safe_str(ip4_object.get_id()) + ' Host Record: ' + util.safe_str(absolute_name), 'succeed')
            
            # Perform Server Deployment for DHCP and DNS if checked
            if form.deploy_now.data:
                flash('Deploying DHCP and DNS updates to Servers', 'succeed')
                dhcp_roles = ip4_object.get_deployment_roles()
                g.user.logger.info(dhcp_roles)
                dhcp_servers = get_server_role(dhcp_roles) # May contain DHCP and Reverse Zone
                g.user.logger.info(dhcp_servers)

                host_record = view.get_host_record(absolute_name)
                dns_roles = host_record.get_deployment_roles()
                g.user.logger.info(dns_roles)
                dns_servers = get_server_role(dns_roles, 'dns')
                g.user.logger.info(dns_servers)
                
                # Get list of servers and its entity containing the serverInterfaceId
                servers = configuration.get_servers()

                for server in servers:
                    server_entity = server.get_service_ip4_address_entities()

                    # Check if it contains both DNS and DHCP
                    if type(dhcp_servers) is not list:
                        # Network/Block
                        g.user.logger.error("Checking DHCP")
                        for dhcp_serv in dhcp_servers[0]:
                            if ismatchEntity(dhcp_serv, server_entity):
                                g.user.logger.info("DHCP Deployment: " + util.safe_str(server))
                                server.deploy_services(services=['DHCP'])
                        
                        # Reverse Zone
                        g.user.logger.error("Checking DNS")
                        for dns_serv in dhcp_servers[1]:
                            if ismatchEntity(dns_serv, server_entity):
                                g.user.logger.info("DNS Deployment (Reverse Zone): " + util.safe_str(server))
                                server.deploy_services(services=['DNS'])
                    
                    # Only 1 list, perform deployment of both
                    else:
                        # Network/Block
                        g.user.logger.error("Checking both DNS and DHCP")
                        for dhcp_serv in dhcp_servers:
                            if ismatchEntity(dhcp_serv, server_entity):
                                g.user.logger.info("DNS & DHCP Deployment: " + util.safe_str(server))
                                server.deploy_services(services=['DHCP', 'DNS'])


                    # Perform server deployment for DNS, Forward Zone
                    if type(dns_servers) is list:
                        g.user.logger.info("Checking DNS Only ====")
                        for dns_serv in dns_servers:
                            if ismatchEntity(dns_serv, server_entity):
                                g.user.logger.info("DNS Deployment (Forward Zone): " + util.safe_str(server))
                                server.deploy_services(services=['DNS'])
            
            return redirect(url_for('devassigndevassign_devassign_page'))

        else:
            g.user.logger.error('Invalid MAC Address')
            raise PortalException('Invalid MAC Address')
    except PortalException as e:
        g.user.logger.error('%s' % e, msg_type=g.user.logger.EXCEPTION)
        flash("Invalid MAC Address detected.")
        flash('Unable to retrieve configuration or view specified in configuration')
        return redirect(url_for('devassigndevassign_devassign_page'))


@route(app, '/devassign/get_deploy_status', methods=['POST'])
@util.rest_workflow_permission_required('devassign_page')
@util.rest_exception_catcher
def get_deploy_status():
    """
    Retrieves and updates deployment task status
    :return:
    """
    result = get_result_template()
    deploy_token = request.form['deploy_token']
    try:
        task_status = g.user.get_api().get_deployment_task_status(deploy_token)
        result['status'] = task_status['status']

        if task_status['status'] == SelectiveDeploymentStatus.FINISHED:
            deploy_errors = task_status['response']['errors']

            # Deployment failed
            if deploy_errors:
                result['data'] = "FAILED"
                result['message'] = deploy_errors
                raise Exception('Deployment Error: ' + str(deploy_errors))

            # Deployment succeeded
            elif task_status['response']['views']:
                task_result = task_status['response']['views'][0]['zones'][0]['records'][0]['result']
                result['data'] = task_result

            # Deployment finished with no changes
            else:
                result['data'] = 'FINISHED'

            g.user.logger.info('Deployment Task Status: ' + str(task_status))

        # Deployment queued/started
        else:
            result['data'] = task_status['status']
    # pylint: disable=broad-except
    except Exception as e:
        g.user.logger.warning(e)

    return jsonify(empty_decorator(result))
