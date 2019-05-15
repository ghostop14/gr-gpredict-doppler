#!/usr/bin/env python
# 
# Adapted from Nagle's doppler.py to fit rotor
# 

from gnuradio import gr
import sys
import threading
import time
import socket
import pmt


class rotor_runner(threading.Thread):
  def __init__(self, blockclass, minEl, gpredict_host, gpredict_port, verbose):
    threading.Thread.__init__(self)

    self.gpredict_host = gpredict_host
    self.gpredict_port = gpredict_port
    self.verbose = verbose

    self.blockclass = blockclass
    self.minEl = minEl
    
    self.stopThread = False
    self.clientConnected = False
    self.sock = None
    
  def run(self):
    try:
      bind_to = (self.gpredict_host, self.gpredict_port)
      server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      server.bind(bind_to)
      server.listen(0)
    except Exception as e:
      print("[rotor] Error starting listener: %s" % str(e))
      sys.exit(1)
          
    time.sleep(0.5) # TODO: Find better way to know if init is all done
    curState = False
	
    while not self.stopThread:
      print("[rotor] Waiting for connection on: %s:%d" % bind_to)
      self.clientConnected = False
      self.sock, addr = server.accept()
      self.clientConnected = True
      print("[rotor] Connected from: %s:%d" % (addr[0], addr[1]))

      cur_az = -9999.0
      cur_el = -9999.0
      
      while not self.stopThread:
        try:
          data = self.sock.recv(1024)
        except:
          data = None
          
        if not data or self.stopThread:
          break

        data = data.decode()

        # Allow for multiple commands to have come in at once.  For instance Frequency and AOS / LOS
        data = data.rstrip('\n') # Prevent extra '' in array
        commands = data.split('\n')
        
        for curCommand in commands:
          if curCommand.startswith('P'):
            # if self.verbose: print("[rotor] Incoming rotor command: %s" % data)
            rotctl=curCommand.split()
            az=float(rotctl[1])
            el=float(rotctl[2])
          
            if (cur_az != az) or (cur_el != el):
              self.blockclass.sendAzEl(az,el)
            
            if cur_az != az:
              if self.verbose: print("[rotor] New Azimuth: %f" % az)
              cur_az = az
            
            if cur_el != el:
              if self.verbose: print("[rotor] New Elevation: %f" % az)
            
              # deal with state based on elevation
              if (not curState) and el >= self.minEl:
                curState = True
                self.blockclass.sendState(curState)
              elif (curState and el < self.minEl):
                curState = False
                self.blockclass.sendState(curState)
              
              cur_el = el

            # Send report OK response
            try:
              self.sock.sendall(b"RPRT 0\n")
            except:
              pass
          elif curCommand.startswith('p'):
            try:
              self.sock.sendall(b"p: %.1f %.1f\n" % (cur_az,cur_el))
            except:
              pass
          elif curCommand == 'S':
            # Seen with disconnect Disconnect
            # Send report OK response
            try:
              self.sock.sendall(b"RPRT 0\n")
            except:
              pass   
          elif curCommand == 'q':
            # Disconnect
            # Send report OK response
            try:
              self.sock.sendall(b"RPRT 0\n")
            except:
              pass   
          else:
            print("[rotor] Unknown command: %s" % curCommand)
            # Send report OK response
            try:
              self.sock.sendall(b"RPRT 0\n")
            except:
              pass   

      self.sock.close()
      self.clientConnected = False
      self.sock = None
      if self.verbose: print("[rotor] Disconnected from: %s:%d" % (addr[0], addr[1]))


class rotor(gr.sync_block):
  def __init__(self, minEl, gpredict_host, gpredict_port, verbose):
    gr.sync_block.__init__(self, name = "GPredict Rotor", in_sig = None, out_sig = None)
    
    self.port = gpredict_port
    self.thread = rotor_runner(self, minEl, gpredict_host, gpredict_port, verbose)
    self.thread.start()
    
    self.message_port_register_out(pmt.intern("az_el"))
    self.message_port_register_out(pmt.intern("state"))

  def stop(self):
    self.thread.stopThread = True
    if self.thread.clientConnected:
      self.thread.sock.close()
    else:
      # Have to force a connection to unblock the accept
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost",self.port))
        time.sleep(0.1)
        s.close()
      except:
        pass
      
    return True
    
	     
  def sendAzEl(self,az,el):
    meta = {}      
    meta['az'] = az
    meta['el'] = el
    self.message_port_pub(pmt.intern("az_el"),pmt.cons( pmt.to_pmt(meta), pmt.PMT_NIL ))

  def sendState(self,state):
    meta = {}  
    
    if (state):    
      meta['state'] = 1
    else:
      meta['state'] = 0
      
    self.message_port_pub(pmt.intern("state"),pmt.cons( pmt.to_pmt(meta), pmt.PMT_NIL ))
