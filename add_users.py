import os, sha, base64, random, string
from keystoneclient.v2_0 import client
from fabric.api import local, env

username = os.environ.get('OS_USERNAME')
tenant_name = os.environ.get('OS_TENANT_NAME')
auth_url = os.environ.get('OS_AUTH_URL')
password = os.environ.get('OS_PASSWORD')

new_tenant = 'NAME OF PROJECT'

def getsalt(chars = string.letters + string.digits,length=16):
    salt = ''
    for i in range(int(length)):
        salt += random.choice(chars)
    return salt

def randpasswd(chars = string.digits + string.ascii_letters,length=8):
    result = ''
    for i in range(length):
        result = result + getsalt(chars,1)
    return result

plaintext_length = 10

ul = list()
# save output of findinfo -P <project name> | grep @ into a file called hostlist
with open('userlist', 'r') as users:
    for entry in users.readlines():
        user = entry.split(' ')
        l = list()
        for i in user:
            if len(i) != 0:
                l.append(i)
        ul.append(l)

users = dict()

for line in ul:
    users[line[-1]] = list()
    users[line[-1]].append(line[2])
    users[line[-1]].append(base64.encodestring(sha.new(randpasswd()).digest()))

keystone = client.Client(username=username, password=password, tenant_name=tenant_name, auth_url=auth_url)
tenant = keystone.tenants.create(tenant_name=new_tenant)

for user in users:
    keystone.users.create(name=user, password=users[user][1], tenant_id=tenant.id, email=users[user][0], enabled=True)
    with open('creds/' + str(user) + 'rc', 'w') as credfile:
        credfile.write('OS_USERNAME=' + user + '\n')
        credfile.write('OS_TENANT_NAME=' + new_tenant + '\n')
        credfile.write('OS_AUTH_URL=' + auth_url + '\n')
        credfile.write('OS_REGION_NAME=' + 'RegionOne' + '\n')
        credfile.write('OS_PASSWORD=' + users[user][1] + '\n')


