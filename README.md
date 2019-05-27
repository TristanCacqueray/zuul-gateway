# zuul-gateway: convert external events to git based trigger

Proof of concept that generates virtual git references to trigger zuul events
from non git events.

## Setup

Add to zuul.conf:

```
[connection virtual]
driver=pagure
server=localhost:5000
baseurl=http://localhost:5000
```

To main.yaml:

```
- tenant:
    name: local
    source:
      virtual:
        untrusted-projects:
        - gateway
```

To a check pipeline:

```
- pipeline:
    name: check
    trigger:
      virtual:
        - event: pg_pull_request
          action:
            - opened
    success:
      virtual:
        status: 'success'
    failure:
      virtual:
        status: 'failure'
```

## Run the gateway

```
FLASK_APP=gateway.py flask run
```

## Trigger a job

```
$ curl -X POST --header "Content-Type: application/json" \
    -d '{"job": "rpm-lint", "vars": {"rpm-url": "http://koji/test.rpm"}}' \
    http://127.0.0.1:5000/jobs
OK: 1
$ curl http://127.0.0.1:5000/jobs
{"1":"Build succeeded.\n\n- [rpm-lint](https://sftests.com/logs/1/1/None/check/rpm-lint/5125e93/) : SUCCESS in 40s\n"}
```
