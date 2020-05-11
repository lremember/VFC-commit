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

from lcm.pub.database.models import SubscriptionModel
from lcm.pub.exceptions import NFLCMException

logger = logging.getLogger(__name__)
ROOT_FILTERS = {
    'operationTypes': 'operation_types',
    'operationStates': 'operation_states',
    'notificationTypes': 'notification_types'
}
VNF_INSTANCE_FILTERS = {
    "vnfInstanceId": "vnf_instance_filter"
}


class QuerySubscription:
    def __init__(self, data, subscription_id=''):
        self.subscription_id = subscription_id
        self.params = data

    def query_single_subscription(self):
        subscription = SubscriptionModel.objects.filter(subscription_id=self.subscription_id)
        if not subscription.exists():
            raise NFLCMException('Subscription(%s) does not exist' % self.subscription_id)
        return self.fill_resp_data(subscription)

    def query_multi_subscriptions(self):
        query_data = {}
        logger.debug("QueryMultiSubscriptions--get--biz::> Check for filters in query params" % self.params)
        for query, value in list(self.params.items()):
            if query in ROOT_FILTERS:
                query_data[ROOT_FILTERS[query] + '__icontains'] = value
        for query, value in list(self.params.items()):
            if query in VNF_INSTANCE_FILTERS:
                query_data[VNF_INSTANCE_FILTERS[query] + '__icontains'] = value
        # Query the database with filters if the request has fields in request params, else fetch all records
        if query_data:
            subscriptions = SubscriptionModel.objects.filter(**query_data)
        else:
            subscriptions = SubscriptionModel.objects.all()
        if not subscriptions.exists():
            raise NFLCMException('Subscriptions do not exist')
        return [self.fill_resp_data(subscription) for subscription in subscriptions]

    def fill_resp_data(self, subscription):
        subscription_filter = {
            "notificationTypes": ast.literal_eval(subscription.notification_types),
            "operationTypes": ast.literal_eval(subscription.operation_types),
            "operationStates": ast.literal_eval(subscription.operation_states),
            "vnfInstanceSubscriptionFilter": json.loads(subscription.vnf_instance_filter)
        }
        resp_data = {
            'id': subscription.subscription_id,
            'callbackUri': subscription.callback_uri,
            'filter': subscription_filter,
            '_links': json.loads(subscription.links)
        }
        return resp_data
