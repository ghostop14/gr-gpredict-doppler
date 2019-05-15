#!/usr/bin/env python
# 

from gnuradio import gr
import pmt

class AzElLimit(gr.sync_block):
  def __init__(self,el_min,el_max,az_min,az_max):
    gr.sync_block.__init__(self, name = "Az El Limit", in_sig = None, out_sig = None)

    self.el_min = el_min
    self.el_max = el_max
    self.az_min = az_min
    self.az_max = az_max
    
    self.curState = False
    
    # if min <= max, we're normal mode.  If not we're inverted.
    
    if az_min <= az_max:
      if (az_min == az_max):
        print("[azel_limit] WARNING azimuth min = azimuth max.  Results would only be good for 1 degree setting.")
        
      self.az_inverted = False
    else:
      self.az_inverted = True
      
    # Set up messages    
    self.message_port_register_in(pmt.intern("az_el"))
    self.message_port_register_out(pmt.intern("state"))
    self.set_msg_handler(pmt.intern("az_el"), self.azelHandler)   

  def azelHandler(self, pdu):
    meta = pmt.to_python(pmt.car(pdu))
    
    try:    
      az = int(meta['az'])
      el = int(meta['el'])
      
      if (self.el_min <= el) and (el <= self.el_max):
        el_good = True
      else:
        el_good = False
        
      if not self.az_inverted:
        # min <= max
        if (self.az_min <= az) and (az <= self.az_max):
          az_good = True
        else:
          az_good = False
      else:
        # min > max
        # Example: az_min = 300.0, az_max = 40.0
        # az >= 300.0 (up to 360.0 of course but assuming that's all we'd get from the input)
        # or az <= az_max is a good window
        if (az >= self.az_min) or (az <= self.az_max):
          az_good = True
        else:
          az_good = False
          
      if az_good and el_good:
        # Check if we're transitioning to in-zone
        if not self.curState:
          self.curState = True
          self.sendState(True)
      else:
        # Check if we're transitioning out
        if self.curState:
          self.curState = False
          self.sendState(False)
    except Exception as e:
      print("[azel_limit] Error with az/el message: %s" % str(e))
      print(str(meta))
      
  def sendState(self,state):
    meta = {}  
    
    if (state):    
      meta['state'] = 1
    else:
      meta['state'] = 0
      
    self.message_port_pub(pmt.intern("state"),pmt.cons( pmt.to_pmt(meta), pmt.PMT_NIL ))
      