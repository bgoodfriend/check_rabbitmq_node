#!/bin/python

import requests
from requests.exceptions import HTTPError
import argparse
import sys


parser = argparse.ArgumentParser(description='Check RabbitMQ Node')
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
parser.add_argument('-rabbitname', help='Rabbit name (default: rabbit)',
                    default='rabbit')
parser.add_argument('-metric', help='Metric to check (default: mem_used)',
                    default='mem_used')
parser.add_argument('-metric_limit',
                    help='Metric to check (default: mem_used)',
                    default='mem_limit')

args = parser.parse_args()

# This script's output follows the Nagios/Icinga plugin standard:
# https://nagios-plugins.org/doc/guidelines.html

# This script consumes typical http://<rabbitmqhost>/api/nodes
# For a complete RabbitMQ solution, additionally test at least
# http://<rabbitmqhost>/api/aliveness-test/

# Another approach to monitoring RabbitMQ in containers, is to let th4
# containers export their own metrics to Prometheus.  Examples:
# https://github.com/kbudde/rabbitmq_exporter
# https://github.com/deadtrickster/prometheus_rabbitmq_exporter

# Example function test procedure:
# 1. local deploy community docker image, create named node:
# % sudo docker run -it --rm --hostname my-rabbit --name my-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
# 2. Verify it's there:
# # All nodes (array of 1 node):
# curl -u guest:guest -X GET http://localhost:15672/api/nodes | jq
# # Just our named node:
# curl -u guest:guest -X GET http://localhost:15672/api/nodes/rabbit@my-rabbit/ | jq
# 3. Default check all nodes:
# % ./check_rabbitmq_node -hostname localhost

ERROR = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3}
warn_msg = []
crit_msg = []
ok_msg = []

protocol = "s" if args.ssl else ""
url = "http%s://%s:%s/api/nodes/%s" % (protocol, args.hostname, args.port, args.node)
print(url)

try:
    response = requests.get(url, auth=(args.user, args.password))

    # If the response was successful, no Exception will be raised
    response.raise_for_status()
except HTTPError as http_err:
    print("UNKNOWN:HTTP error occurred: ", http_err)
    print(sys.exit(3))
except Exception as err:
    print("UNKNOWN:Other error occured: ", err)
    print(sys.exit(3))
else:
    print('Success!')

try:
    nodes = response.json()
except ValueError:
    print("UNKNOWN:No JSON in Response from ", url)

# /api/nodes returns a list of dicts...
# Single node endpoint returns dict.
if isinstance(nodes, dict):
    nodes = [nodes]

for node in nodes:
    if args.metric not in node:
        print("UNKNOWN: Could not find metric ", args.metric,
              " in node ", node)
        print(sys.exit(3))
    print(node['name'])
    if args.metric_limit not in node:
        print("UNKNOWN: Could not find metric ", args.metric_limit,
              " in node ", node)
        print(sys.exit(3))
    print(node['name'])
    print(node[args.metric])
    print(node[args.metric_limit])
    print(node['proc_used'])
    print(node['proc_total'])
    print(node['fd_used'])
    print(node['fd_total'])
