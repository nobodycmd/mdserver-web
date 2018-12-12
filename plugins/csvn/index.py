# coding: utf-8

import time
import random
import os
import urllib
import binascii
import json
import re
import sys
import subprocess

sys.path.append(os.getcwd() + "/class/core")
import public


app_debug = False
if public.getOs() == 'darwin':
    app_debug = True


def getPluginName():
    return 'csvn'


def getPluginDir():
    return public.getPluginDir() + '/' + getPluginName()


def getServerDir():
    return public.getServerDir() + '/' + getPluginName()


def getInitDFile():
    if app_debug:
        return '/tmp/' + getPluginName()
    return '/etc/init.d/' + getPluginName()


def getArgs():
    args = sys.argv[2:]
    tmp = {}
    args_len = len(args)

    if args_len == 1:
        t = args[0].strip('{').strip('}')
        t = t.split(':')
        tmp[t[0]] = t[1]
    elif args_len > 1:
        for i in range(len(args)):
            t = args[i].split(':')
            tmp[t[0]] = t[1]

    return tmp


def initDreplace():
    initd_file = getInitDFile()

    if not os.path.exists(initd_file):
        return getServerDir()

    return initd_file


def status():
    data = public.execShell(
        "ps -ef|grep " + getPluginName() + " |grep -v grep | grep -v python | awk '{print $2}'")
    if data[0] == '':
        return 'stop'
    return 'start'


def csvnOp(method):

    if app_debug:
        os_name = public.getOs()
        if os_name == 'darwin':
            return "Apple Computer does not support"

    _initd_csvn = '/etc/init.d/csvn'
    _initd_csvn_httpd = '/etc/init.d/csvn-httpd'
    #_csvn = getServerDir() + '/bin/csvn'
    #_csvn_httpd = getServerDir() + '/bin/csvn-httpd'

    ret_csvn_httpd = public.execShell(_initd_csvn_httpd + ' ' + method)
    # ret_csvn = public.execShell(_initd_csvn + ' ' + method)
    subprocess.Popen(_initd_csvn + ' ' + method,
                     stdout=subprocess.PIPE, shell=True)
    if ret_csvn_httpd[1] == '':
        return 'ok'
    return 'fail'


def start():
    return csvnOp('start')


def stop():
    return csvnOp('stop')


def restart():
    return csvnOp('restart')


def reload():
    return csvnOp('reload')


def initdStatus():
    if not app_debug:
        if public.getOs() == 'darwin':
            return "Apple Computer does not support"

    _initd_csvn = '/etc/init.d/csvn'
    _initd_csvn_httpd = '/etc/init.d/csvn-httpd'

    if os.path.exists(_initd_csvn) and os.path.exists(_initd_csvn_httpd):
        return 'ok'
    return 'fail'


def initdInstall():
    import shutil
    if not app_debug:
        if public.getOs() == 'darwin':
            return "Apple Computer does not support"

    _csvn = getServerDir() + '/bin/csvn'
    _csvn_httpd = getServerDir() + '/bin/csvn-httpd'

    ret_csvn = public.execShell(_csvn + ' install')
    ret_csvn_httpd = public.execShell(_csvn_httpd + ' install')
    if ret_csvn[1] == '' and ret_csvn_httpd[1] == '':
        return 'ok'
    return 'fail'


def initdUinstall():
    if not app_debug:
        if public.getOs() == 'darwin':
            return "Apple Computer does not support"

    _csvn = getServerDir() + '/bin/csvn'
    _csvn_httpd = getServerDir() + '/bin/csvn-httpd'

    ret_csvn = public.execShell(_csvn + ' remove')
    ret_csvn_httpd = public.execShell(_csvn_httpd + ' remove')
    return 'ok'


def userAdd():
    args = getArgs()
    if not 'username' in args:
        return 'name missing'

    if not 'password' in args:
        return 'password missing'

    htpasswd = getServerDir() + "/bin/htpasswd"
    svn_auth_file = getServerDir() + "/data/conf/svn_auth_file"
    cmd = htpasswd + ' -b ' + svn_auth_file + ' ' + \
        args['username'] + ' ' + args['password']
    data = public.execShell(cmd)
    if data[0] == '':
        return 'ok'
    return 'fail'


