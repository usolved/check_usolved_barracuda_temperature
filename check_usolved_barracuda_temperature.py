#!/usr/bin/env python

'''
This Python Nagios/Icinga plugin checks the temperature and fan state of Barracuda firewalls.

Python 2 is required with use of the libraries sys, os, optparse

Copyright (c) 2015 www.usolved.net 
Published under https://github.com/usolved/check_usolved_barracuda_temperature


This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

------------------------

v1.2 2015-11-10
Fixed perfdata and replaced spaces with a "-"

v1.1 2015-07-22
Fixed output when snmpwalk returned quotes in string

v1.0 2015-07-17
Initial release

'''

######################################################################
# Import modules

import sys
import os
import optparse


######################################################################
# Definitions of variables

# Arrays for return codes and return message
return_code 		= { 'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3 }
return_msg 			= ''
return_perfdata 	= ''
return_status 		= return_code['UNKNOWN']


# OIDs
oid	= {
	'Sensors':	'.1.3.6.1.4.1.10704.1.4.1',
	'Name':		'.1',
	'Type':		'.2',
	'Value':	'.3'
	}

cmd = {
	'SNMP_Walk': '/usr/bin/snmpwalk',
	'SNMP_Get': '/usr/bin/snmpget'
}

######################################################################
# Parse Arguments

parser 		= optparse.OptionParser()
parser.add_option('-H', '--hostname', 	help='Required: IP or hostname of the Barracuda firewall node with a running snmp service', dest='arg_hostname', type='string')
parser.add_option('-C', '--community', 	help='Optional: SNMP Community String', dest='arg_snmp_community', type='string', default='public')
parser.add_option('-V', '--version', 	help='Optional: SNMP version 1 or 2c are supported, if argument not given version 2 is used by default', dest='arg_snmp_version', type='string', default='2c')
parser.add_option('-O', '--object', 	help='Optional: temp or fan. If no object is given fans and temperature will be checked', dest='arg_object', type='string', default='all')
parser.add_option('-w', '--warning', 	help='Optional: Warning threshold for the temperature in degree celsius', dest='arg_warning', type='string')
parser.add_option('-c', '--critical', 	help='Optional: Critical threshold for the temperature in degree celsius', dest='arg_critical', type='string')
parser.add_option('-P', '--perfdata', 	help='Optional: Write -P yes if you like to have performance data', dest='arg_perfdata', type='string')
parser.add_option('-T', '--timeout', 	help='Optional: SNMP timeout in seconds', dest='arg_timeout', type='int', default=30)
(opts, args) = parser.parse_args()

arg_hostname 		= opts.arg_hostname
arg_snmp_community	= opts.arg_snmp_community
arg_snmp_version	= opts.arg_snmp_version
arg_object			= opts.arg_object
arg_warning			= opts.arg_warning
arg_critical		= opts.arg_critical
arg_perfdata		= opts.arg_perfdata
arg_timeout			= opts.arg_timeout



######################################################################
# Functions

def output_nagios(return_msg, return_perfdata, return_code):

	print return_msg+return_perfdata

	sys.exit(return_code)



def get_sensors_execute(cmdline):

	sensor 				= []
	cmdline_return 		= os.popen(cmdline)


	for line in cmdline_return.readlines():
		sensor.append(line.rstrip().replace('"',''))

	cmdline_return_code = cmdline_return.close()
	return sensor



def get_sensors():

	cmdline_snmp 		= cmd['SNMP_Walk']+' -v '+arg_snmp_version+' -c '+arg_snmp_community+' -OqevtU -t '+ str(arg_timeout) +' '+arg_hostname
	cmdline_oid_name 	= oid['Sensors']+oid['Name']
	cmdline_oid_type 	= oid['Sensors']+oid['Type']
	cmdline_oid_value 	= oid['Sensors']+oid['Value']

	# read snmp info for every sensor
	sensor_name 		= get_sensors_execute(cmdline_snmp+' '+cmdline_oid_name)
	sensor_type 		= get_sensors_execute(cmdline_snmp+' '+cmdline_oid_type)
	sensor_value 		= get_sensors_execute(cmdline_snmp+' '+cmdline_oid_value)


	# put the returned data into a dictionary to have the data in context
	sensors 	= []

	i = 0
	while i < len(sensor_name):

		tmp_dict 	= {'name': sensor_name[i], 'type': sensor_type[i], 'value': sensor_value[i]}

		sensors.append(tmp_dict)

		i += 1


	return sensors



def check_sensors(sensors):

	global return_msg, return_perfdata

	return_key 				= "OK"
	return_msg_put 			= ""
	return_msg_put_temp 	= ""
	return_perfdata_put 	= ""
	return_msg_extended_put = ""

	count_temp 				= 0
	count_fan 				= 0


	for sensor_data in sensors:

		# the value from snmp is like 35000 so we convert it to a float when the current sensor is temperature

		if sensor_data['type'] == '2':
			sensor_value_float = float(sensor_data['value']) / 1000
		else:
			sensor_value_float = 0.0


		# check if a sensor is in a critical state

		if (arg_object == 'all' or arg_object == 'fan') and sensor_data['type'] == '1' and int(sensor_data['value']) == 0:

			return_msg_put += sensor_data['name'] + " is not working, "
			return_key = 'CRITICAL'

		elif (arg_object == 'all' or arg_object == 'temp') and sensor_data['type'] == '2' and arg_critical and sensor_value_float >= float(arg_critical):

			return_msg_put += sensor_data['name'] + " is " + str(sensor_value_float) + " *C, "
			return_key = 'CRITICAL'

		elif (arg_object == 'all' or arg_object == 'temp') and sensor_data['type'] == '2' and arg_warning and sensor_value_float >= float(arg_warning):

			return_msg_put += sensor_data['name'] + " is " + str(sensor_value_float) + " *C, "

			if return_key != 'CRITICAL':
				return_key = 'WARNING'


		# count the found sensors for the output

		if (arg_object == 'all' or arg_object == 'fan') and sensor_data['type'] == '1':
			count_fan += 1

			# add extended output for fans
			return_msg_extended_put += "\n" + sensor_data['name'] + ": " + sensor_data['value'] + " RPM"

		elif (arg_object == 'all' or arg_object == 'temp') and sensor_data['type'] == '2':
			count_temp += 1

			# add extended output for temperature
			return_msg_extended_put += "\n" + sensor_data['name'] + ": " + str(sensor_value_float) + " *C"
			return_msg_put_temp 	+= sensor_data['name'] + ": " + str(sensor_value_float) + " *C, "

			if arg_perfdata == 'yes':
				sensor_data['name'] = sensor_data['name'].replace(" ", "-")
				return_perfdata_put += sensor_data['name'] + '=' + str(sensor_value_float) + ' '


	# put together the output message

	if return_key == 'OK':

		sensor_output 		= ''

		if count_fan > 0:

			if count_fan > 1:
				label_fan = "fans"
			else:
				label_fan = "fan"

			sensor_output += str(count_fan) + " " + label_fan + " / "

		if count_temp > 0:
			sensor_output += return_msg_put_temp[:-2] + " / "


		sensor_output = sensor_output[:-3]


		# if sensor_output is not empty then sensors where found

		if sensor_output:
			return_msg = return_key + " - " + sensor_output

		else:
			return_key = 'UNKNOWN'
			return_msg = return_key + " - No sensors found"


	else:
		return_msg = return_key + " - " + return_msg_put[:-2]



	# extended output

	if return_msg_extended_put:
		return_msg += return_msg_extended_put



	# if perfdata found

	if return_perfdata_put:
		return_perfdata = return_perfdata_put[:-1]


	return return_code[return_key]




######################################################################
# General

if not arg_hostname:

	return_msg = 'UNKNOWN - Not all required arguments given\nType ./'+os.path.basename(__file__)+' --help for all options.'

	output_nagios(return_msg, '', return_code['UNKNOWN'])

else:

	sensors 		= get_sensors()

	return_status 	= check_sensors(sensors)



	# If performace data available, build output string
	if arg_perfdata == 'yes' and return_perfdata:
		return_perfdata = ' | ' + return_perfdata


	# output the string to std
	output_nagios(return_msg, return_perfdata, return_status)
