#!/usr/bin/env python

""" Reads a Alteon output file and returns the VIPs, Server Groups and
    Real Servers as a complex data structure in the form of a collection
    of dictionaries.
"""

# Author: Wayne Bellward
# Date: 17/03/2022


import os
import sys
import re
import socket
import pathlib
from pprint import pprint
from datetime import datetime


def set_working_dir():
    """ Function that sets the working directory """

    working_dir = ""

    directory_input = False
    while not directory_input:
        working_dir = pathlib.Path(input("Please enter the path to your input"
                        " file, or 'enter' if it's in the same directory as"
                        " this program: "))
        directory_input = pathlib.Path.exists(working_dir)
        if not directory_input:
            input("Invalid path or directory, press enter to try again. ")
            os.system('cls')
    return working_dir


def get_filename(file_path, message):
    """ Welcome screen and setup for initial parameters including
        the working directory and input file """

    my_file = None
    file_input = False

    while not file_input:
        os.system('cls')
        print("\nThe specified file must be comma separated")
        file_name = input(message)
        my_file = file_path / file_name
        file_input = pathlib.Path.exists(my_file)
        if not file_input or file_name == '':
            file_input = False
            input("Invalid file name or file does not exist,"
                  " press enter to try again. ")
    return my_file


def write_dict(dump_dict):
    # Unpack 'dump_dict and write the virtual server info dump to a .csv file

    now = datetime.now()
    dt_str = now.strftime('%d-%m-%y_%H%M%S')

    suffix = '_' + dt_str

    filename = input("\n\nPlease enter the name of the file you wish to save without the file extension: ")
    filename = filename + suffix +'.csv'

    header = ['LB VIP ID', ',', 'LB VIP Name', ',', 'LB VIP IP Addr', ',',
              'Local VIP State', ',', 'Remote VIP State', ',',
              'Service Port', ',', 'RealPort Mapping', ',', 
              'Real Server_1 Name', ',', 'Real Server_1 IP Addr',  ',',
              'Real Server_1 State',  ',', 'Real Server_2 Name', ',',
              'Real Server_2 IP Addr',  ',','Real Server_2 State',  ',',
              'Real Server_3 Name', ',', 'Real Server_3 IP Addr',  ',',
              'Real Server_3 State',  ',','Real Server_4 Name', ',',
              'Real Server_4 IP Addr',  ',','Real Server_4 State',  ',',
              'Real Server_5 Name', ',', 'Real Server_5 IP Addr',  ',',
              'Real Server_5 State',  ',', 'Real Server_6 Name', ',',
              'Real Server_6 IP Addr',  ',', 'Real Server_6 State',  ',',
              'Real Server_7 Name', ',', 'Real Server_7 IP Addr',  ',',
              'Real Server_7 State',',','Real Server_8 Name', ',',
              'Real Server_8 IP Addr',  ',', 'Real Server_8 State', ',',
              'Real Server_9 Name', ',', 'Real Server_9 IP Addr',  ',',
              'Real Server_9 State',  ',', 'Real Server_10 Name', ',',
              'Real Server_10 IP Addr',  ',','Real Server_10 State', ',',
              'Real Server_11 Name', ',', 'Real Server_11 IP Addr',  ',',
              'Real Server_11 State',  ',','Real Server_12 Name', ',',
              'Real Server_12 IP Addr',  ',', 'Real Server_12 State',',',
              'Real Server_13 Name', ',', 'Real Server_13 IP Addr',  ',',
              'Real Server_13 state', ',', 'Real Server_14 Name',  ',',
              'Real Server_14 IP Addr',',', 'Real Server_14 State',',',
              '\n']
              
    with open(filename, 'w') as file:
        file.writelines(header)
        for virt, params in dump_dict.items():
            virt_id = params['id']
            vname = params['name']
            vstate = params['state']
            service = params['services']
            for svc_num, svc_params in service.items():
                svc_grp = svc_params['grp']
                svc_port = svc_params['service_port']
                svc_rport = svc_params['real_port']
                svc_state = svc_params['service_state']
                realsrv_dict = svc_params['realsrvs']
                svc_line = [virt_id, ',', vname, ',', virt, ',', vstate, ',',
                            svc_state, ',', svc_num,',', svc_rport, ',']
                file.writelines(svc_line)
                for srv, params in realsrv_dict.items():
                    #srv_name = params['name']
                    srv_ipaddr = params['ipaddr']
                    srv_state = params['state']
                    srv_line = [srv, ',', srv_ipaddr, ',', srv_state, ',']
                    file.writelines(srv_line)
                new_line = ['\n']
                file.writelines(new_line)
                
    print('\nThe file has been written to timestamped "', filename,
          '" in the local directory', sep = '')
    print()


