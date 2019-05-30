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

import hmac
import json
import time
import uuid

from hashlib import sha1
from typing import Dict
from zlib import compress

import flask
import requests

app = flask.Flask(__name__)


class VirtualGit:
    def __init__(self):
        self.refs = {}  # type: Dict[str, str]
        self.objects = {}  # type: Dict[str, Dict[str, bytes]]
        self.add("heads/master", "Zuul <z@local>", "init", {"README": b""})

    def list(self) -> str:
        return "\n".join([v + "\t" + k for k, v in self.refs.items()]) + "\n"

    def add(self, name: str, author: str, title: str, files: Dict[str, bytes]):
        def encode(obj: str, data: bytes) -> bytes:
            return ("%s %d\x00" % (obj, len(data))).encode('ascii') + data

        def addObject(data: bytes) -> str:
            hash = sha1(data).hexdigest()
            self.objects.setdefault(hash[:2], {})[hash[2:]] = compress(data)
            return hash

        blobs = []
        for fileName, fileContent in files.items():
            blob = encode("blob", fileContent)
            addObject(blob)
            blobs.append((fileName, sha1(blob).digest()))

        tree = addObject(encode("tree", b"".join([
            b"100644 " + fileName.encode('ascii') + b"\x00" + blob
            for fileName, blob in blobs])))

        parent = "" if name.startswith("heads") else "\nparent %s" % (
            self.refs["refs/heads/master"])

        commit = addObject(encode("commit", ("\n".join([
            "tree {tree}" + parent,
            "author {author}",
            "committer {author}",
            "",
            "%s\n" % title
        ])).format(author=author + " %d +0000" % time.time(),
                   tree=tree).encode('ascii')))
        self.refs["refs/" + name] = commit


class Service:
    git = VirtualGit()
    # token = "".join([random.choice(string.ascii_letters) for _ in range(34)])
    token = "WCL92MLWMRPGKBQ5LI0LZCSIS4TRQMHR0Q"
    zuul = "http://localhost:9000/api/connection/virtual/payload"
    project = "gateway"
    jobs = {}  # type: Dict[str, Dict[str, str]]

    def sendPayload(topic: str, body: Dict[str, Dict]):
        payload = dict(msg_id=str(uuid.uuid4()), topic=topic, msg=body)
        req = requests.post(
            Service.zuul, json=payload, headers={
                "x-pagure-project": Service.project,
                "x-pagure-signature": hmac.new(
                    Service.token.encode('utf-8'),
                    json.dumps(payload).encode('utf-8'), sha1).hexdigest()})
        if not req.ok:
            raise RuntimeError(
                "Failure to send payload: %s %s" % (str(req), req.text))

    def trigger(job: str, zuul: bytes, author: str = None):
        if not author:
            author = "Zuul Gateway <zuul@localhost>"
        Service.jobs[job] = {"status": "pending"}
        Service.git.add("refs/pull/%s/head" % job, author, "Trigger event",
                        {"zuul.yaml": zuul})
        Service.sendPayload("pull-request.new", dict(pullrequest=dict(
            branch='master',
            id=job,
            project=dict(name=Service.project),
            title="Trigger event")))

    @app.route("/jobs")
    def jobsList() -> Dict[int, str]:
        return flask.jsonify(Service.jobs)

    @app.route("/jobs/<name>", methods=['GET', 'POST'])
    def jobsTrigger(name: str) -> Dict[str, str]:
        if flask.request.method == 'POST':
            Service.trigger(name, flask.request.data)
        return flask.jsonify(Service.jobs[name])

    @app.route("/<proj>/HEAD")
    def head(proj: str) -> str:
        return "ref: refs/heads/master"

    @app.route("/<proj>/info/refs")
    def refs(proj: str) -> str:
        return Service.git.list()

    @app.route("/<proj>/objects/<nib>/<rest>")
    def objects(proj: str, nib: str, rest: str) -> bytes:
        return Service.git.objects[nib][rest]

    @app.route("/api/0/<proj>/pull-request/<pr>")
    @app.route("/api/0/<proj>/pull-request/<pr>/diffstats")
    @app.route("/api/0/<proj>/pull-request/<pr>/flag", methods=['GET', 'POST'])
    @app.route("/api/0/<proj>/pull-request/<pr>/comment", methods=['POST'])
    def pr(proj: str, pr: str) -> Dict[str, str]:
        if flask.request.form and flask.request.form.get("status"):
            Service.jobs[pr]["status"] = flask.request.form["status"]
        elif flask.request.form and flask.request.form.get("comment"):
            Service.jobs[pr]["comment"] = flask.request.form["comment"]
        return flask.jsonify({"status": "Open", "branch": "master",
                              "commit_stop": 1, "flags": None,
                              "zuul.yaml": "yes"})

    @app.route("/<path:subpath>", methods=['GET', 'POST', 'PUT'])
    def api(subpath: str) -> Dict:
        token = dict(id=1, description="zuul-token-%d" % time.time(),
                     expired=False)
        return flask.jsonify(dict(total_branches=1,
                                  branches=["master"],
                                  connector=dict(api_tokens=[token],
                                                 hook_token=Service.token)))


def main():
    ...
