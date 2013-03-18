#!/usr/bin/env python
from optparse import OptionParser
from nfacct import DataBase, researchers

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from urllib import quote_plus as urlquote

import os, sha, base64, random, string, errno, os.path
from keystoneclient.v2_0 import client

username = os.environ.get('OS_USERNAME')
tenant_name = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

db = create_engine(os.environ.get('NF_DRIVER') + '://' +
                   os.environ.get('NF_USERNAME') + ':' +
                   urlquote(os.environ.get('NF_PASSWORD')) + '@' +
                   os.environ.get('NF_HOST') + '/' +
                   os.environ.get('NF_DATABASE'))

Base = declarative_base()
Base.metadata.reflect(bind=db)

class Projects(Base):
    __table__ = Base.metadata.tables['projects']

class Researchers(Base):
    __table__ = Base.metadata.tables['researchers']

class People(Base):
    __table__ = Base.metadata.tables['people']

Session = sessionmaker(bind=db)
session = Session()

memberRole='fd285496b39e42a8a9949881c36a9603'

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

    title =  session.query(Projects, Projects.title).filter_by(project=project)[0].title

    # get tenant by name is bugged at the moment
    # https://bugs.launchpad.net/keystone/+bug/1055763
    tenants = keystone.tenants.list()
    t = [t for t in tenants if t.name==project]
    if len(t) == 0:
        print "making project " + project + " with description '" + title + "'"
        keystone.tenants.create(project, description=title, enabled=True)
        tenants = keystone.tenants.list()

    tenant = [t for t in tenants if t.name==project][0]
    existingusers = [k for k in keystone.users.list()]
    existingusernames = [k.name for k in existingusers]

    for user in users:
        existinguser = [u for u in existingusers if u.name == user]
        if len(existinguser) == 1:
            existinguser = existinguser[0]
            print "adding member roles to " + user
            keystone.roles.add_user_role(existinguser.id, role=memberRole, tenant=tenant.id)
        else:
            print "adding " + user
            userpw = str(base64.encodestring(sha.new(randpasswd()).digest())).replace('=','-')[:-1]
            pid = researchers.get_personid(db, user)

            # some users don't have email addresses
            ppl = session.query(People.email).filter_by(personid=pid)
            for p in ppl:
                email = p.email
                break
            keystone.users.create(name=user, password=userpw, email=email, tenant_id=tenant.id, enabled=True)
            create_cred_file(user, userpw, tenant.name)
            
# add user in researcher db to tenant in keystone
def add_user_to_tenant(user, tenant):
    keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
    db = DataBase.acctDB()
    
def test():
    keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
    print keystone.tenants.list()[0].name
    title =  session.query(Projects, Projects.title).filter_by(project='z00')
    print title[0].title

# write user credentials to a file for them to source
def create_cred_file(user, password, tenant):
    os.umask(0o077)
    try:
        os.makedirs(tenant + "/" + user)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(tenant + "/" + user):
            pass
        else: raise
    with open(tenant + '/' + user + '/.nci-os-creds-' + user + '.sh', 'w') as credfile:
        credfile.write('export OS_USERNAME=' + user + '\n')
        credfile.write('export OS_TENANT_NAME=${PROJECT:-' + tenant + '}\n')
        credfile.write('export OS_AUTH_URL=' + auth_url + '\n')
        credfile.write('export OS_REGION_NAME=' + 'RegionOne' + '\n')
        credfile.write('export OS_PASSWORD=' + password + '\n')
        credfile.write('export OS_NO_CACHE=1'+ '\n')
    with open(tenant + '/' + user + '/.nci-os-creds-' + user + '.csh', 'w') as credfile:
        credfile.write('setenv OS_USERNAME ' + user + '\n')
        credfile.write('if ( ${?PROJECT} ) then\n')
        credfile.write('\tsetenv OS_TENANT_NAME $PROJECT\n')
        credfile.write('else\n')
        credfile.write('\tsetenv OS_TENANT_NAME ' + tenant + '\n')
        credfile.write('endif\n')
        credfile.write('setenv OS_AUTH_URL ' + auth_url + '\n')
        credfile.write('setenv OS_REGION_NAME ' + 'RegionOne' + '\n')
        credfile.write('setenv OS_PASSWORD ' + password + '\n')
        credfile.write('setenv OS_NO_CACHE 1'+ '\n')


def main():
    p = OptionParser()

    p.add_option('--user', '-u', help="Must be used with -t. NOT YET IMPLEMENTED.")
    p.add_option('--tenant', '-t', help="Must be used with -u. NOT YET IMPLEMENTED.")

    p.add_option('--project', '-p')

    p.add_option('--debug', '-d', action="store_true", default=False)

    options, arguments = p.parse_args()

    if (options.debug):
        test()
        return

    if (options.project):
        add_project(options.project)
        return

    if (options.user and options.tenant):
        add_user_to_tenant(options.user, options.tenant)
        return

    p.print_help()


if __name__ == '__main__':
    main()


