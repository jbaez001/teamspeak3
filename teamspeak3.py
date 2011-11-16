# Copyright (C) 2011 by Juan L. Baez
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__author__    = "Juan L. Baez"
__copyright__ = "Copyright 2011, Juan L. Baez"
__license__   = "MIT"
__version__   = "1.0.0"
__status__    = "alpha"

from telnetlib import Telnet

class teamspeak:
  default_timeout_connect   = 5
  default_timeout_read      = 5
  
  def encode_string(self, string):
    """
    Encodes a string
    
    @param string: String to encode
    @type string: str
    
    @return: Encoded string
    """
    string = string.replace('\\', '\\\\')
    string = string.replace('/',  '\\/')
    string = string.replace(' ',  '\\s')
    string = string.replace('|',  '\\p')
    string = string.replace('\a', '\\a')
    string = string.replace('\b', '\\b')
    string = string.replace('\f', '\\f')
    string = string.replace('\n', '\\n')
    string = string.replace('\r', '\\r')
    string = string.replace('\t', '\\t')
    string = string.replace('\v', '\\v')
    
    return string

  def decode_string(self, string):
    """
    Decodes a string
    
    @param string: String to decode
    @type string: str
    
    @return: Secoded string
    """
    string = string.replace('\\\\', '\\')
    string = string.replace('\\/',  '/')
    string = string.replace('\\s',  ' ')
    string = string.replace('\\p',  '|')
    string = string.replace('\\a',  '\a')
    string = string.replace('\\b',  '\b')
    string = string.replace('\\f',  '\f')
    string = string.replace('\\n',  '\n')
    string = string.replace('\\r',  '\r')
    string = string.replace('\\t',  '\t')
    string = string.replace('\\v',  '\v')
    
    return string

  def __init__(self, server_host, server_port='10011'):
    """
    Class constructor
    """
    self.server_port  = server_port
    self.server_host  = server_host
  
  def connect(self, server_id=None):
    """
    Connects to the server
    
    @param server_id: Virtual Server's ID
    @type server_id: string 
    """
    data = ''
    
    try:
      self.net = Telnet(self.server_host, self.server_port, teamspeak.default_timeout_connect)
      data = self.net.read_until('\n', teamspeak.default_timeout_read)
      
      if data.rstrip() != 'TS3':
        print 'The server specified does not appear to be a TeamSpeak 3 server.'
        return False
      
    except:
      print 'Error connecting to server.'
      return False
    
    if (server_id):
      self.command('use %s' % (server_id))
    
    self.connected = True
    return True
  
  def read(self):
    """
    Reads from the server. This is useful for server notifications/events.
    
    @return: a list of data to parse
    @return: None if there is nothing to parse
    """
    data = self.net.read_very_eager()
      
    if len(data) > 1:
      data = data.split('\n')
      return data
    
    return None
      
  def disconnect(self):
    """
    Disconnects from the server.
    """
    self.net.write('quit\n')
    self.net.close()
    
  def login(self, client_login_name, client_login_password):
    """
    Logins to the server.
    
    @param client_login_name: Server query login
    @type client_login_name: str
    
    @param client_login_password: Server query password
    @type client_login_password: str
    """
    return self.command('login', { 'client_login_name' : client_login_name, 'client_login_password' : client_login_password})
    
  def parse_results(self, res):
    """
    Experimental parser.
    
    @param res: Raw data.
    @type res: str
    
    @return: dictionary of parsed items
    """
    out = {}
    
    res = res.replace('\r', '')
    for key in res.split(' '):
      value = key.split('=',1)
      
      if len(value) > 1:
        out[value[0]] = self.decode_string(''.join(value[1:]))
      else:
        out[key] = None
      
    return out
  
  def command(self, cmd, parameters={}, options=''):
    """
    Executes a command.
    
    @param cmd: Command to execute.
    @type cmd: str
    
    @param parameters: Parameters
    @type parameters: dict
    
    @param options: Options to pass.
    @type options: str
    
    @return: a list of dictionaries containing the results
    """
    ret = []
    
    out = cmd
    
    for key in parameters:
      out += ' %s=%s' % (key, self.encode_string(parameters[key]))
    
    out += ' ' + options + '\n'
    
    # print '->' + out
    self.net.write(out)
    
    data = self.net.expect(['(error id=)\d+ (msg=).*\n'], 5)
    
    results   = data[2].split('\n')
    error_id  = results[len(results)-2].split(' ')[1].split('=')[1]
    error_msg = results[len(results)-2].split(' ')[2].split('=')[1]
    
    if (error_id != '0'):
      print 'Server Error: %s, on command: %s' % (error_msg, cmd)
      return ret
      
    results = results[0]
    multi   = results.split('|')
    
    if len(multi) > 1:
      for item in multi:
        ret.append(self.parse_results(item))
    else:
      ret.append(self.parse_results(results))

    return ret
  
  def get_client_list(self, options=''):
    """
    Retrieves a list of clients with the given options.
    
    @param options: Options.
    @type options: str
    
    @return: Same as command
    """
    return self.command('clientlist', {}, options)
  
  def get_client_info(self, clid):
    """
    Retrieves information for a specific client.
    
    @param clid: Client's Id
    @type clid: str
    
    @return: Same as command
    """
    return self.command('clientinfo', {'clid' : clid})