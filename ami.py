from gevent import monkey
monkey.patch_all()

import time
import socket
from uuid import uuid1
try:
    import simplejson as json
except ImportError:
    import json


class AMIClient(object):

    def __init__(self, username, password, host='localhost', port=5038,
                 **kwargs):

        self._cbs_events = {}
        self._cbs_actions = {}
        self._cbs_global = {}
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((host, port))
        self._version = ''
        while not self.version.endswith('\r\n'):
            self._version += self.sock.recv(1024)
            time.sleep(0)
        self.action('login', username=username, secret=password,
                    callback=self._login, **kwargs)

    def _login(self, evt):
        if evt['Response'] != 'Success':
            raise Exception('Login Error')

    @property
    def sock(self):
        return self._sock

    @property
    def version(self):
        return self._version

    def on(self, event, callback):
        if event in ['all', 'event', 'response', 'raw']:
            self._cbs_global[event] = callback
        else:
            self._cbs_events[event] = callback

    def dispatch(self, event):
        if 'all' in self._cbs_global:
            self._cbs_global['all'](event)
            time.sleep(0)

        if 'event' in self._cbs_global and 'Event' in event:
            self._cbs_global['event'](event)
            time.sleep(0)

        if 'response' in self._cbs_global and 'ActionID' in event:
            self._cbs_global['response'](event)
            time.sleep(0)

        if 'ActionID' in event and event['ActionID'] in self._cbs_actions:
            callback = self._cbs_actions.pop(event['ActionID'])
            callback(event)
            time.sleep(0)

        elif 'Event' in event and event['Event'] in self._cbs_events:
            callback = self._cbs_events.get(event['Event'])
            callback(event)
            time.sleep(0)

        elif 'RawData' in event and 'raw' in self._cbs_global:
            self._cbs_global['raw'](event)
            time.sleep(0)

    def parser(self, data):
        res = {}

        try:
            for x in data.split('\r\n'):
                k, v = x.split(': ', 1)
                res[k] = v
        except:
            res = {'RawData': data}

        return res

    def action(self, name, **kwargs):
        actionid = kwargs.pop('actionid', str(uuid1()))

        variable = '\r\nvariable: '.join(
            ['%s=%s' % (k, v) for k, v in kwargs.pop('variable', {}).items()]
        )

        callback = kwargs.pop('callback', None)

        if callback:
            self._cbs_actions[actionid] = callback

        cmd = 'action: %s\r\n' % name

        for k, v in kwargs.iteritems():
            cmd += '%s: %s\r\n' % (k, v)

        cmd += 'variable: %s\r\n' % variable if variable != '' else ''
        cmd += 'actionid: %s\r\n\r\n' % actionid

        self.sock.send(cmd)
        time.sleep(0)

        return actionid

    def serve_forever(self):
        buffer = ''
        while True:
            buffer += self.sock.recv(1024)
            if buffer.endswith('\r\n\r\n'):
                for v in buffer.split('\r\n\r\n'):
                    if v != '':
                        event = self.parser(v)
                        self.dispatch(event)
                buffer = ''
            time.sleep(0)

    def stop(self):
        self.sock.close()