def userDel():
    args = getArgs()
    if not 'username' in args:
        return 'name missing'

    htpasswd = getServerDir() + "/bin/htpasswd"
    svn_auth_file = getServerDir() + "/data/conf/svn_auth_file"
    cmd = htpasswd + ' -D ' + svn_auth_file + ' ' + args['username']
    data = public.execShell(cmd)
    if data[0] == '':
        return 'ok'
    return 'fail'


def getAllUser():
    svn_auth_file = getServerDir() + '/data/conf/svn_auth_file'
    if not os.path.exists(svn_auth_file):
        return public.getJson([])
    auth = public.readFile(svn_auth_file)
    auth = auth.strip()
    auth_list = auth.split("\n")

    ulist = []
    for x in range(len(auth_list)):
        tmp = auth_list[x].split(':')
        ulist.append(tmp[0])
    return ulist


def userList():
    import math
    args = getArgs()

    page = 1
    page_size = 10
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    ulist = getAllUser()
    ulist_sum = len(ulist)

    page_info = {'count': ulist_sum, 'p': page,
                 'row': 10, 'tojs': 'csvnUserList'}
    data = {}
    data['list'] = public.getPage(page_info)
    data['page'] = page
    data['page_size'] = page_size
    data['page_count'] = int(math.ceil(ulist_sum / page_size))
    start = (page - 1) * page_size

    data['data'] = ulist[start:start + page_size]
    return public.getJson(data)


def projectAdd():
    args = getArgs()
    if not 'name' in args:
        return 'project name missing'
    path = getServerDir() + '/bin/svnadmin'
    dest = getServerDir() + '/data/repositories/' + args['name']
    cmd = path + ' create ' + dest
    data = public.execShell(cmd)
    if data[1] == '':
        public.execShell('chown -R csvn:csvn ' + dest)
        return 'ok'
    return 'fail'


def projectDel():
    args = getArgs()
    if not 'name' in args:
        return 'project name missing'

    dest = getServerDir() + '/data/repositories/' + args['name']
    cmd = 'rm -rf ' + dest
    data = public.execShell(cmd)
    if data[0] == '':
        return 'ok'
    return 'fail'


def projectList():
    import math
    args = getArgs()

    path = getServerDir() + '/data/repositories'
    dlist = []
    data = {}
    if os.path.exists(path):
        for filename in os.listdir(path):
            tmp = {}
            filePath = path + '/' + filename
            if os.path.isdir(filePath):
                tmp['name'] = filename
                verPath = filePath + '/format'
                if os.path.exists(verPath):
                    ver = public.readFile(verPath).strip()
                    tmp['ver'] = ver
            dlist.append(tmp)

    page = 1
    page_size = 10
    if 'page' in args:
        page = int(args['page'])

    if 'page_size' in args:
        page_size = int(args['page_size'])

    dlist_sum = len(dlist)
    page_info = {'count': dlist_sum, 'p': page,
                 'row': 10, 'tojs': 'csvnProjectList'}
    data['list'] = public.getPage(page_info)
    data['page'] = page
    data['page_size'] = page_size
    data['page_count'] = int(math.ceil(dlist_sum / page_size))

    start = (page - 1) * page_size
    data['data'] = dlist[start:start + page_size]

    return public.getJson(data)


def getAllAclList():
    svn_access_file = getServerDir() + '/data/conf/svn_access_file'
    aData = public.readFile(svn_access_file)
    aData = re.sub('#.*', '', aData)
    aData = aData.strip().split('[')[1:]
    allAcl = {}
    for i in range(len(aData)):
        oData = aData[i].strip().split(']')
        name = oData[0].strip('/')
        if oData[1] == '':
            allAcl[name] = []
        else:
            user = oData[1].strip().split('\n')
            userAll = []
            for iu in range(len(user)):
                ulist = user[iu].split('=')
                utmp = {}
                utmp['user'] = ulist[0].strip()
                utmp['acl'] = ulist[1].strip()
                userAll.append(utmp)
            allAcl[name] = userAll
    return allAcl