def check_open_port(ipaddr, port):
    """ Checks to see if the port is open for that service on the load balancer """

    service_ports = {'http': 80,
                     'https': 443,
                     'ssh': 22,
                     'smtp': 25,
                     'ftp': 21
                     }

    try:
        port = int(port)
    except ValueError:
        port = service_ports[port]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        if sock.connect_ex((ipaddr, port)) == 0:
            sock.settimeout(None)
            return 'UP'
        else:
            sock.settimeout(None)
            return 'NO SERVICES UP'
    

def extract_virt(line):
    """ Extracts the vip information from the initial line """

    line = line.strip()
    virt_cut = line.split()
    virt_id = virt_cut[0].strip(':')
    virt_ip = virt_cut[2].strip(',')
    try:
        virt_name = virt_cut[5].strip(',')
    except IndexError:
        virt_name = 'none'
    try:
        virt_state = virt_cut[8]
        virt_state = 'NO SERVICES UP'
    except IndexError:
        virt_state = 'UP'
    virt_info = {virt_ip: {'id': virt_id,
                           'name': virt_name,
                           'state': virt_state,
                           'services': {}}}
    return virt_ip, virt_info


def extract_service(line):
    """ Extracts the service information from the line """

    line = line.strip()
    service_cut = line.split()
    service_port = service_cut[0].strip(':')
    real_port = service_cut[2].strip(',')
    service_grp = service_cut[4].strip(',')
    service_desc = service_cut[5].strip(',')
    service_info = {service_port: {'service_port': service_port,
                                   'service_state': '',
                                   'real_port': real_port,
                                   'grp': service_grp,
                                   'service_desc': service_desc,
                                   'realsrvs': {}}}
                                   
    return service_port, service_info


def extract_realsrv(line):
    """ Extracts the real server information from the line """

    line = line.strip()
    realsrv_cut = line.split()
    realsrv_id = realsrv_cut[0].strip(':')
    realsrv_ipaddr = realsrv_cut[1].strip(',')
    realsrv_name = realsrv_cut[2].strip(',')

    state_match = re.search(r'(?P<state>\S+)$', line)
    realsrv_state = state_match.groupdict()['state']
    realsrv_info = {realsrv_name: {'id': realsrv_id,
                                   'ipaddr': realsrv_ipaddr,
                                   'name': realsrv_name,
                                   'state': realsrv_state}}
                                   
    return realsrv_info

def capture_info(dump_file):
    """ Function iterates through the dump file and compiles a
        complex data structure from the required information elements """

    # Intialise varibles
    virt_dict = {}
    capture = False

    # Start and end patterns
    virtual_srv_section_pattern = re.compile(r"^Virtual server state:$")
    virt_start_pattern = re.compile(r"^\d+:\sIP4\s")
    service_start_pattern = re.compile(r"^\s{4}\S+\srport")
    realsrvs_start_pattern = re.compile(r"^\s{8}\d+:\s[0-9]{1,3}\.[0-9]{1,3}\.")
    section_end_pattern = re.compile(r"^next$")
    end_pattern = re.compile(r"^IDS group state:$")

    with open(dump_file) as dump_file:
        # Interate through dump file and compile complex data structure
        for line in dump_file:
                
            # Identify start and end points for capturing virtual server info
            if re.match(virtual_srv_section_pattern, line):
                capture = True

            if capture:
                # Start capturing general VIP info
                if re.match(virt_start_pattern, line):
                    vip_ip, virt_info = extract_virt(line) 
                    virt_dict.update(virt_info)
                    
                # Start service info
                elif re.match(service_start_pattern, line):
                    service_port, service_info = extract_service(line)
                    print('.', end='')
                    service_state = check_open_port(vip_ip, service_port)
                    service_info[service_port]['service_state'] = service_state
                    virt_dict[vip_ip]['services'].update(service_info)
                    service_info = {}
                    
                # Start capturing address object configuration
                elif re.match(realsrvs_start_pattern, line):
                    realsrv_info = extract_realsrv(line)
                    virt_dict[vip_ip]['services'][service_port]['realsrvs'].update(realsrv_info)
                    realsrv_info = {}

                # End capturing at the end of the virtual server state section
                elif re.match(end_pattern, line):
                    capture = False
            
    return virt_dict


def main():
    """ Main Program, used when the module is run directly as a script """
    
    # Read and process the firewall config file into a list
    file_path = set_working_dir()
    dump_message = ("\nEnter the full filename containing the Alteon"
                         " SLB dump file: ")
    dump_file_name = get_filename(file_path, dump_message)

    # Read configuration list and capture the required sections for processing
    dump_dict = capture_info(dump_file_name)
    write_dict(dump_dict)
    print()
    
main()
