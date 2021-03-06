#!/usr/bin/env python

# Copyright (c) 2016 Thomas Nicholson <tnnich@googlemail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The names of the author(s) may not be used to endorse or promote
#    products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from twisted.internet import reactor
from twisted.conch.ssh.keys import Key
from twisted.python import log
from twisted.application import internet, service
import sys, os
from honssh import server, interact
from honssh.config import config
from honssh.config import validateConfig
from honssh import log as hlog


if not os.path.exists('honssh.cfg'):
    print '[ERR][FATAL] honssh.cfg is missing!'
    sys.exit(1)

cfg = config()

if cfg.has_option('devmode', 'enabled'):   
    if cfg.get('devmode', 'enabled') == 'true':
        log.startLogging(sys.stdout, setStdout=0)

if not validateConfig(cfg):
    sys.exit(1)

ssh_addr = cfg.get('honeypot', 'ssh_addr')

if not os.path.exists(cfg.get('folders', 'log_path')):
    os.makedirs(cfg.get('folders', 'log_path'))
    os.chmod(cfg.get('folders', 'log_path'),0755)
if not os.path.exists(cfg.get('folders', 'session_path')):
    os.makedirs(cfg.get('folders', 'session_path'))
    os.chmod(cfg.get('folders', 'session_path'),0755)

with open(cfg.get('honeypot', 'private_key')) as privateBlobFile:
    privateBlob = privateBlobFile.read()
    privateKey = Key.fromString(data=privateBlob)
with open(cfg.get('honeypot', 'public_key')) as publicBlobFile:
    publicBlob = publicBlobFile.read()
    publicKey = Key.fromString(data=publicBlob)    
with open(cfg.get('honeypot', 'private_key_dsa')) as privateBlobFile:
    privateBlob = privateBlobFile.read()
    privateKeyDSA = Key.fromString(data=privateBlob)
with open(cfg.get('honeypot', 'public_key_dsa')) as publicBlobFile:
    publicBlob = publicBlobFile.read()
    publicKeyDSA = Key.fromString(data=publicBlob)    
    
serverFactory = server.HonsshServerFactory()
serverFactory.privateKeys = {'ssh-rsa': privateKey, 'ssh-dsa': privateKeyDSA}
serverFactory.publicKeys = {'ssh-rsa': publicKey, 'ssh-dsa': publicKeyDSA}

if not cfg.has_option('devmode', 'enabled'):   
    application = service.Application('honeypot')
    service = internet.TCPServer(int(cfg.get('honeypot', 'ssh_port')), serverFactory, interface=ssh_addr)
    service.setServiceParent(application)
else:
    if cfg.get('devmode', 'enabled') == 'true':
        reactor.listenTCP(int(cfg.get('honeypot', 'ssh_port')), serverFactory, interface=ssh_addr)

if cfg.get('interact', 'enabled')== 'true':
    iport = int(cfg.get('interact', 'port'))
    if not cfg.has_option('devmode', 'enabled'):   
        service = internet.TCPServer(iport, interact.makeInteractFactory(serverFactory), interface=cfg.get('interact', 'interface'))
        service.setServiceParent(application)
    else:
        if cfg.get('devmode', 'enabled') == 'true':
            reactor.listenTCP(iport, interact.makeInteractFactory(serverFactory), interface=cfg.get('interact', 'interface'))

if cfg.has_option('devmode', 'enabled'): 
    if cfg.get('devmode', 'enabled') == 'true':
        reactor.run()
