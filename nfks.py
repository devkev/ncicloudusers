#!/usr/bin/env python
from optparse import OptionParser
from nfacct import DataBase, researchers

from sqlalchemy import Table, MetaData, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import mapper, sessionmaker
from urllib import quote_plus as urlquote

import os, sha, base64, random, string
from keystoneclient.v2_0 import client
from fabric.api import local, env

username = os.environ.get('OS_USERNAME')
tenant_name = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

db = create_engine(os.environ.get('NF_DRIVER') + '://' +
                   os.environ.get('NF_USERNAME') + ':' +
                   urlquote(os.environ.get('NF_PASSWORD')) + '@' +
                   os.environ.get('NF_HOST') + '/' +
                   os.environ.get('NF_DATABASE'))

Session = sessionmaker(bind=db)
session = Session()
metadata = MetaData(db)

projects = Table('projects', metadata, autoload=True)
users = Table('researchers', metadata, autoload=True)


# Generate a pseudo-random salt
def getsalt(chars = string.letters + string.digits,length=16):
    salt = ''
    for i in range(int(length)):
        salt += random.choice(chars)
    return salt

# Generate a random passwod for a user
def randpasswd(chars = string.digits + string.ascii_letters,length=8):
    result = ''
    for i in range(length):
        result = result + getsalt(chars,1)
    return result

#add all users in a project to a keystone tenant, and create the tenant if necessary
def add_project(project):
    keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
    db = DataBase.acctDB()
    users = researchers.findprojlogins(db, project)

    # sanity check
    if len(users) == 0:
        print "That project has no users."
        return

    # get tenant by name is bugged at the moment
    # https://bugs.launchpad.net/keystone/+bug/1055763
    tenants = keystone.tenants.list()
    t = [t for t in tenants if t.name==project]
    if len(t) > 0:
        tenant = t[0]
    else:
        print type()
        pass
        #keystone.tenants.create(project, description="", enabled="")

    # if the project already exists
    
# add user in reseracher db to tenant in keystone
def add_user_to_tenant(user, tenant):
    keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
    db = DataBase.acctDB()
    
# write user credentials to a file for them to source
def write_credentials(user, tenant, password):
    pass
    
def test():
    keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
    tenants = keystone.tenants.list()

    for project in session.query(projects):
        print project.title


def main():
    p = OptionParser()

    p.add_option('--user', '-u')
    p.add_option('--tenant', '-t')

    p.add_option('--project', '-p')

    p.add_option('--debug', '-d')
    options, arguments = p.parse_args()

    # add project, and all users from project
    # output creds for new users
    if (options.debug):
        test()

    if (options.project):
        add_project(options.project)

    # add user who is in project to tenant
    # no creds output
    if (options.user and options.tenant):
        add_user_to_tenant(options.user, options.tenant)

if __name__ == '__main__':
    main()


