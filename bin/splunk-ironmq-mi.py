import sys, urllib2, os

try:
    import json
except:
    import simplejson as json


SPLUNK_HOME = os.environ.get("SPLUNK_HOME")

EGG_DIR = SPLUNK_HOME + "/etc/apps/ironmq_ta/bin/"

for filename in os.listdir(EGG_DIR):
    if filename.endswith(".egg"):
        sys.path.append(EGG_DIR + filename)

from splunklib.modularinput import *
from iron_mq import *


class MyScript(Script):
    def __str_to_bool(self, s):
        if s == 'True':
            return True
        elif s == 'False':
            return False
        else:
            raise ValueError("'is_deletable' not a boolean type. Must be True or False.")

    def get_scheme(self):
        scheme = Scheme("IronMQ")

        scheme.description = "The Message Queue For the Modern Cloud"

        scheme.use_external_validation = True
        scheme.use_single_instance = False

        token_arg = Argument("token")
        token_arg.title = "Token"
        token_arg.data_type = Argument.data_type_string
        token_arg.description = "IronMQ Project Token"
        token_arg.required_on_create = True
        scheme.add_argument(token_arg)

        project_id_arg = Argument("project_id")
        project_id_arg.title = "Project ID"
        project_id_arg.data_type = Argument.data_type_string
        project_id_arg.description = "IronMQ Project ID"
        project_id_arg.required_on_create = True
        scheme.add_argument(project_id_arg)

        queue_name_arg = Argument("queue_name")
        queue_name_arg.title = "Queue Name"
        queue_name_arg.data_type = Argument.data_type_string
        queue_name_arg.description = "IronMQ Project Queue Name"
        queue_name_arg.required_on_create = True
        scheme.add_argument(queue_name_arg)

        max_num_of_msg_arg = Argument("max_number_of_messages")
        max_num_of_msg_arg.title = "Max Queue Size"
        max_num_of_msg_arg.data_type = Argument.data_type_number
        max_num_of_msg_arg.description = "Message size in single request to IronMQ"
        max_num_of_msg_arg.required_on_create = False
        scheme.add_argument(max_num_of_msg_arg)

        ironmq_host_arg = Argument("ironmq_host")
        ironmq_host_arg.title = "IronMQ AWS Host"
        ironmq_host_arg.data_type = Argument.data_type_string
        ironmq_host_arg.description = "IronMQ AWS Host"
        ironmq_host_arg.required_on_create = False
        scheme.add_argument(ironmq_host_arg)

        is_deletable_arg = Argument("is_deletable")
        is_deletable_arg.title = "Is Deletable"
        is_deletable_arg.data_type = Argument.data_type_boolean
        is_deletable_arg.description = "Is deletable after receiving a message from the queue"
        is_deletable_arg.required_on_create = False
        scheme.add_argument(is_deletable_arg)

        return scheme

    def validate_input(self, validation_definition):
        host = validation_definition.parameters["ironmq_host"]
        if host:
            try:
                response = urllib2.urlopen("http://" + host).read()
                jsondata = json.loads(response)
            except:
                raise Exception("The host does not exist: %s !" % host)

        # Project ID, Token validation
        project_id = validation_definition.parameters["project_id"]
        token = validation_definition.parameters["token"]
        try:
            if host:
                ironmq = IronMQ(
                    project_id=project_id,
                    token=token,
                    host=host
                )
            else:
                ironmq = IronMQ(
                    project_id=project_id,
                    token=token
                )

            queues = ironmq.queues()
        except:
            raise Exception("IronMQ project doesn't exist with the specified credentials: project_id:%s, token:%s" % (project_id, token))

        max_size = validation_definition.parameters["max_number_of_messages"]
        if max_size:
            try:
                val = int(max_size)
                if val <= 0:
                    raise ValueError("Max size of queue must be greater than zero!")
            except ValueError:
                raise ValueError("Max size of queue is not an int value!")

        is_deletable = validation_definition.parameters["is_deletable"]
        if is_deletable:
            val = self.__str_to_bool(is_deletable)

    def stream_events(self, inputs, ew):
        for input_name, input_item in inputs.inputs.iteritems():
            # Get fields from the InputDefinition object
            token = input_item["token"]
            project_id = input_item["project_id"]
            queue_name = input_item["queue_name"]
            max_num_of_msg = input_item["max_number_of_messages"] if "max_number_of_messages" in input_item else 1
            ironmq_host = input_item["ironmq_host"] if "ironmq_host" in input_item else "mq-aws-us-east-1.iron.io"
            is_deletable = self.__str_to_bool(input_item["is_deletable"]) if "is_deletable" in input_item else True

            info = "Token: %s, ProjectID: %s, Queue: %s, Max size of message: %s, Host: %s, Deletable: %s" % (
                token, project_id, queue_name, max_num_of_msg, ironmq_host, is_deletable
            )
            ew.log("INFO", info)

            try:
                ironmq = IronMQ(
                    project_id=project_id,
                    token=token,
                    host=ironmq_host
                )

                queue = ironmq.queue(queue_name)
                ew.log("INFO", "Get queue: %s from %s" % (queue_name, queue.client.base_url))

                msgs = queue.get(max=max_num_of_msg)
                for msg in msgs["messages"]:
                    # Create an Event object, and set its fields
                    event = Event()
                    event.stanza = input_name
                    event.data = json.dumps(msg)

                    if is_deletable:
                        queue.delete(msg["id"])
                        ew.log("INFO", "Queue message is deleted: %s" % msg["id"])

                    # Tell the EventWriter to write this event
                    ew.write_event(event)
                    ew.log("INFO", "Queue message is indexed: %s" % json.dumps(msg))
            except Exception, e:
                ew.log("ERROR", e)


if __name__ == "__main__":
    sys.exit(MyScript().run(sys.argv))
