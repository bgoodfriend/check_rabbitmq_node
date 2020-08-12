#!/bin/python
'''
    This script's output follows the Nagios/Icinga plugin standard:
    https://nagios-plugins.org/doc/guidelines.html

    This script consumes typical http://<rabbitmqhost>/api/nodes
    For a complete RabbitMQ solution, additionally test at least
    http://<rabbitmqhost>/api/aliveness-test/

    Reports on ALL nodes, or optional specified --node <nodename>.

    Another approach to monitoring RabbitMQ, is to let the
    containers export their own metrics to Prometheus.  Examples:
    https://github.com/kbudde/rabbitmq_exporter
    https://github.com/deadtrickster/prometheus_rabbitmq_exporter

    Example function test procedure:
    1. local deploy community docker image, create named node:
    % sudo docker run -it --rm --hostname my-rabbit --name my-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
    2. Verify it's there:
    # All nodes (array of 1 node):
    curl -u guest:guest -X GET http://localhost:15672/api/nodes | jq
    # Just our named node:
    curl -u guest:guest -X GET http://localhost:15672/api/nodes/rabbit@my-rabbit/ | jq

    # EXAMPLE CHECK RUNS
    % $ ./check_rabbitmq_node.py -hostname localhost
    OK rabbit@my-rabbit: 21.52% mem_used/mem_limit
    $ ./check_rabbitmq_node.py -hostname localhost -w 5
    WARNING rabbit@my-rabbit: 21.52% mem_used/mem_limit
    $ ./check_rabbitmq_node.py -hostname localhost -w 5 -c 10
    CRITICAL rabbit@my-rabbit: 21.52% mem_used/mem_limit
    $ ./check_rabbitmq_node.py -hostname localhost -metric "proc_used" -metric_limit "proc_total"
    OK rabbit@my-rabbit: 0.04% proc_used/proc_total
    $ ./check_rabbitmq_node.py -hostname localhost -metric "fd_used" -metric_limit "fd_total"
    OK rabbit@my-rabbit: 3.22% fd_used/fd_total
    # Specify node:
    $ ./check_rabbitmq_node.py -hostname localhost -node "rabbit@my-rabbit"
    OK rabbit@my-rabbit: 21.52% mem_used/mem_limit
'''
import requests
from requests.exceptions import HTTPError
import argparse
import sys


parser = argparse.ArgumentParser(description='Check RabbitMQ Node')
parser.add_argument('-warning', help='WARNING Threshhold % (default: 80)',
                    type=int,
                    default='80')
parser.add_argument('-critical', help='CRITICAL Threshhold % (default: 90)',
                    type=int,
                    default='90')
parser.add_argument('-hostname', help='RabbitMQ host name',
                    required=True)
parser.add_argument('-port', help='RabbitMQ port',
                    default='15672')
parser.add_argument('-node', help='RabbitMQ node',
                    default="")
parser.add_argument('-user', help='RabbitMQ username',
                    default='guest')
parser.add_argument('-password', help='RabbitMQ password',
                    default='guest')
parser.add_argument('-ssl', help='Use SSL', action='store_true')
parser.add_argument('-metric', help='Metric to check (default: mem_used)',
                    default='mem_used')
parser.add_argument('-metric_limit',
                    help='Metric to check (default: mem_used)',
                    default='mem_limit')

args = parser.parse_args()

protocol = "s" if args.ssl else ""
url = "http%s://%s:%s/api/nodes/%s" % (protocol, args.hostname, args.port, args.node)

try:
    response = requests.get(url, auth=(args.user, args.password))

    response.raise_for_status()
except HTTPError as http_err:
    print("UNKNOWN:HTTP error occurred: ", http_err)
    print(sys.exit(3))
except Exception as err:
    print("UNKNOWN:Other error occured: ", err)
    print(sys.exit(3))

try:
    nodes = response.json()
except ValueError:
    print("UNKNOWN:No JSON in Response from ", url)

# /api/nodes returns a list of dicts...Single node endpoint returns dict.
if isinstance(nodes, dict):
    nodes = [nodes]

state = "OK"
msg = []
for node in nodes:
    if 'name' not in node:
        node['name'] = "Unknown"
    if args.metric not in node:
        print("UNKNOWN: Could not find metric ", args.metric,
              " in node ", node)
        print(sys.exit(3))
    if args.metric_limit not in node:
        print("UNKNOWN: Could not find metric ", args.metric_limit,
              " in node ", node)
        print(sys.exit(3))
    if args.metric == 0:
        print("UNKNOWN: Cannot compare 0-value ", args.metric_limit)
        print(sys.exit(3))

    percent = (node[args.metric] / node[args.metric_limit]) * 100
    msg.append("%s: %.2f%% %s/%s" % (node['name'], percent, args.metric, args.metric_limit))
    if percent > args.critical:
        state = "CRITICAL"
    elif percent > args.warning:
        if state != "CRITICAL":
            state = "WARNING"

print(state, "\n".join(msg))
ERROR = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3}
print(sys.exit(ERROR[state]))
