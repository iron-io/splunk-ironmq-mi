# Setup

1. Set the `SPLUNK_HOME` environment variable to the root directory of your Splunk instance. To make the changes to your `PATH` variable permanent, add these export commands to your `.bashrc` file:

```
export SPLUNK_HOME=/opt/splunk
export PATH=$SPLUNK_HOME/bin:$PATH
```

2. Copy this whole `splunk-ironmq-mi` folder to `$SPLUNK_HOME/etc/apps`.
* Restart Splunk

# Adding an input

1. From Splunk Home, click the Settings menu. Under **Data**, click **Data inputs**, and find `IronMQ`, the input you just added. **Click Add new on that row**.
* Click **Add new** and fill in:
    * `name` (whatever name you want to give this input)
    * `token` (the Token of the IronMQ project)
    * `project_id` (the Project ID of the IronMQ project)
    * `queue_name` (the queue name of the IronMQ project)
    * (optional) `max_number_of_messages` (the message size in single request to IronMQ. **Default:** `1`)
    * (optional) `ironmq_host` ([Iron.io AWS Hosts](http://dev.iron.io/mq/reference/clouds/). **Default:** `mq-aws-us-east-1.iron.io`)
    * (optional) `is_deletable` (It's determines whether to delete after receiving a message from the queue. Possible values are True or False. **Default:** `True`)
* Save your input, and navigate back to `Splunk Home`.
* Do a search for `sourcetype=splunk-ironmq-mi` and you should see some queue message indexed, if your Iron.io project has a message in queue.

