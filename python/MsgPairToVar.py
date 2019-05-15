#!/usr/bin/env python
# 

from gnuradio import gr
import pmt

class MsgPairToVar(gr.sync_block):
  def __init__(self, callback):
    gr.sync_block.__init__(self, name = "MsgPairToVar", in_sig = None, out_sig = None)
    
    self.callback = callback
             
    self.message_port_register_in(pmt.intern("inpair"))
    self.set_msg_handler(pmt.intern("inpair"), self.msgHandler)   

  def msgHandler(self, msg):
    try:    
      newVal = pmt.to_python(pmt.cdr(msg))
      
      self.callback(newVal)
      
    except Exception as e:
      print("[MsgPairTOVar] Error with message conversion: %s" % str(e))
    
  def stop(self):
    return True
