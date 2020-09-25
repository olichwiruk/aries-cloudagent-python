### Present Proof 

* Proof presentation step might not work properly if all the schema fields are not filled so that it doesnt have the None value(can be filled even with meaningless info)
* Errors seem to be propagated to the next stage of the protocol, even though first stage passed the next stage can throw a invalid structure error

### Code Keywords to look for what changed (case insensitive)

* Original
* Krzosa
* THCF

### Debugger

To enable the debugger you need to pass in the --debug flag to the Acapy start command, this will make the agent wait for a debugger attach, preventing any startup actions.

To have good compatibility between the source code inside the container and what you have locally its probably a good idea to add a volume to the docker compose this way the code inside the container is always exactly what you have locally

volumes:
         - ./aries-cloudagent-python/aries_cloudagent/:/home/indy/aries_cloudagent


The debugger server by default starts on a 5678 port which needs to be published outside of the container like so in docker-compose:
ports:
          - 8152:5678

where:
	  - portToPublishTo:portInsideContainer

If the agent is waiting with the port published than we can attach to it using the ptvsd debugger and VSCode, you might need download the ptvsd using pip like so:

> pip3 install ptvsd

Finally to begin debugging openup the acapy source code that is also mounted using a volume inside a docker container and click Ctrl + Shift + P (The command menu) type in "open launch.json" and paste in this code into the launch.json file:

"""
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Remote Attach",
            "type": "python",
            "request": "attach",
            "port": 8152,
            "host": "localhost",
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/aries_cloudagent",
                    "remoteRoot": "/home/indy/aries_cloudagent"
                }
            ]
        }
    ]
}
"""
Make sure that pathMappings match exactly to what you have on your setup
Make sure that you use the correct port

To start debugging hit Ctrl + Shift + P (The command menu) type in start debugging.

