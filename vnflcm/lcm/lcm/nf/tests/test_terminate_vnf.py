# Copyright 2017 ZTE Corporation.
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

import json
import uuid
import mock

from django.test import TestCase, Client
from rest_framework import status

from lcm.pub.database.models import NfInstModel
from lcm.pub.database.models import JobStatusModel
from lcm.pub.database.models import VmInstModel
from lcm.pub.database.models import NetworkInstModel
from lcm.pub.database.models import SubNetworkInstModel
from lcm.pub.database.models import PortInstModel
from lcm.pub.database.models import FlavourInstModel
from lcm.pub.database.models import StorageInstModel
from lcm.pub.database.models import SubscriptionModel
from lcm.pub.utils import restcall
from lcm.pub.utils.jobutil import JobUtil
from lcm.pub.utils.timeutil import now_time
from lcm.pub.utils.notificationsutil import NotificationsUtil
from lcm.pub.vimapi import api
from lcm.nf.biz.terminate_vnf import TerminateVnf


class TestNFTerminate(TestCase):
    def setUp(self):
        self.client = Client()
        StorageInstModel.objects.create(
            storageid="1",
            vimid="1",
            resourceid="11",
            insttype=0,
            instid="1111",
            is_predefined=1
        )
        NetworkInstModel.objects.create(
            networkid='1',
            vimid='1',
            resourceid='1',
            name='pnet_network',
            is_predefined=1,
            tenant='admin',
            insttype=0,
            instid='1111'
        )
        SubNetworkInstModel.objects.create(
            subnetworkid='1',
            vimid='1',
            resourceid='1',
            networkid='1',
            is_predefined=1,
            name='sub_pnet',
            tenant='admin',
            insttype=0,
            instid='1111'
        )
        PortInstModel.objects.create(
            portid='1',
            networkid='1',
            subnetworkid='1',
            vimid='1',
            resourceid='1',
            is_predefined=1,
            name='aaa_pnet_cp',
            tenant='admin',
            insttype=0,
            instid='1111'
        )
        FlavourInstModel.objects.create(
            flavourid="1",
            vimid="1",
            resourceid="11",
            instid="1111",
            is_predefined=1
        )
        VmInstModel.objects.create(
            vmid="1",
            vimid="1",
            resourceid="11",
            insttype=0,
            instid="1111",
            vmname="test_01",
            is_predefined=1,
            operationalstate=1
        )

    def tearDown(self):
        VmInstModel.objects.all().delete()
        NetworkInstModel.objects.all().delete()
        SubNetworkInstModel.objects.all().delete()
        PortInstModel.objects.all().delete()
        NfInstModel.objects.all().delete()

    def assert_job_result(self, job_id, job_progress, job_detail):
        jobs = JobStatusModel.objects.filter(
            jobid=job_id,
            progress=job_progress,
            descp=job_detail
        )
        self.assertEqual(1, len(jobs))

    @mock.patch.object(TerminateVnf, 'run')
    def test_terminate_vnf(self, mock_run):
        req_data = {
            "terminationType": "GRACEFUL",
            "gracefulTerminationTimeout": 120
        }
        NfInstModel(
            nfinstid='12',
            nf_name='VNF1',
            nf_desc="VNF DESC",
            vnfdid="1",
            netype="XGW",
            vendor="ZTE",
            vnfSoftwareVersion="V1",
            version="V1",
            package_id="2",
            status='INSTANTIATED'
        ).save()
        mock_run.re.return_value = None
        response = self.client.post(
            "/api/vnflcm/v1/vnf_instances/12/terminate",
            data=req_data,
            format='json'
        )
        self.assertEqual(
            status.HTTP_202_ACCEPTED,
            response.status_code,
            response.content
        )

    @mock.patch.object(TerminateVnf, 'run')
    def test_terminate_vnf_not_found(self, mock_run):
        req_data = {
            "terminationType": "GRACEFUL",
            "gracefulTerminationTimeout": 120
        }
        mock_run.re.return_value = None
        response = self.client.post(
            "/api/vnflcm/v1/vnf_instances/567/terminate",
            data=req_data,
            format='json'
        )
        self.assertEqual(
            status.HTTP_404_NOT_FOUND,
            response.status_code,
            response.content
        )

    @mock.patch.object(TerminateVnf, 'run')
    def test_terminate_vnf_conflict(self, mock_run):
        req_data = {
            "terminationType": "GRACEFUL",
            "gracefulTerminationTimeout": 120
        }
        NfInstModel(
            nfinstid='123',
            nf_name='VNF1',
            nf_desc="VNF DESC",
            vnfdid="1",
            netype="XGW",
            vendor="ZTE",
            vnfSoftwareVersion="V1",
            version="V1",
            package_id="2",
            status='NOT_INSTANTIATED'
        ).save()
        mock_run.re.return_value = None
        response = self.client.post(
            "/api/vnflcm/v1/vnf_instances/123/terminate",
            data=req_data,
            format='json'
        )
        self.assertEqual(
            status.HTTP_409_CONFLICT,
            response.status_code,
            response.content
        )

    def test_terminate_vnf_when_inst_id_not_exist(self):
        data = {
            "terminationType": "GRACEFUL",
            "gracefulTerminationTimeout": 120
        }
        self.nf_inst_id = str(uuid.uuid4())
        self.job_id = JobUtil.create_job('NF', 'CREATE', self.nf_inst_id)
        JobUtil.add_job_status(self.job_id, 0, "INST_VNF_READY")
        TerminateVnf(data, nf_inst_id=self.nf_inst_id, job_id=self.job_id).run()
        self.assert_job_result(self.job_id, 100, "Terminate Vnf success.")

    @mock.patch.object(restcall, 'call_req')
    @mock.patch.object(api, 'call')
    @mock.patch.object(NotificationsUtil, 'post_notification')
    def test_terminate_vnf_success(self, mock_post_notification, mock_call, mock_call_req):
        NfInstModel.objects.create(
            nfinstid='1111',
            nf_name='2222',
            vnfminstid='1',
            package_id='todo',
            version='',
            vendor='',
            netype='',
            vnfd_model='',
            status='VNF_INSTANTIATED',
            nf_desc='',
            vnfdid='',
            vnfSoftwareVersion='',
            vnfConfigurableProperties='todo',
            localizationLanguage='EN_US',
            create_time=now_time()
        )

        SubscriptionModel.objects.create(
            subscription_id=str(uuid.uuid4()),
            callback_uri='api/gvnfmdriver/v1/vnfs/lifecyclechangesnotification',
            auth_info=json.JSONEncoder().encode({
                'authType': ['BASIC'],
                'paramsBasic': {
                    'userName': 'username',
                    'password': 'password'
                }
            }),
            notification_types=str([
                'VnfLcmOperationOccurrenceNotification',
                'VnfIdentifierCreationNotification',
                'VnfIdentifierDeletionNotification'
            ]),
            operation_types=str(['TERMINATE']),
            operation_states=str(['COMPLETED']),
            vnf_instance_filter=json.JSONEncoder().encode({
                'vnfdIds': ['111'],
                'vnfProductsFromProviders': [],
                'vnfInstanceIds': ['1111'],
                'vnfInstanceNames': [],
            })
        )

        t1_apply_grant_result = [0, json.JSONEncoder().encode(
            {
                "id": "1",
                "vnfInstanceId": "1",
                "vnfLcmOpOccId": "2",
                "vimConnections": [
                    {
                        "id": "1",
                        "vimId": "1"
                    }
                ]
            }), '200']
        t2_lcm_notify_result = [0, json.JSONEncoder().encode(''), '200']
        t3_delete_flavor = [0, json.JSONEncoder().encode({"vim_id": "vimid_1"}), '200']
        mock_call_req.side_effect = [
            t1_apply_grant_result,
            t2_lcm_notify_result,
            t3_delete_flavor
        ]
        mock_call.return_value = None
        mock_post_notification.return_value = None
        data = {
            "terminationType": "FORCEFUL",
            "gracefulTerminationTimeout": 120
        }
        self.nf_inst_id = '1111'
        self.job_id = JobUtil.create_job('NF', 'CREATE', self.nf_inst_id)
        JobUtil.add_job_status(self.job_id, 0, "INST_VNF_READY")
        TerminateVnf(data, nf_inst_id=self.nf_inst_id, job_id=self.job_id).run()
        self.assert_job_result(self.job_id, 100, "Terminate Vnf success.")
