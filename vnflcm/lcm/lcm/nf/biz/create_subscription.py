# Copyright (C) 2018 Verizon. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import json
import logging
import requests
import uuid

from collections import Counter

from rest_framework import status

from lcm.nf import const
from lcm.pub.database.models import SubscriptionModel
from lcm.pub.exceptions import NFLCMException
from lcm.pub.exceptions import NFLCMExceptionSeeOther
from lcm.pub.utils.values import ignore_case_get
from lcm.pub.config.config import MSB_BASE_URL

logger = logging.getLogger(__name__)


def is_filter_type_equal(new_filter, existing_filter):
    return Counter(new_filter) == Counter(existing_filter)


class CreateSubscription:
    def __init__(self, data):
        self.data = data
        self.filter = ignore_case_get(self.data, "filter", {})
        logger.debug("self.data:%s" % self.data)
        logger.debug("self.filter:%s" % self.filter)
        self.callback_uri = ignore_case_get(self.data, "callbackUri")
        self.authentication = ignore_case_get(self.data, "authentication", {})
        self.notification_types = ignore_case_get(self.filter, "notificationTypes", [])
        self.operation_types = ignore_case_get(self.filter, "operationTypes", [])
        self.operation_states = ignore_case_get(self.filter, "operationStates", [])
        self.vnf_filter = \
            ignore_case_get(self.filter, "vnfInstanceSubscriptionFilter", {})

    def check_callbackuri_connection(self):
        logger.debug("SubscribeNotification-post::> Sending GET request "
                     "to %s" % self.callback_uri)
        retry_count = 3
        while retry_count > 0:
            requests.packages.urllib3.disable_warnings()
            response = requests.get(self.callback_uri, timeout=10, verify=False)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return
            logger.debug("callbackUri %s returns %s status code." % (self.callback_uri, response.status_code))
            retry_count = - 1

        raise NFLCMException("callbackUri %s didn't return 204 status." % self.callback_uri)

    def do_biz(self):
        self.subscription_id = str(uuid.uuid4())
        self.check_callbackuri_connection()
        self.check_valid_auth_info()
        self.check_filter_types()
        self.check_valid()
        self.save_db()
        subscription = SubscriptionModel.objects.get(subscription_id=self.subscription_id)
        return subscription

    def check_filter_types(self):
        logger.debug("SubscribeNotification--post::> Validating "
                     "operationTypes  and operationStates if exists")
        if self.operation_types and \
                const.LCCNNOTIFICATION not in self.notification_types:
            raise NFLCMException("If you are setting operationTypes,"
                                 "then notificationTypes "
                                 "must be " + const.LCCNNOTIFICATION)
        if self.operation_states and \
                const.LCCNNOTIFICATION not in self.notification_types:
            raise NFLCMException("If you are setting operationStates,"
                                 "then notificationTypes "
                                 "must be " + const.LCCNNOTIFICATION)

    def check_valid_auth_info(self):
        logger.debug("SubscribeNotification--post::> Validating Auth "
                     "details if provided")
        if self.authentication.get("paramsBasic", {}) and \
                const.BASIC not in self.authentication.get("authType"):
            raise NFLCMException('Auth type should be ' + const.BASIC)
        if self.authentication.get("paramsOauth2ClientCredentials", {}) and \
                const.OAUTH2_CLIENT_CREDENTIALS not in self.authentication.get("authType"):
            raise NFLCMException('Auth type should be ' + const.OAUTH2_CLIENT_CREDENTIALS)

    def check_filter_exists(self, sub):
        # Check the notificationTypes, operationTypes, operationStates
        for filter_type in ["operation_types",
                            "notification_types", "operation_states"]:
            if not is_filter_type_equal(getattr(self, filter_type),
                                        ast.literal_eval(getattr(sub, filter_type))):
                return False
        # If all the above types are same then check vnf instance filters
        nf_filter = json.loads(sub.vnf_instance_filter)
        for vnf_filter_type in ["vnfdIds", "vnfInstanceIds",
                                "vnfInstanceNames"]:
            if not is_filter_type_equal(self.vnf_filter.get(vnf_filter_type, []),
                                        nf_filter.get(vnf_filter_type, [])):
                return False
        return True

    def check_valid(self):
        logger.debug("SubscribeNotification--post::> Checking DB if "
                     "callbackUri already exists")
        subscriptions = SubscriptionModel.objects.filter(callback_uri=self.callback_uri)
        if not subscriptions.exists():
            return True
        for subscription in subscriptions:
            if self.check_filter_exists(subscription):
                links = json.loads(subscription.links)
                raise NFLCMExceptionSeeOther("%s/%s" % (MSB_BASE_URL, links["self"]["href"]))
        return False

    def save_db(self):
        logger.debug("SubscribeNotification--post::> Saving the subscription "
                     "%s to the database" % self.subscription_id)
        links = {
            "self": {
                "href": const.ROOT_URI + self.subscription_id
            }
        }
        SubscriptionModel.objects.create(subscription_id=self.subscription_id,
                                         callback_uri=self.callback_uri,
                                         auth_info=json.dumps(self.authentication),
                                         notification_types=json.dumps(self.notification_types),
                                         operation_types=json.dumps(self.operation_types),
                                         operation_states=json.dumps(self.operation_states),
                                         vnf_instance_filter=json.dumps(self.vnf_filter),
                                         links=json.dumps(links))
        logger.debug('Create Subscription[%s] success', self.subscription_id)
