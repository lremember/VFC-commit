# Copyright 2018 ZTE Corporation.
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

from rest_framework import serializers

from .resource_handle import ResourceHandleSerializer


class VnfLinkPortInfoSerializer(serializers.Serializer):
    id = serializers.CharField(
        help_text="Identifier of this link port as provided by the entity that has created the link port.",
        max_length=255,
        required=True,
        allow_null=False,
        allow_blank=False)
    resourceHandle = ResourceHandleSerializer(
        help_text="Reference to the virtualised network resource realizing this link port.",
        required=True,
        allow_null=False)
    cpInstanceId = serializers.CharField(
        help_text="When the link port is used for external connectivity by the VNF, \
        this attribute represents the identifier of the external CP of the VNF to be connected to this link port.",
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True)
