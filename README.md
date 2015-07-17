# check_usolved_barracuda_temperature

## Overview

This Python Nagios/Icinga plugin checks the temperature and fan state of Barracuda firewalls.
If the temperature is higher than the given treshold you'll be informed.
You'll also get noticed if a fan isn't working anymore with the integrated hardware check.

The plugin also returns performance data for the temperature sensors.

## Authors

Ricardo Klement (www.usolved.net)

## Installation

Just copy the file check_usolved_barracuda_temperature.py into your Nagios plugin directory.
For example this path: /usr/local/nagios/libexec/

Give check_usolved_barracuda_temperature.py execution rights for the nagios user.
This plugin needs Python 2 to be installed and uses the libraries sys, os and optparse.

Why not Python 3 you may ask?
Most Nagios / Icinga installations are already using other plugins which are written in Python 2.
So for compatibility reasons I've decided to use Python 2 as well.

Make sure you've enabled the SNMP service on your Barracuda firewall. If you have a cluster it's good to 
configure the SNMP service on the virtual server layer on your Barracuda.
Details to find [here](https://techlib.barracuda.com/display/BNGv54/How+to+Configure+the+SNMP+Service).

I've tested the plugin on Barracuda appliances F100b, F200b, F200c, F600c and F800b.

## Usage

### Test on command line
If you are in the Nagios plugin directory execute this command:

```
./check_usolved_barracuda_temperature.py -H ip_address_of_barracuda -C snmp_community
```

The output could be something like this:

```
OK - 8 fans / CPU Temperature: 49.5 *C, Mainboard Temperature: 23.0 *C
Chassis Fan 1A: 1917 RPM
Chassis Fan 1B: 2109 RPM
Chassis Fan 2A: 2343 RPM
Chassis Fan 2B: 2812 RPM
Chassis Fan 3A: 2481 RPM
Chassis Fan 3B: 2721 RPM
Chassis Fan 4A: 2481 RPM
Chassis Fan 4B: 2909 RPM
CPU Temperature: 49.5 *C
Mainboard Temperature: 23.0 *C
```

Here are all arguments that can be used within this plugin:

```
-H <host address>;
Required: IP or hostname of the Barracuda firewall node with a running snmp service

[-C <snmp community>]
Optional: SNMP Community String

[-V <snmp version>]
Optional: SNMP version 1 or 2c are supported, if argument not given version 2 is used by default

[-O <object>]
Optional: temp or fan. If no object is given fans and temperature will be checked

[-w <warning>]
Optional: Warning threshold for the temperature in degree celsius

[-c <critical>]
Optional: Critical threshold for the temperature in degree celsius

[-P <perfdata>]
Optional: Write -P yes if you like to have performance data

[-T <timeout>]
Optional: SNMP timeout in seconds. Default is 30 seconds.
```

### Install in Nagios

Edit your **commands.cfg** and add the following.

Example for checking the temperature with performande data enabled (detecting not working fans works by default):

```
define command {
    command_name    check_usolved_barracuda_temperature
    command_line    $USER1$/check_usolved_barracuda_temperature.py -H $HOSTADDRESS$ -P yes -C public -w $ARG1$ -c $ARG2$
}
```

Example for just checking the fans (if they are not spinning anymore a critical will be thrown):

```
define command {
    command_name    check_usolved_barracuda_temperature
    command_line    $USER1$/check_usolved_barracuda_temperature.py -H $HOSTADDRESS$ -P yes -C public -O fan
}
```

Edit your **services.cfg** and add the following.

Example for checking the temperature:

```
define service{
	host_name				Test-Server
	service_description		Barracuda-Temperature
	use						generic-service
	check_command			check_usolved_barracuda_temperature!60!70
}
```


You could also use host macros for the snmp community.
