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


class VirtualGitTestCase(unittest.TestCase):
    def setUp(self):
        self.git = gateway.VirtualGit()

    def test_add_ref(self):
        assert 1 == len(self.git.refs)
        assert 3 == len(self.git.objects)
        assert "refs/heads/master" in self.git.refs
        self.git.add("test", "test", "test", {})
        assert 2 == len(self.git.refs)
        assert "refs/test" in self.git.refs
        assert 3 == len(self.git.list().split('\n'))


class GatewayTestCase(unittest.TestCase):
    def setUp(self):
        gateway.app.testing = True
        self.app = gateway.app.test_client()

    def test_project_api(self):
        resp = self.app.get('/gateway/HEAD')
        assert '200 OK' == resp.status
        assert b'ref: refs/heads/master' == resp.data

    def test_project_ref(self):
        resp = self.app.get('/gateway/info/refs')
        assert '200 OK' == resp.status
        assert resp.data.endswith(b'\trefs/heads/master\n')
        ref = resp.data.split()[0].decode('ascii')
        resp = self.app.get('/gateway/objects/{}/{}'.format(ref[:2], ref[2:]))
        assert '200 OK' == resp.status


if __name__ == '__main__':
    unittest.main()
