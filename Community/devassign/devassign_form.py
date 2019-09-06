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

import datetime

from bluecat.wtform_fields import IP4Address, CustomStringField, CustomBooleanField, PlainHTML, CustomSearchButtonField, CustomSubmitField
from bluecat.wtform_extensions import GatewayForm
from .devassign_host_wtform_fields import CustomZone, IP4Network, CustomIP4Address
from .devassign_host_endpoints import get_next_ip4_address_endpoint

def filter_reserved(res):
    """
    Filter reserved IP.

    :param res:
    :return:
    """
    try:
        if res['data']['state'] == 'RESERVED':
            res['status'] = 'FAIL'
            res['message'] = 'Host records cannot be added if ip address is reserved.'
        return res
    except (TypeError, KeyError):
        return res

class GenericFormTemplate(GatewayForm):
    """
    Generic form Template

    Note:
        When updating the form, remember to make the corresponding changes to the workflow pages
    """
    workflow_name = 'devassign'
    workflow_permission = 'devassign_page'
	
    zone = CustomZone(
        workflow_name=workflow_name,
        permissions=workflow_permission,
        label='Zone',
        required=True,
        is_disabled_on_start=False
    )

    input_x1_button_x1_aligned_open_1 = PlainHTML('<div class="input_x1_button_x1_aligned">')

    input_x1_aligned_open_1 = PlainHTML('<div class="input_x1_aligned">')

    ip4_network = IP4Network(
        workflow_name=workflow_name,
        permissions=workflow_permission,
        label='Network (Optional)',
        required=False,
        one_off=False,
        is_disabled_on_start=False
    )

    input_x1_aligned_close_1 = PlainHTML('</div>')

    get_next_available_ip4 = CustomSearchButtonField(
        workflow_name=workflow_name,
        permissions=workflow_permission,
        label='Get Next IPv4',
        server_side_method=get_next_ip4_address_endpoint,
        on_complete=['populate_ip4_address'],
        is_disabled_on_start=False,
    )

    input_x1_button_x1_aligned_close_1 = PlainHTML('</div>')

    clearfix_2 = PlainHTML('<div class="clearfix"> </div>')

    ip4_address = CustomIP4Address(
        workflow_name=workflow_name,
        permissions=workflow_permission,
        label='IP Address',
        required=True,
        inputs={'address': 'ip4_address'},
        result_decorator=filter_reserved,
        should_cascade_disable_on_change=True,
        is_disabled_on_start=False
    )

    hostname = CustomStringField(
        label='Hostname',
        required=True,
        is_disabled_on_start=False
    )

    macaddress = CustomStringField(
        label='MAC Address',
        required=True,
        is_disabled_on_start=False
    )

    deploy_now = CustomBooleanField(
        label='Deploy Now',
        is_disabled_on_start=False
    )

    submit = CustomSubmitField(
        label='Submit',
        is_disabled_on_start=False
    )
