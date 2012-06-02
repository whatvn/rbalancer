#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       rbalancer version 0.1.0
#       
#       Copyright 2012 Hung. Nguyen Van <hungnv@opensource.com.vn>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import random 
import sys 
import logging 
import re 
import threading 
from socket import gaierror, error 
from os import getcwd
from time import time, ctime  
from ConfigParser import SafeConfigParser
from tornado.options import define, options
from httplib import HTTPConnection 


config_file = '/etc/rbalancer.conf' 
log_file = '/var/log/rbalancer.log'
counts = {}
start_time = last_check = time() 
constructed_cluster = {} 
webroot=""
logger = logging.getLogger('rbalancer')
hdlr = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.ERROR) 


def init_server():
	global webroot 
	p = SafeConfigParser() 
	p.read(config_file) 
	if p.has_section('global'): 
		server_port = int(p.get('global', 'port'))  
	else:
		server_port = 9998
	define("port", default=server_port, help="run on the given port", type=int)
	webroot = p.get('global', 'static_dir') 

def health_check(target):  
	global dead_servers 
	is_alive = 0
	p    = re.compile("[a-z0-9-.]*?\.[a-z]+$")
	domain_tld = p.findall(target)[0]   
	accepted_responses = (404, 302, 304, 301, 200) 
	try:
		conn = HTTPConnection(domain_tld, timeout = 3) 
		conn.request('HEAD', '/') 
		response = conn.getresponse() 
		if response.status in accepted_responses:
			is_alive = 1
		else:
			logger.error(ctime() + ': %s is down, HTTP error code is: %s' ) %(target, response.status) 
	#FIXME
	except gaierror:
		#logger.error(ctime() + ' ' + target + ':Name or service does not known' )   
		is_alive = 1
	except error:
		logger.error(ctime() + ' ' + target + ': Connection refuse ' ) 
	finally:
		conn.close() 
	if is_alive == 0 and target not in dead_servers:
		dead_servers.append(target)
	if is_alive == 1 and target in dead_servers: 
		dead_servers.pop(dead_servers.index(target)) 


def get_configuration(f):
	"""Use configparser module to parse configuration file
	config file must be in right format, otherwise, server cannot start"""
	cluster = {} 
	group = {} 
	global constructed_cluster
	parser = SafeConfigParser()
	parser.read(f)
	if parser.has_section('farms'):
		farm_list = [value for name, value in parser.items('farms')] 
		for item in farm_list[0].split(','):
			if parser.has_section(item):
				cluster[item] = {name:value for name, value in parser.items(item)}  
	else:
		sys.stderr.write("Configuration file error, no item 'farms' defined\n") 
		sys.stderr.write("Exit!\n") 
		sys.exit(2) 
	
	for i in parser.get('farms','list').split(','):
		list_redirect_domain = [parser.get(parser.get(i, 'list').split(',')[j], 'domain') for j in range(len(parser.get(i, 'list').split(','))) ]
		constructed_cluster[parser.get(i, 'domain')]  = list_redirect_domain 

	for server_group, server_list in cluster.iteritems():
		temporary_list = [] 
		origin_domain_name = server_list['domain']
		servers = [server for server in server_list['list'].split(',')]
		for s in servers: 
			temporary_list.append([v for k, v in parser.items(s) if v != 'on']) 
		group[origin_domain_name] = temporary_list 
	return group 

def random_weighted(d):
	"""Random based on weight defined"""
	offset = random.randint(0, sum(d.itervalues())-1)
	for k, v in d.iteritems():
		if offset < v:
			#print "%s < %s: return %s" %(offset, v, v)
			return k
		offset -= v

init_server() 
handle_servers = get_configuration(config_file)

class BaseHandler(tornado.web.RequestHandler):
	"""This class was defined to work with tornando async only
	it does not do anything except inheriting from RequestHandler"""
	pass

dead_servers = [] 

class Redirector(BaseHandler): 
	"""Main function: get values from configuration, redirect request to right servers"""
	@tornado.web.asynchronous
	def get(self, _path):
		servers = {}
		global last_check  
		global dead_servers 
		self.request.host = self.request.host.split(':')[0] 
		if handle_servers.has_key(self.request.host):
			balance_list = handle_servers[self.request.host]
			for i in range(0, len(balance_list)):
				if len(balance_list[i]) > 2 :
					continue 
				servers[balance_list[i][0]] = int(balance_list[i][1])
			check_list = servers.copy() 
			if (time() - last_check) > 30:
				for k, v in check_list.iteritems():
					t = threading.Thread(target=health_check, args=(k,)) 
					t.start() 
				last_check += 5
			for k in range(len(dead_servers)):
				if servers.has_key(dead_servers[k]): servers.pop(dead_servers[k]) 
			if len(servers.values()) < 1:
				#logger.error('No server available to serve request for ' + self.request.host) 
				last_check -= 5
				raise tornado.web.HTTPError(502, 'No available server') 
			server = random_weighted(servers) 
			try:
				counts[server] = counts[server] + 1
			except KeyError:
				counts[server] = 1 
			_path = self.request.uri 
			if self.get_argument('debug', None)  != None:
				self.write('<b>' + server + _path + '</b>')
				self.finish() 
			else:
				self.redirect(server + _path)  
		else:
			raise tornado.web.HTTPError(403, 'Forbidden')  

class showStatus(tornado.web.RequestHandler):
	def get(self):
		self.request.host = self.request.host.split(':')[0] 
		running_time = int(time() - start_time) 
		self.write('Original domain: <b>' + self.request.host + '</b> <br>') 
		self.write('<b>UP:</b><br>') 
		self.write('<br><table>') 
		for key, value in counts.iteritems():
			if key not in constructed_cluster[self.request.host]: continue  
			if key in dead_servers: continue 
			req_per_second = value/running_time 
			self.write('<tr> <td>' +  '<b>' +  key + '</b>')   
			self.write( '</td>'  + '<td> - Number of requests : ' + '<b>' + str(value) + '</b></td> ') 
			self.write( '<td> - Requests/second: ' + '<b>' + str(req_per_second) +  '</b> </td> </tr>') 
		self.write('</table>')  	
		self.write('<br><b>DOWN: ' + '</b>' + str(len(dead_servers)) + '</br>')
		if len(dead_servers) > 0:
			for i in range(0, len(dead_servers)):
				self.write('  - ' + dead_servers[i] + '<br>') 

			

def main():
	tornado.options.parse_command_line()
	application = tornado.web.Application([
	 			(r'/(.ico)', tornado.web.StaticFileHandler, {'path': webroot}),
				(r'/stats', showStatus), 
        (r'/(.*)', Redirector),
    ])
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.bind(options.port)
	http_server.start(0) 
	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	main()
