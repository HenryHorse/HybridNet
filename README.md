# HybridNet: An Online Multiplayer Networking Solution

HybridNet is a project for CSC 564: Research Topics in Computer Networks at Cal Poly SLO.

The goal of the project was to create a system that could be an in between of the Client/Server models and Peer to Peer models for online multiplayer.
To that end, the code in this repository is for a simple online multiplayer game, which can migrate hosts from a client to a dedicated server.

File overview:
* __classes.py__: Object oriented classes representing different components of the game, including bullets, players, and the game state.
* __client.py__: Code that runs a Pygame rendering of the game, takes in user input, sends those inputs to a given IP address, and receives state updates from that same IP.
* __server.py__: Code that accepts incoming client connections and handles their input packets to update game state. Broadcasts the state to all clients
* __server_launcher.py__: Functions to run server.py as a background process if it is not already running
* __remote_api.py__: A Flask server to handle remote requests to launch a server using server_launcher.py

Running __server.py__ will open up a server on your local machine, on port 9999.
You can then connect to that server using __client.py__ the IP address of that machine.

```bash
python3 client.py --ip <server IP>
```

However, this will not work across the internet unless you set up port forwarding to the machine the server is running on.
My recommendation is to use a VPN service such as Tailscale, and adding both your server and clients to your Tailscale network.
This way, you can avoid setting up port forwarding and bypass most network firewalls that could potentially block your connection.

To allow for hybrid swapping to a remote server, you can use __remote_api.py__. 
Running __remote_api.py__ opens up a Flask server on port 9998 on the device you run the script on.
You can then run __client.py__ like so:
```bash
python3 client.py --host
```
to start the client as a host. If you hit space, it will swap the connection to the remote server, and do so for all connected clients.
You can hit space again to swap back to localhost.
You MUST change the REMOTE_IP variable to match the IP address of the device you ran __remote_api.py__ on.