def makeAclFile(content):
    # print content
    svn_access_file = getServerDir() + '/data/conf/svn_access_file'
    tmp = "\n"
    for k, v in content.items():
        if k == '':
            tmp += "[/]\n"
        else:
            tmp += "[/" + k + "]\n"

        for iv in range(len(v)):
            tmp += v[iv]['user'] + ' = ' + v[iv]['acl'] + "\n"
        tmp += "\n"
    svn_tmp_path = getServerDir() + '/data/conf/svn_access_file.log'
    return public.writeFile(svn_access_file, tmp)


def projectAclList():
    args = getArgs()
    if not 'name' in args:
        return 'name missing!'
    name = args['name']
    acl = getAllAclList()

    if name in acl:
        return public.getJson(acl[name])
    else:
        return 'fail'
    # makeAclFile(acl)
    # return public.getJson(acl)


def projectAclAdd():
    args = getArgs()
    if not 'uname' in args:
        return 'username missing'
    if not 'pname' in args:
        return 'project name missing'
    uname = args['uname']
    pname = args['pname']

    ulist = getAllUser()
    if not uname in ulist:
        return uname + " user not exists!"

    acl = getAllAclList()

    tmp_acl = {'user': uname, 'acl': 'rw'}
    if not pname in acl:
        acl[pname] = [tmp_acl]
        makeAclFile(acl)
        return 'ok'

    tmp = acl[pname]
    tmp_len = len(tmp)

    if tmp_len == 0:
        acl[pname] = [tmp_acl]
    else:
        is_have = False
        for x in range(tmp_len):
            if tmp[x]['user'] == uname:
                is_have = True
                return uname + ' users already exist!'
        if not is_have:
            tmp.append(tmp_acl)
            acl[pname] = tmp

    makeAclFile(acl)
    return 'ok'


def projectAclDel():
    args = getArgs()
    if not 'uname' in args:
        return 'username missing'
    if not 'pname' in args:
        return 'project name missing'

    uname = args['uname']
    pname = args['pname']

    ulist = getAllUser()
    if not uname in ulist:
        return uname + " user not exists!"

    acl = getAllAclList()

    if not pname in acl:
        return 'project not exists!'

    tmp = acl[pname]
    tmp_len = len(tmp)
    if tmp_len == 0:
        return 'project no have user:' + uname
    else:
        is_have = False
        rtmp = []
        for x in range(tmp_len):
            if tmp[x]['user'] != uname:
                rtmp.append(tmp[x])
        acl[pname] = rtmp
    makeAclFile(acl)
    return 'ok'


def projectAclSet():
    args = getArgs()
    if not 'uname' in args:
        return 'username missing'
    if not 'pname' in args:
        return 'project name missing'
    if not 'acl' in args:
        return 'acl missing'

    uname = args['uname']
    pname = args['pname']
    up_acl = args['acl']

    ulist = getAllUser()
    if not uname in ulist:
        return uname + " user not exists!"

    acl = getAllAclList()

    if not pname in acl:
        return 'project not exists!'

    tmp = acl[pname]
    tmp_len = len(tmp)
    if tmp_len == 0:
        return 'project no have user:' + uname
    else:
        is_have = False
        for x in range(tmp_len):
            if tmp[x]['user'] == uname:
                tmp[x]['acl'] = up_acl
        acl[pname] = tmp
    makeAclFile(acl)
    return 'ok'

if __name__ == "__main__":
    func = sys.argv[1]
    if func == 'status':
        print status()
    elif func == 'start':
        print start()
    elif func == 'stop':
        print stop()
    elif func == 'restart':
        print restart()
    elif func == 'reload':
        print reload()
    elif func == 'initd_status':
        print initdStatus()
    elif func == 'initd_install':
        print initdInstall()
    elif func == 'initd_uninstall':
        print initdUinstall()
    elif func == 'run_info':
        print runInfo()
    elif func == 'conf':
        print getConf()
    elif func == 'save_conf':
        print saveConf()
    elif func == 'user_list':
        print userList()
    elif func == 'user_add':
        print userAdd()
    elif func == 'user_del':
        print userDel()
    elif func == 'project_list':
        print projectList()
    elif func == 'project_del':
        print projectDel()
    elif func == 'project_add':
        print projectAdd()
    elif func == 'project_acl_list':
        print projectAclList()
    elif func == 'project_acl_add':
        print projectAclAdd()
    elif func == 'project_acl_del':
        print projectAclDel()
    elif func == 'project_acl_set':
        print projectAclSet()
    else:
        print 'fail'
