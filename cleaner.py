import os, sha, base64, random, string
from keystoneclient.v2_0 import client
from fabric.api import local, env

username = os.environ.get('OS_USERNAME')
tenant_name = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')


keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)

tenant = keystone.tenants.get('b3c77e67c34344ff9bfb96b6bc09fe36')

for user in tenant.list_users():
    user.delete()




