# check_rabbitmq_node

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

## Example function test procedure:
1. local deploy community docker image, create named node:
% sudo docker run -it --rm --hostname my-rabbit --name my-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
2. Verify it's there:

### All nodes (array of 1 node):
curl -u guest:guest -X GET http://localhost:15672/api/nodes | jq

### Just our named node:
curl -u guest:guest -X GET http://localhost:15672/api/nodes/rabbit@my-rabbit/ | jq

## EXAMPLE CHECK RUNS
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

