#!/usr/bin/python
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

from teamspeak3 import teamspeak
from time import sleep, time

# Basic Configuration
Config = {
          # Server Settings
          'ServerHost'    : '127.0.0.1',    # Server's IP or Hostname
          'ServerPort'    : '10011',        # Server's port (query), default port: 10011
          'ServerId'      : '1',            # Virtual server ID
          'QueryLogin'    : 'serveradmin',  # Query login
          'QueryPass'     : '11111111',     # Query password
          'Nickname'      : 'R2D2',         # Bot's nickname
  
          # AFK Settings
          'AFKEnable'     : True,
          'AFKChannel'    : '1',            # AFK Channel ID
          'AFKTimer'      : '30',           # Duration in minutes
}

class AFKSampleBot:
  """
  A sample of an AFK Bot using the teamspeak3 python library.
  """
  
  def __init__(self):
    """
    Class constructor.
    """
    self.ts3        = teamspeak(Config['ServerHost'], Config['ServerPort'])
    self.afk_queue  = {}
    self.idle_timer = int(Config['AFKTimer']) * 60
    
  def connect(self):
    """
    Connects to the TeamSpeak 3 server.
    """
    self.ts3.connect(Config['ServerId'])
    self.ts3.login(Config['QueryLogin'], Config['QueryPass'])
    self.ts3.command('clientupdate', {'client_nickname': Config['Nickname']})
    
    while True:
      if Config['AFKEnable']:
        self.check_afk_clients()
        
      sleep(5)
  
  # AFK Related Methods
  def is_pending_move(self, clid):
    """
    Checks to see if a client is on the afk queue.
    
    @param clid: Client's Id
    @type clid: str  
    """
    
    for client in self.afk_queue:
      if client == clid:
        return True
    
    return False
  
  def should_move(self, clid):
    """
    Checks to see if a client needs to be moved or not.
    
    @param clid: Client's Id
    @type clid: str
    """
    
    length = time() - self.afk_queue[clid]
    
    # Give the client a 20 second leeway since TeamSpeak doesn't reset 
    # the idle time right away after the user performs an action
    if length > 20:
      return True
    
    return False
  
  def check_afk_clients(self):
    """
    Check's to see which clients are AFK.
    """
    
    # Get the client list
    client_list = self.ts3.get_client_list('-times')
    
    # Iterate through the client list.
    for client in client_list:
      
      # We are going to ignore any client that is not a voice client.
      if client['client_type'] != '0':
        continue
      
      # If the user is already in the AFK channel, we'll continue over to the next client.
      if client['cid'] == Config['AFKChannel']:
        continue
      
      clid = client['clid']
      
      # If the client's idle time exceeds what we allow, we will add the client to the afk
      # queue list. If the client's idle time does notreset after 20 second, we will then
      # move the client.
      if (int(client['client_idle_time']) / 1000) >= self.idle_timer:
        if self.is_pending_move(clid):
          if self.should_move(clid):
            self.ts3.command('clientmove', {'clid': clid, 'cid' : Config['AFKChannel']})
            del self.afk_queue[clid]
    
        else:
          self.afk_queue[clid] = time()
          
      # If the client's idle time reset, we'll check to see if he was in the afk queue, if so,
      # we will kindly take him out.    
      elif self.is_pending_move(clid):
        del self.afk_queue[clid]
    
if __name__ == "__main__":
  sample = AFKSampleBot()
  sample.connect()
  