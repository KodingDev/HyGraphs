# HyGraphs
A simple, self-hostable InfluxDB importer for Hypixel related data.

#### Introduction
**So, what IS HyGraphs?** HyGraphs is a simple importer
of Hypixel data into InfluxDB to be displayed in dashboards
such as Grafana and Chronograf.

#### Self Hosting
When self hosting there are two options.

1. [Using Docker compose **(Recommended)**](#docker-compose)
2. [Manual](#manual)

Before starting, ensure you update the `.env` file appropriately.
In most cases, this will simply be setting your
Minecraft UUID and Hypixel API key.

##### Environment Variables
```properties
INFLUX_USERNAME=root
INFLUX_PASSWORD=root
INFLUX_HOST=localhost
INFLUX_PORT=8086

UUID=MC_UUID_HERE
HYPIXEL_API_KEY=API_KEY_HERE
```

##### Docker Compose
To run using Docker compose, make sure Docker is installed
properly for your system.

After Docker is installed, run the `docker-compose up -d`
command in the project directory.
The dashboard will be accessible at `0.0.0.0:8080` and
the raw InfluxDB database will be bound to
`0.0.0.0:8086`.

> **DISCLAIMER:** Ensure that your firewall is properly configured, as
> the Chronograf dashboard that runs by default gives **any user**
> **full admin access over your cluster**. You have been warned!

##### Manual
To run HyGraphs manually, first install Python 3.8 for
your operating system.

Then install the requirements using `pip3 install -r requirements.txt`.
Please note that using a venv is **highly recommended**, although
not required.

After the dependencies are installed, edit your `.env`
file and then run the main script using `python3 main.py`.