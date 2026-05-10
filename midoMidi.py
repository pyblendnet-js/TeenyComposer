import sys, math  #python3 -m pip install mido
from mido import Message, MidiFile, MidiTrack

class midiParser():

  min_note = 0
  max_note = -1
  duration = 0
  tracks = [[],]  #first empty track
  track_nms = ["track1",]
  track_program = [0,]
  track_enable = [True,]
  verbose = False
  ticks_per_beat = 480   #1000 would be one beat per second at default tempo
  
  def load(self,fid):
    self.midi_file = MidiFile(fid)
    print(f"MIDI Type: {self.midi_file.type}")
    self.ticks_per_beat = self.midi_file.ticks_per_beat
    print(f"Ticks per Beat: {self.ticks_per_beat}")
    print(dir(self.midi_file))
  #enddef
  
  def save(self,fid):
    mid = MidiFile()
    for ti,track_nm in enumerate(self.track_nms):
      track = MidiTrack()
      track.name = track_nm
      print("Saving track:",track_nm)
      mid.tracks.append(track)
      track.append(Message('program_change', program=self.track_program[ti], time=0))
      ltm = 0
      for env in self.tracks[ti]:
        if self.track_enable[ti]:
          dtm = env[2] - ltm  # delta time since last event
          ltm = env[2]
          if env[1] == 0:  #note off event
            track.append(Message('note_off', note=env[0], velocity=0, time=int(dtm)))
          else:
            track.append(Message('note_on', note=env[0], velocity=env[1], time=int(dtm)))
          #endif
        #endif
      #endfor
    #endfor 
    mid.save(fid)
  #enddef

  def scan(self,target_track = ""):
    self.tracks = []
    self.track_nms = []
    self.track_program = []
    # Iterate through all messages in all tracks
    self.min_note = 1000
    self.max_note = -1000
    sharps = 0
    for ti, track in enumerate(self.midi_file.tracks):
        print(f'Track {ti}: {track.name}')
        #print(track.name, target_track)
        note_i = [0,]*128
        tm = 0
        if target_track == "" or track.name == target_track:
          self.track_nms.append(track.name)
          self.track_program.append(0);
          self.tracks.append([])
          self.track_enable.append(True)
          for msg in track:
              # Print each message and its time delta
              mstr = str(msg)
              if self.verbose:
                print(msg)
              if msg.type == "program_change":  #let us assume that each track has only one program
                self.track_program[-1] = msg.program
              elif msg.type == "note_on" or msg.type == "note_off":
                #print(msg.type)
                n = msg.note
                vel = msg.velocity
                if self.verbose:
                  print(n)  #," = ",getNote(n))
                if n < self.min_note:
                  self.min_note = n
                if n > self.max_note:
                  self.max_note = n
                tm += msg.time
                if msg.type == "note_on":
                  note_i[n] = len(self.tracks[ti])
                  self.tracks[ti].append((n,vel,tm,0))  #track, note, vel, start_time, temp end_time - replaced once we know
                else:
                  env = self.tracks[ti][note_i[n]]  #get the note on event that should exist
                  self.tracks[ti][note_i[n]] = (env[0],env[1],env[2],tm)  #append end time to that event
                  self.tracks[ti].append((n,0,tm,env[2])) #note end = note, vel=0, end_time, start_time  (note reversal)
                if self.verbose:
                  print(tm,n)
              #endif
          #endfor
        #endif
    #endfor
    print(f"{sharps} sharps")
    print("Min note:",self.min_note)
    print("Max note:",self.max_note)
    self.duration = tm
    print("Duration:",tm)
  #enddef

  def save_track(self,fid,track_nr=0):
    with open(fid,"w") as f:
      f.write(f"program={self.track_program[track_nr]}\n")
      f.write(f"ticks_per_beat={self.ticks_per_beat}\n")
      track = self.tracks[track_nr]
      for env in track:
        f.write(f"{env[0]},{env[1]},{env[2]},{env[3]}\n")  #note, vel, start_tm, end_tm
      #endfor
    #endwith
  #enddef
  
  def load_track(self,fid,track_nm,track_nr=-1):
    if track_nr < 0 and len(self.tracks[0]) == 0:
      track_nr = 0  #so this is the first track
    #endif  
    if track_nr < 0 or track_nr > len(self.track_nms):
      track_nr = len(self.track_program)
      self.track_nms.append(track_nm)
      self.track_program.append(0)
      self.tracks.append([])
      self.track_enable.append(True)
    else:
      self.track_nms[track_nr] = track_nm
      self.track_program[track_nr] = 0
      self.track_enable[track_nr] = True
    #endif
    track = self.tracks[track_nr]
    with open(fid,"r") as f:
      l = f.readline()
      while l:     
        lp = l.strip().split("=")
        if len(lp) != 2:
          break
        #endif
        if lp[0] == "program":
          track_prog = int(lp[1])
        elif lp[0] == "ticks_per_beat":
          ticks_per_beat = int(lp[1])
          if ticks_per_beat != self.ticks_per_beat:
            print(f"Ticks per beat old={self.ticks_per_beat} new={ticks_per_beat}")
            self.ticks_per_beat = ticks_per_beat
        else:
          break
        l = f.readline() 
      #endwhile       
      while l:
        lp = l.strip().split(",")
        print(lp)
        nenv = (int(lp[0]),int(lp[1]),int(lp[2]),int(lp[3]))
        print(nenv)
        if nenv[2] > self.duration:
          self.duration = nenv[2]
        inserted = False
        for i, env in enumerate(track):
          if env[2] > nenv[2]:
            self.tracks[track_nr].insert(i,nenv)
            inserted = True
            break
          #endif  
        #endfor
        if not inserted:
          self.tracks[track_nr].append(nenv)
        #endif
        l = f.readline()
      #endwhile
    #endwith
    self.test_range(track)
    print("Duration:",self.duration)
  #enddef
  
  def test_all_range(self):
    self.min_note = 128
    self.max_note = 0
    for ti,track in enumerate(self.tracks):
      if self.track_enable[ti]:
        self.test_range(track)
      #endif
    #endfor
    print("Min note:",self.min_note)
    print("Max note:",self.max_note)
  #enddef
  
  def test_range(self,track):
    for env in track:
      self.check_range(env[0])
    #endfor
  #enddef
  
  def check_range(self,n):  
    if n < self.min_note:
      self.min_note = n
      print("min:",n)
    #endif  
    if n > self.max_note:
      self.max_note = n
      print("max:",n)
    #endif
  #enddef    
  
  def delete_track(self,ti):
    print("Deleting track:",ti)
    del self.track_nms[ti]       
    del self.track_program[ti]
    del self.tracks[ti]
    self.test_all_range()
  #enddef
  
  def add_track(self,nm):
    self.track_nms.append(nm)
    self.track_program.append(0)
    self.tracks.append([],)
    self.track_enable.append(True)
  #enddef
  
  def remove_notes(self,start_n,end_n,start_tm,end_tm,ti):
    track = self.tracks[ti]
    del_cnt = 0
    for n in range(start_n,end_n):
      print("Remove note:",n," for ",start_tm," to ",end_tm)
      del_cnt += self.remove_note(n,start_tm,end_tm,track)
    #endfor
    print("Removed ",del_cnt,"notes")
    return del_cnt
  #enddef
    
  def remove_note(self,n,start_tm,end_tm,track):
    del_cnt = 0
    while(True):
      i = self.find_existing_note(n,start_tm,end_tm,track)
      if i < 0:
        break
      j = self.find_matching_noteoff(n,i,track)
      print("Erase note at ", i)
      del track[i]
      del_cnt += 1
      if j >= 0:
        del track[j]
      #endif
    #endwhile
    self.test_all_range()
    return del_cnt                    
  #enddef
  
  def mod_note(self,n,start_tm,end_tm,ti=0,vel=64):
    track = self.tracks[ti]
    i = self.find_existing_note(n,start_tm,end_tm,track)
    if i >= 0:
      j = self.find_matching_noteoff(n,i,track)
      track[i] = (n,vel,start_tm,end_tm)
      if j >= 0:
        track[j] = (n,0,end_tm,start_tm)  #note reversal of times for noteoff event
      self.duration = max(self.duration,end_tm)
      return i
    #endif
    return -1
  #enddef 
  
  def find_existing_note(self,n,start_tm,end_tm,track):
    #print("Look for existing notes in ",self.tune)
    end_scan_tm = max(start_tm,end_tm)  #new note is defined at this stage
    for i, env in enumerate(track):
      print("Compare with:",env)
      if env[2] > end_scan_tm:
        print("no more notes to clean up")
        break
      #endif
      if env[0] != n:  #not the same pitch
        continue
      if env[1] > 0:  # this is a noteon event
        if env[3] < start_tm or env[2] > end_tm:
          #this event ends before our new note starts or
          #this event doesn't start before end of our new note ends
          print("Skip")  #so we can keep looking
          continue
        #endif
      #endif
      print("Existing note found:",env, " at ", i)
      return i
    #endfor
    return -1
  #enddef 
  
  def find_matching_noteoff(self,start_i,n,track):
    for i in range(start_i,len(track)):
      env = track[i]
      if env[0] == n:
        if env[1] != 0:
          print("error - noteon found before note off")
          return -2  #  else:   #this is a note off event
        #endif
        return i
      #endif
    #endfor
    print("Matching noteoff event not found")
    return -1
  #enddef  

  def insert_note(self,n,start_tm,end_tm,ti,vel):
    track = self.tracks[ti]
    note_env = (n,vel,start_tm,end_tm)
    print("Insert ",note_env," into track:",ti)
    self.check_range(note_env[0])
    i = 0
    track = self.tracks[ti]
    while i < len(track):
      env = track[i]
      if env[2] > note_env[2]:  #this event past intended event
        if i < len(track):
          self.tracks[ti].insert(i,note_env)
        else:
          self.tracks[ti].append(note_env)
        #endif
        i += 1 #to allow for the inserted event
        if note_env[1] == 0:  #vel already set to 0 so this is noteoff
          return  #note off has already been inserted
        note_env = (n,0,end_tm,start_tm)   #note reversal of time for noteoff
        self.duration = max(self.duration,end_tm)
        #keep going and look for place to add note off
      #endif
      i += 1
    #endwhile
    self.tracks[ti].append(note_env)
    if note_env[1] != 0:  #vel is not zero
      note_env = (note_env[0],0,note_env[3],note_env[2])   #note reversal of time for noteoff
      self.tracks[ti].append(note_env)
    #endif
  #enddef 
  
  def transpose(self,delta):
    for track in self.tracks:
      for i,env in enumerate(track):
        track[i] = (env[0]+delta,env[1],env[2],env[3])
      #endfor
    #endfor
  #enddef
  
  def find_index(self,tm):
    tm_i = [0,]*len(self.tracks)
    for ti,track in enumerate(self.tracks):
      for i,env in enumerate(track):
        if env[2] > tm:
          tm_i[ti] = max(0,i-1)
          break
        #endif
      #endfor
    #endfor
    return tm_i
  #enddef
        
#endclass
