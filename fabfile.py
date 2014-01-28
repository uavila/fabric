# fabfile.py

"""
Glassfish webapp deployment tool
fab vega:wap deploy_application:vega-smt-sync-ws.war,smtsync.war
"""
import os, re
from hashlib import md5

from fabric.api import put, run, env, cd, sudo, settings
from fabric.contrib import files

# Globals
env.user  = 'uavila'
env.key_filename = '/home/uavila/.ssh/id_rsa'

# Default parameters
DEFAULT_INSTALLATION_PATH = "/opt/glassfish3/glassfish/domains/domain1/autodeploy/"
DEFAULT_TMP_PATH = "/tmp/"

#Environment
def vega(role):
    env.gateway = '10.201.29.7'
    if role == "wap":
        env.hosts=['fypwap1.vega.lan', 'fypwap2.vega.lan'] 
    elif role == "sys":
        env.hosts=['fypsys1.vega.lan', 'fypsys2.vega.lan']
    else:
        raise Exception("No role defined.\nfab client(role) deploy_application(war_file)\n")

# Tasks
def hexhash(path):
    m = md5()
    m.update(open(path, 'r').read())
    return m.hexdigest()


def prepare_deploy_application(war_file, tmp_path=None):
    # Calculate md5sum
    local_md5sum = hexhash(war_file)
    print local_md5sum
    # If no tmp path specified, use default.
    if not tmp_path:
        tmp_path = os.path.join(DEFAULT_TMP_PATH, 'deployment')
    with settings(warn_only=True):
        if run('test -d /tmp/deployment'): 
            # Now copy our WAR into the remote tmp path.
            result=put(local_path=war_file, remote_path=os.path.join(tmp_path, war_file), use_sudo=True)
            if result.succeeded: return True
            else: return False
        else:
            sudo('mkdir /tmp/deployment')
            result=put(local_path=war_file, remote_path=os.path.join(tmp_path, war_file), use_sudo=True)
            if result.succeeded: return True
            else: return False

def _extract_deployment_result(log_path):
    """
    Parses server.log to extract autodeployment output
    """
    print env.gateway
    output=sudo('tail -10 ' + log_path)
    match = re.search(r'autodeployment: (.*)', output)
    if match is None:
        return None
    return match

def deploy_application(war_file, context, webapp_path=None):
    """
    Deploy an application into the webapp path for a Glassfish installation.
    """
    result = prepare_deploy_application(war_file)
    if result:
        print "[OK] Package correctly uploaded to the server"
    else: 
        print "[ERROR] Package not uploaded to the server"
        return False
    # If no webapp path specified, used default installation.
    if not webapp_path:
        webapp_path = DEFAULT_INSTALLATION_PATH
    tmp_path=os.path.join(DEFAULT_TMP_PATH, 'deployment', war_file)
    remote_path=os.path.join(webapp_path, context)
    # Now copy our WAR from tmp into the webapp path.
    sudo('mv ' + tmp_path + ' ' + remote_path, pty=True)
    _extract_deployment_result('/opt/glassfish3/glassfish/domains/domain1/logs/server.log')
