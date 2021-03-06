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

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from lcm.nf.serializers.lccn_subscription_request import LccnSubscriptionRequestSerializer
from lcm.nf.serializers.lccn_subscription import LccnSubscriptionSerializer
from lcm.nf.serializers.lccn_subscriptions import LccnSubscriptionsSerializer
from lcm.nf.serializers.response import ProblemDetailsSerializer
from lcm.pub.exceptions import NFLCMException, NFLCMExceptionBadRequest
from lcm.nf.biz.create_subscription import CreateSubscription
from lcm.nf.biz.query_subscription import QuerySubscription
from lcm.nf.biz.delete_subscription import DeleteSubscription
from .common import view_safe_call_with_log

logger = logging.getLogger(__name__)
VALID_FILTERS = ["operationTypes", "operationStates", "notificationTypes", "vnfInstanceId"]


def get_problem_details_serializer(status_code, error_message):
    problem_details = {
        "status": status_code,
        "detail": error_message
    }
    problem_details_serializer = ProblemDetailsSerializer(data=problem_details)
    problem_details_serializer.is_valid()
    return problem_details_serializer


class SubscriptionsView(APIView):
    @swagger_auto_schema(
        request_body=LccnSubscriptionRequestSerializer(),
        responses={
            status.HTTP_201_CREATED: LccnSubscriptionSerializer(),
            status.HTTP_303_SEE_OTHER: ProblemDetailsSerializer(),
            status.HTTP_400_BAD_REQUEST: ProblemDetailsSerializer(),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ProblemDetailsSerializer()
        }
    )
    @view_safe_call_with_log(logger=logger)
    def post(self, request):
        logger.debug("SubscribeNotification--post::> %s" % request.data)

        lccn_subscription_request_serializer = LccnSubscriptionRequestSerializer(data=request.data)
        if not lccn_subscription_request_serializer.is_valid():
            raise NFLCMExceptionBadRequest(lccn_subscription_request_serializer.errors)
        subscription = CreateSubscription(
            request.data).do_biz()
        lccn_notifications_filter = {
            "notificationTypes": ast.literal_eval(subscription.notification_types),
            "operationTypes": ast.literal_eval(subscription.operation_types),
            "operationStates": ast.literal_eval(subscription.operation_states),
            "vnfInstanceSubscriptionFilter": json.loads(subscription.vnf_instance_filter)
        }
        subscription_data = {
            "id": subscription.subscription_id,
            "callbackUri": subscription.callback_uri,
            "_links": json.loads(subscription.links),
            "filter": lccn_notifications_filter
        }
        sub_resp_serializer = LccnSubscriptionSerializer(data=subscription_data)
        if not sub_resp_serializer.is_valid():
            raise NFLCMException(sub_resp_serializer.errors)
        return Response(data=subscription_data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: LccnSubscriptionsSerializer(),
            status.HTTP_400_BAD_REQUEST: ProblemDetailsSerializer(),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ProblemDetailsSerializer()
        }
    )
    @view_safe_call_with_log(logger=logger)
    def get(self, request):
        logger.debug("SubscribeNotification--get::> %s" % request.query_params)

        if request.query_params and not set(request.query_params).issubset(set(VALID_FILTERS)):
            problem_details_serializer = get_problem_details_serializer(
                status.HTTP_400_BAD_REQUEST,
                "Not a valid filter"
            )
            return Response(data=problem_details_serializer.data,
                            status=status.HTTP_400_BAD_REQUEST)
        resp_data = QuerySubscription(request.query_params).query_multi_subscriptions()

        subscriptions_serializer = LccnSubscriptionsSerializer(data=resp_data)
        if not subscriptions_serializer.is_valid():
            raise NFLCMException(subscriptions_serializer.errors)

        logger.debug("SubscribeNotification--get::> Remove default fields")
        return Response(data=resp_data, status=status.HTTP_200_OK)


class SubscriptionDetailView(APIView):
    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: LccnSubscriptionSerializer(),
            status.HTTP_404_NOT_FOUND: ProblemDetailsSerializer(),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ProblemDetailsSerializer()
        }
    )
    @view_safe_call_with_log(logger=logger)
    def get(self, request, subscriptionid):
        logger.debug("SubscriptionDetailView--get::> %s" % subscriptionid)

        resp_data = QuerySubscription(
            subscription_id=subscriptionid
        ).query_single_subscription()

        subscription_serializer = LccnSubscriptionSerializer(data=resp_data)
        if not subscription_serializer.is_valid():
            raise NFLCMException(subscription_serializer.errors)

        return Response(data=resp_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_204_NO_CONTENT: "",
            status.HTTP_404_NOT_FOUND: ProblemDetailsSerializer(),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ProblemDetailsSerializer()
        }
    )
    @view_safe_call_with_log(logger=logger)
    def delete(self, request, subscriptionid):
        logger.debug("SubscriptionDetailView--delete::> %s" % subscriptionid)

        DeleteSubscription(
            subscription_id=subscriptionid
        ).delete_single_subscription()

        return Response(status=status.HTTP_204_NO_CONTENT)
