# Copyright 2019 Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import unittest
import gateway


class GatewayTestCase(unittest.TestCase):
    def setUp(self):
        gateway.app.testing = True
        self.app = gateway.app.test_client()

    def test_project_api(self):
        resp = self.app.get('/gateway/HEAD')
        assert '200 OK' == resp.status
        assert b'ref: refs/heads/master' == resp.data


if __name__ == '__main__':
    unittest.main()
