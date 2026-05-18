import fluidsynth

class fluid():

  fonts = {}
  instruments = {}

  def __init__(self):
    self._synth = fluidsynth.Synth()
    self._synth.start()
  #enddef
  
  def stop(self):
    self._synth.system_reset()
  #enddef
  
  def close(self):
    self._synth.system_reset()
    self._synth.delete()
  #endif  
  
  def set_font(self, font = "GeneralUser-GS", id="font0"):
    self.fonts[id] = self._synth.sfload(font + ".sf2")
    #try:
    if True:
      with open(font + ".txt") as f:
        for l in f.readlines():
          li = l.index(" ")
          instr = l.strip()[li:]
          #print(instr)
          lpp = l[:li].split("-")
          #print(lpp)
          self.instruments[instr] = (int(lpp[0]),int(lpp[1]))
          #print(self.instruments[instr])
        #endfor
      #endwith
    #except:
    #  print("No instrument list - use list-sf2.sh to create file")
    #endtry
    return self.instruments.keys()
  #enddef
    
  def set_program(self, channel=0, program=0, font_id="font0"):
    #print(channel,program,font_id)
    #program_select(channel, soundfontid, banknum, presetnum)
    #channel#10 = 9 is for drums
    programs = list(self.instruments.keys())
    #print("Programs:",len(programs))
    #print(self.instruments)
    if program < len(programs):
      bank,preset = self.instruments[programs[program]]
    else:
      bank = 0
      preset = program
    #endif  
    try:
      self._synth.program_select(channel, self.fonts[font_id], bank, preset)
      print(f"Channel {channel} set to bank {bank} preset {preset}")
    except:
      print(f"{self.fonts[font_id]} doesn't have bank {bank} and preset {preset}")
    #endtry  
  #enddef
  
  def play(self, note, vel=64, chan = 0):
      if vel == 0:
        self._synth.noteoff(chan,note)
      else:
        self._synth.noteon(chan,note,vel)
      #endif
  #enddef

#endclass
