import sys, math, copy
#python3 -m pip install mido
from mido import Message, MetaMessage, MidiFile, MidiTrack

class midiParser():

  min_note = 0
  max_note = -1
  duration = 0
  tracks = [[],]  #first empty track
  track_nms = ["track1",]
  track_program = [0,]
  track_show = [True,]
  track_mute = [False,]
  track_solo = -1 #otherwise is track so solo
  verbose = False
  ticks_per_beat = 480
  tempo =600000    # uSec per per quarter note
  numerator = 4
  denominator = 4
  clocks_per_click = 24
  notated_32nd_notes_per_beat = 8
  
  edit_history = []  #record (track,event_index,type,env) where type=(0=addition,1=deletion,3=modification delete)
  undo_index = 0
  rec_disable = False  #used to prevent undo history being lost during redo or over written with undo
  
  selected = []
  clipboard = []
  tune_stack = []
  
  #1000 would be one beat per second at default tempo
  
  def clear(self):
    self.min_note = 0
    self.max_note = -1
    self.duration = 0
    self.tracks = [[],]  #first empty track
    self.track_nms = ["track1",]
    self.track_program = [0,]
    self.track_show = [True,]
    self.track_mute = [False,]
    self.track_solo = -1 #otherwise is track so solo
    self.edit_history = []
    self.undo_index = 0
    self.selected = []
    self.clipboard = []
    self.tune_stack = []
    self.ticks_per_beat = 480
    self.tempo =600000    # uSec per per quarter note
    self.numerator = 4
    self.denominator = 4
    self.clocks_per_click = 24
    self.notated_32nd_notes_per_beat = 8
  #enddef
  
  def load(self,fid):
    self.clear()
    self.midi_file = MidiFile(fid)
    print(f"MIDI Type: {self.midi_file.type}")
    self.ticks_per_beat = self.midi_file.ticks_per_beat
    print(f"Ticks per Beat: {self.ticks_per_beat}")
    #self.temp = self.midi_file.tempo
    #print(f"Tempo: {self.tempo} uSec/quarter note")
    #print(dir(self.midi_file))
    self.scan()
  #enddef
  
  def save(self,fid):
    if not fid.endswith(".mid"):
      fid += ".mid"
    #endif  
    mid = MidiFile()
    for ti,track_nm in enumerate(self.track_nms):
      track = MidiTrack()
      track.name = track_nm
      print("Saving track:",track_nm)
      mid.tracks.append(track)
      if ti == 0:  #first track
        track.append(MetaMessage('set_tempo', tempo=self.tempo, time=0))
        track.append(MetaMessage('time_signature',numerator = self.numerator,\
            denominator =self.denominator , clocks_per_click =self.clocks_per_click , \
             notated_32nd_notes_per_beat = self.notated_32nd_notes_per_beat, time=0))
      #endif  
      track.append(Message('program_change', program=self.track_program[ti], time=0))
      ltm = 0
      note_i = [-1,]*128    #-1 to indicate no note on for this note yet
      for env in self.tracks[ti]:
        dtm = env[2] - ltm  # delta time since last event
        ltm = env[2]
        if env[1] == 0:  #note off event
          if note_i[env[0]] > 0:
            track.append(Message('note_off', note=env[0], velocity=0, time=int(dtm)))
            note_i[env[0]] = -1
          else:
            print("Ignoring note_off without note_on")
          #endif
        else:
          track.append(Message('note_on', note=env[0], velocity=env[1], time=int(dtm)))
          note_i[env[0]] = 1
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
        note_i = [-1,]*128    #-1 to indicate no note on for this note yet
        tm = 0
        if target_track == "" or track.name == target_track:
          if len(track.name) > 0:
            self.track_nms.append(track.name)
          else:
            self.track_nms.append(f"track{ti}")
          #endif
          self.track_program.append(0);
          self.tracks.append([])
          self.track_show.append(True)
          self.track_mute.append(False)
          self.track_solo = -1
          for msg in track:
              # Print each message and its time delta
              mstr = str(msg)
              if self.verbose or msg.is_meta:
                print(msg)
              #print(msg.type)
              if msg.type == "program_change":  #let us assume that each track has only one program
                self.track_program[-1] = msg.program
              elif msg.type == "set_tempo":
                self.tempo = msg.tempo
              elif msg.type == "time_signature":
                self.numerator = msg.numerator
                self.denominator = msg.denominator
                self.clocks_per_click = msg.clocks_per_click
                self.notated_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
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
                if msg.type == "note_on" and vel > 0:
                  note_i[n] = len(self.tracks[ti])
                  self.tracks[ti].append((n,vel,tm,0))  #track, note, vel, start_time, temp end_time - replaced once we know
                elif note_i[n] < 0:
                  print("Deleting noteoff without noteon")
                else:
                  env = self.tracks[ti][note_i[n]]  #get the note on event that should exist
                  print("Correcting start note end at:",note_i[n]," to ",tm) 
                  self.tracks[ti][note_i[n]] = (env[0],env[1],env[2],tm)  #append end time to that event
                  self.tracks[ti].append((n,0,tm,env[2])) #note end = note, vel=0, end_time, start_time  (note reversal)
                  note_i[n] = -1
                #endif
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
    if not fid.endswith(".trk"):
      fid += ".trk"
    #endif
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
      self.track_show.append(True)
      self.track_mute.append(False)
      self.track_solo = -1
    else:
      self.track_nms[track_nr] = track_nm
      self.track_program[track_nr] = 0
      self.track_show[track_nr] = True
      self.track_mute[track_nr] = False
      self.track_solo = -1
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
        #print(lp)
        nenv = (int(lp[0]),int(lp[1]),int(lp[2]),int(lp[3]))
        #print(nenv)
        if nenv[2] > self.duration:
          self.duration = nenv[2]
        inserted = False
        for i, env in enumerate(track):
          if env[2] > nenv[2]:
            self.tracks[track_nr].insert(i,nenv)
            self.adjust_selected(track,i,1)
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
      if self.track_show[ti]:
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
    self.selected = []  #too hard to adjust it safely
  #enddef
  
  def add_track(self,nm):
    self.track_nms.append(nm)
    self.track_program.append(0)
    self.tracks.append([],)
    self.track_show.append(True)
    self.track_mute.append(False)
    self.track_solo = -1
  #enddef
  
  def print_track(self,ti):
    print("track ",ti)
    track = self.tracks[ti]
    for env in track:
      print(env)
    #endfor
  #enddef
  
  def print_history(self):
    print("undo index:",self.undo_index)
    if self.undo_index > 0:
      print("Current history:",self.edit_history[:-self.undo_index])
    else:
      print("Current history:",self.edit_history)
    #endif
  #enddef
  
  def rec_history(self,edit):
    if self.rec_disable:  #happens when doing redo so that history isn't erased
      return
    print("Record this:",edit)
    if len(edit) > 3:
      env = edit[3]
      if env[1] == 0:  #don't record noteoff events
        return
      #endif
    #endif
    if self.undo_index > 0 and self.undo_index < len(self.edit_history):
      for edit in self.edit_history[-self.undo_index:]:
        if edit[2] == 3:
          self.prune_tune_stack(edit[1])
      self.edit_history = self.edit_history[:-self.undo_index]
      self.undo_index = 0
    #endif
    self.edit_history.append(edit)
  #enddef
  
  def push_tune(self):
    cp = copy.deepcopy(self.tracks)
    print("stack copy is:",cp)
    self.tune_stack.append(cp)
    print("Tune stack:",len(self.tune_stack))
  #enddef
  
  def pop_tune(self):
    if len(self.tune_stack) > 0:
      print("Tune stack:",len(self.tune_stack))
      self.tracks = self.tune_stack.pop()
    #endif
  #enddef
  
  def prune_tune_stack(self,from_here):
    #free up tune stack for unnecessary redos
    self.tune_stack = self.tune_stack[:from_here]
  #endif
  
  def undo(self):
    print("undo index:",self.undo_index)
    print("Current history:",self.edit_history)
    self.rec_disable = True
    if self.undo_index < len(self.edit_history):
      self.undo_index += 1
      edit = self.edit_history[-self.undo_index]
      #track = self.tracks[edit[0]]
      if edit[2] == 3:  #full copy
        self.pop_tune()
        self.duration += edit[1]
        #self.begin_time = edit[0]
        #self.fini_time += edit[1]
      else:
        env = edit[3]
        if edit[2] == 0:  #insert
          self.delete_note(edit[0],edit[1])
        elif edit[2] == 1:  #deletion
          self.insert_note(env[0],env[1],env[2],env[3],edit[0])
        elif edit[2] == 2:  #modification
          #nenv = track[edit[1]]
          self.delete_note(edit[0],edit[1])
          self.insert_note(env[0],env[1],env[2],env[3],edit[0])
        #endif
      #endif
    #endif
    self.rec_disable = False
  #enddef
  
  def redo(self):
    print("undo index:",self.undo_index)
    print("Current history:",self.edit_history)
    self.rec_disable = True
    if self.undo_index > 0:
      edit = self.edit_history[-self.undo_index]
      self.undo_index -= 1
      #track = self.tracks[edit[0]]
      if edit[2] == 3:
        self.push_tune()
        self.duration -= edit[1]
        #self.begin_time = edit[0]
        #self.fini_time -= edit[1]
      else:
        env = edit[3]
        if edit[2] == 0:  #insert type
          self.insert_note(env[0],env[1],env[2],env[3],edit[0])
        elif edit[2] == 1:  #deletion
          self.delete_note(edit[0],edit[1])
        elif edit[2] == 2:  #modification
          #nenv = track[edit[1]]
          self.delete_note(edit[0],edit[1])
          self.insert_note(env[0],env[1],env[2],env[3],edit[0])
        #endif
      #endif
    #endif  
    self.rec_disable = False
  #enddef         
  
  def remove_notes(self,start_n,end_n,start_tm,end_tm,ti):
    track = self.tracks[ti]
    del_cnt = 0
    for n in range(start_n,end_n):
      print("Remove note:",n," for ",start_tm," to ",end_tm)
      del_cnt += self.remove_note(n,start_tm,end_tm,ti)
    #endfor
    print("Removed ",del_cnt,"notes")
    return del_cnt
  #enddef
    
  def remove_note(self,n,start_tm,end_tm,ti):
    track = self.tracks[ti]
    del_cnt = 0
    while(True):
      i = self.find_existing_note(n,start_tm,end_tm,track)
      if i < 0:
        break
      #j = self.find_matching_noteoff(i+1,n,track)
      #print("Erase note at ", i,j)
      del_cnt += 1
      self.delete_note(ti,i)
      #if j >= 0:
      #  del track[j]  #must erase noteoff first
      #endif
      #del track[i]
    #endwhile
    self.test_all_range()
    return del_cnt                    
  #enddef
  
  def mod_note(self,n,start_tm,end_tm,ti=0,vel=64):
    track = self.tracks[ti]
    i = self.find_existing_note(n,start_tm,end_tm,track)
    if i >= 0:  #found one
      self.delete_note(ti,i)
      self.insert_note(n,vel,start_tm,end_tm,ti)
    #endif
    return i
  #enddef 
  
  def select_range(self,n1,n2,stm,etm,ti=0,shift=False):
    print(f"Select note range {n1} to {n2} and from tick:{stm} to {etm}")
    track = self.tracks[ti]
    top_note = max(n1,n2)
    bot_note = min(n1,n2)
    for i, env in enumerate(track):
      if env[1] == 0:
        continue
      if env[0] >= bot_note and env[0] <= top_note and env[2] > stm and env[2] < etm:
        print("Select event at:",i,"for track:",ti)
        ei = i*128+ti
        if shift:
          if ei in self.selected:
            j = self.selected.index(ei)
            del self.selected[j]
          #endif  
        else:
          if ei in self.selected:
            continue
          else:  
            self.selected.append(ei)
          #endif
        #endif
      #endif
    #endfor
  #enddef
  
  def select_existing(self,n,tm,ti=0,cntrl=False):
    print("Select existing note:",n,"at tick:",tm)
    track = self.tracks[ti]
    if not cntrl:
      self.clear_selected()
    #endif
    i = self.find_existing_note(n,tm,tm,track)
    if i >= 0:
      print("Select event at:",i,"for track:",ti)
      ei = i*128+ti
      if not cntrl:
        self.selected = [ei,]
      elif ei in self.selected:
        j = self.selected.index(ei)
        del self.selected[j]
      else:
        self.selected.append(ei)
      #endif
    #endif
  #enddef
  
  def clear_selected(self):
    self.selected = []
  #enddef
  
  def invert_selection(self,ti):
    track = self.tracks[ti]
    temp_sel = list(self.selected)
    #print("Tempsel:",temp_sel)
    self.selected = []
    for i,env in enumerate(track):
      if env[1] == 0:
        continue #ignore note off
      #endif
      ei = i*128 + ti
      if not ei in temp_sel:
        #print("Append:",ei)
        self.selected.append(ei)
      #endif
    #endfor  
  #enddef
  
  def shift_selected(self,dtm,dnote):
    # shift notes for graphic purposes - correct_note_order must be called later 
    print("dtm:",dtm)
    for si in self.selected:
      ti = si & 0x7f
      ni = si>>7
      env = self.tracks[ti][ni]
      j = self.find_matching_noteoff(ni+1,env[0],self.tracks[ti])
      #print(f"For track {ti} index {ni} found note_off at:{j}")
      self.tracks[ti][ni] = (env[0] + dnote,env[1],env[2] + dtm,env[3] + dtm)
      if j > 0:
        self.tracks[ti][j] = (env[0] + dnote,0,env[3] + dtm,env[2] + dtm)
      #endif
    #endfor
  #enddef
  
  def correct_note_order(self):
    for ti,track in enumerate(self.tracks):
      for ci in range(1000):  # for small moves, this is probably the fastes way
        print("Corrections pass:",ci)
        error_found = False
        prev_env = None
        for ni,env in enumerate(track):
          if ni > 0 and env[2] < prev_env[2]:
            #these two are out of order, so swap
            print(f"Swap {ni} for {ni-1}")
            error_found = True
            track[ni-1] = env
            track[ni] = prev_env
            #swap selected indexes
            ei1 = (ni-1)*128 + ti
            ei2 = ni*128 + ti
            if ei1 in self.selected:
              i1 = self.selected.index(ei1)
            else:
              i1 = -1
            #end
            if ei2 in self.selected:
              i2 = self.selected.index(ei2)
            else:
              i2 = -1
            #endif
            if i1 >= 0:            
              self.selected[i1] = ei2
              print(f"Selected at {i1} altered to {ei2}")
            #endif
            if i2 >= 0:  
              self.selected[i2] = ei1
              print(f"Selected at {i2} altered to {ei1}")
            #endif
          else:
            prev_env = env
          #endif
        #endfor
        if not error_found:
          break
        #endif
      #endwhile  
    #endfor
  #enddef
    
  def process_selected(self,action,nti):
    i = 0
    while i <  len(self.selected):
      print(f"Processing item {i} from {self.selected}")
      si = self.selected[i]  #can't use self.selected directly as it may be adjusted during process action
      ti = si & 0x7f  #this is the track where the event was selected
      if ti >= len(self.tracks):
        continue
      #endif  
      ni = si >> 7
      track = self.tracks[ti]
      if ni > len(track):
        print(f"Selected event at {ni} is past length of track {len(track)}")
        continue
      #endif
      if action(ti,ni):  #if returns False, then a delete action has removed item from selected
        i += 1  #advance to next item
      #endif
    #endfor
  #enddef
  
  def copy_action(self,ti,ni):
    track = self.tracks[ti]
    self.clipboard.append(track[ni])
    return True
  #enddef
  
  def copy_selected(self,ti):
    self.clipboard = []
    self.process_selected(self.copy_action,ti)
    return True  
  #enddef
  
  def cut_selected(self,ti):
    self.copy_selected(ti)
    self.delete_selected(ti)
    return True
  #enddef
  
  def paste_clipboard(self,ti,paste_tm):
    start_tm = -1
    for env in self.clipboard:
      if start_tm < 0 or env[2] < start_tm:
        start_tm = env[2]
      #endif
    #endof
    for env in self.clipboard:
      s_tm = env[2] - start_tm + paste_tm
      e_tm = s_tm + env[3] - env[2]
      i = self.insert_note(env[0],env[1],s_tm,e_tm,ti)
      if i >= 0:
        self.selected.append(i*128 + ti)
    #endfor
  #enddef
  
  def delete_note(self,ti,ni):
    track = self.tracks[ti]
    if ni >= len(track):
      print(f"Note not found ni:{ni} >= len(track):{len(track)}")
      return
    #endif
    env = track[ni]
    print(f"Delete note {env} at pos {ni} track {ti} within {len(track)} events")
    self.rec_history((ti,ni,1,tuple(track[ni])))
    j = self.find_matching_noteoff(ni+1,env[0],track)
    print(f"Remove note at pos: {ni} and {j}")
    if j > 0:
      del track[j]
      self.adjust_selected(ti,j,-1)
    del track[ni]
    self.adjust_selected(ti,ni,-1)
    ei = ni*128 + ti
    if ei in self.selected:
      i = self.selected.index(ei)
      if i >= 0:
        del self.selected[i]
      #endif
    #endif
    return False
  #enddef
  
  def delete_selected(self,ti):
    self.process_selected(self.delete_note,ti)
    self.selected = []
  #enddef
  
  def adjust_selected(self,ti,i,di):
    # i is the location of the resent addition or deletion
    # di is 1 for insertions and -1 for deletions
    print(f"Adjust select for location {i} by {di}")
    for si in range(len(self.selected)):
      se = self.selected[si]
      ei = se >> 7  #tm
      eti = se & 0x7f  #track
      #print("Compare tracks:",eti,ti)
      if eti != ti:  #only adjust the selection for the current track
        continue
        #print("Compare loc:",di,ei,i)
      #endif
      if (di < 0 and ei > i) or (di > 0 and ei >= i):
        ei += di
        #print("Adj loc:", si,ei,eti)
        self.selected[si] = ei*128 + eti
      #endif
    #endfor    
  #enddef
  
  def print_selection(self,ti):
    track = self.tracks[ti]
    for si in self.selected:
      if ti != (si & 0x7F):
        continue  #not this track
      #endif
      ni = si >> 7
      if ni < len(track):
        print(f"Select item {ni} at {track[ni]}")
      else:
        print(f"Select item {ni} is past length of track= {len(track)}")
      #endif
    #endfor
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
      if env[1] == 0:  # this is a noteoff event
        continue
      if env[3] < start_tm or env[2] > end_tm:
        #this event ends before our new note starts or
        #this event doesn't start before end of our new note ends
        continue
      #endif
      print("Existing note found:",env, " at ", i)
      return i
    #endfor
    return -1
  #enddef 
  
  def find_matching_noteoff(self,start_i,n,track):
    #print("Track:",track)
    #print("Start_i:",start_i)
    for i in range(start_i,len(track)):
      env = track[i]
      #print("Testing at ",i," for noteoff:",env)
      if env[0] == n:
        if env[1] != 0:
          print(f"error - noteon found before note off = {env}")
          return -2  #  else:   #this is a note off event
        #endif
        return i
      #endif
    #endfor
    print("Matching noteoff event not found")
    return -1
  #enddef
  
  def select_track_errors(self,ti):
    track = self.tracks[ti]
    self.selected = []
    notes_on = [False]*128
    for ni,env in enumerate(track):
      if env[1] > 0:
        j = self.find_matching_noteoff(ni+1,env[0],track)
        if j < 0:
          print(f"  for note:{env} pos {ni}")
          self.selected.append(ni*128 + ti)
        notes_on[env[0]] = True
      else:
        if not notes_on[env[0]]:
          print(f"Error: Note off without note on for {env} at {ni}")
        notes_on[env[0]] = False  
      #endif
    #endfor
  #enddef  

  def insert_note(self,n,vel,start_tm,end_tm,ti):
    track = self.tracks[ti]
    note_env = (n,vel,start_tm,end_tm)
    print("Insert ",note_env," into track:",ti)
    self.duration = max(self.duration,end_tm)
    self.check_range(note_env[0])
    i = 0
    ri = -1 #return position of the new note
    track = self.tracks[ti]
    while i < len(track):
      env = track[i]
      if env[2] > note_env[2]:  #this event past intended event
        if i < len(track):
          self.tracks[ti].insert(i,note_env)
          self.adjust_selected(ti,i,1)
          self.rec_history((ti,i,0,tuple(note_env)))  #0 type is noteon
        else:
          self.rec_history((ti,len(self.tracks[ti]),0,tuple(note_env)))
          self.tracks[ti].append(note_env)
        #endif
        if note_env[1] == 0:  #vel already set to 0 so this is noteoff
          return ri #note off has already been inserted
        note_env = (n,0,end_tm,start_tm)   #note reversal of time for noteoff
        #keep going and look for place to add note off
        if note_env[1] > 0:
          ri = i;
        #endif
      #endif
      i += 1
    #endwhile
    #this noteon or note off is going onto the end
    self.rec_history((ti,len(self.tracks[ti]),0,tuple(note_env)))
    self.tracks[ti].append(note_env)
    ri = i
    if note_env[1] != 0:  #vel is not zero yet, so need to add note off
      note_env = (note_env[0],0,note_env[3],note_env[2])   #note reversal of time for noteoff
      track.append(note_env)
    #endif
    return i;
  #enddef 
  
  def transpose_all(self,delta):
    for ti,track in enumerate(self.tracks):
      self.transpose_track(delta,ti)
    #endfor
  #enddef
  
  def transpose_track(self,delta,ti):
    track = self.tracks[ti]
    for i,env in enumerate(track):
      ei = i*128 + ti
      #if anything has been selected then only selected is shifted
      if len(self.selected) == 0 or ei in self.selected:
        track[i] = (env[0]+delta,env[1],env[2],env[3])
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
  
  def check_duration(self):
    self.duration = 0
    for ti,track in enumerate(self.tracks):
      if len(track) > 0:
        env = track[-1]
        self.duration = max(self.duration,env[2])
      #endif
    #endif
  #enddef  
  
  def trim_tm(self,tm,before=True):
    for ti,track in enumerate(self.tracks):
      if not self.track_show[ti]:
        continue
      #endif
      del_list = []
      for i,env in enumerate(track):
        if before:
          if env[2] < tm: #starts before cutoff
            if env[1] > 0: #not noteoff
              if env[3] >= tm: #ends after cutoff
                track[i] = (env[0],env[1],0,env[3]-tm)
                j = self.find_matching_noteoff(i+1,env[0],track)
                if j > 0:
                  track[j] = (env[0],0,env[2]-tm,0)
                #endif
              else:
                del_list.append(i)
              #endif  
            else:
              del_list.append(i)
          else:
            track[i] = (env[0],env[1],env[2]-tm,env[3]-tm)
          #endif
        else:  #trim after
          if env[2] <= tm:  #keep everything before this time
            if env[1] > 0: #not noteoff
              if env[3] > tm:
                track[i] = (env[0],env[1],env[2],tm)
                j = self.find_matching_noteoff(i+1,env[0],track)
                if j > 0:
                  track[j] = (env[0],0,tm,env[2])
                #endif
              #endif
            #endif  
          else:
            del_list.append(i)
          #endif
        #endif
      #endfor
      del_list.sort()
      del_list = reversed(del_list)
      for i in del_list:
        del track[i]
    #endfor 
    self.check_duration()   
  #enddef
  
  def top_notes(self,ti,overlap_tolerance):
    track = self.tracks[ti]
    self.selected = []
    for ni in range(len(track)):
      env = track[ni]
      if env[1] == 0:
        continue   #ignore noteoff events
      #endif
      mid_tm = int((env[2] +env[3])/2)
      si = max(0,ni - 10)
      ei = min(len(track)-1,ni+10)
      higher = True #assumption
      for mi in range(si,ei):
        if mi == ni:
          continue  #don't compare with self
        #endif
        print(f"Testing {ni} against {mi}")
        env2 = track[mi]
        if env2[1] == 0:
          continue  #ignore noteoff 
        #endif
        print(env,env2)
        # does env2 start before env ends and ends after env starts  
        if (env[3]-env2[2]) > overlap_tolerance and (env2[3]-env[2]) > overlap_tolerance:  #overlap
          print("Overlap")
          if env2[0] > env[0]:  #this other note is higher
            higher = False
            print("Not higher")
            break
          #endif
        #endif
      #endfor  #finished scanning nearby notes
      if higher:
        print("Add highest:",ni)
        self.selected.append(ni*128 + ti)
    #endfor       
  #enddef
    
  def smash(self,begin_tm,end_tm):
    self.push_tune()
    self.selected = []
    dt = end_tm - begin_tm
    to_delete = []
    copy_edit_history = list(self.edit_history)
    for ti,track in enumerate(self.tracks):
      ttrack = list(track)  #make a copy - hoping this makes things more stable
      for ei,env in enumerate(ttrack):
        if env[1] == 0:
          continue
        #endif
        j = self.find_matching_noteoff(ei+1,env[0],track)
        if env[2] < begin_tm:
          print("Note is before begin")
          if env[3] > begin_tm:
            print("Note finishes after begin")
            #self.delete_note(ti,ei)
            #self.insert_note(env[0],env[1],env[2],begin_tm,ti)
            #the following would be quicker but is irreversable
            track[ei] = (env[0],env[1],env[2],begin_tm)
            if j > 0:
              track[j] = (env[0],0,begin_tm,env[2])
            #endif
          #endif
          continue
        #endif
        if env[2] < end_tm:
          print("Note starts before fini")
          if env[3] > end_tm:
            print("Note ends after fini")
            #self.delete_note(ti,ei)
            #self.insert_note(env[0],env[1],end_tm-dt,env[3]-dt,ti)
            #the following would be quicker but is irreversable
            track[ei] = (env[0],env[1],end_tm-dt,env[3]-dt)
            if j > 0:
              track[j] = (env[0],env[1],env[3]-dt,end_tm-dt)
            #endif
            continue
          else:
            print("Note is within smash")
            to_delete.append(ei)
          #endif
        else:
          print("Note is after smash")  
          #self.delete_note(ti,ei)
          #self.insert_note(env[0],env[1],env[2]-dt,env[3]-dt,ti)
          #the following would be quicker but is irreversable
          track[ei] = (env[0],env[1],env[2]-dt,env[3]-dt)
          if j > 0:
            track[j] = (env[0],0,env[3]-dt,env[2]-dt)
          #endif
        #endif
      #endfor
      to_delete.sort()
      for ni in reversed(to_delete):
        self.delete_note(ti,ni)
      #endfor
    #endfor
    #restore history
    self.edit_history = copy_edit_history   #didn't need to know all those deletes.
    self.rec_history((begin_tm,dt,3))
    self.duration -= dt      
  #enddef
  
  def stretch(self,begin_tm,end_tm):
    self.push_tune()
    self.selected = []
    dt = end_tm - begin_tm
    to_delete = []
    copy_edit_history = list(self.edit_history)
    for ti,track in enumerate(self.tracks):
      ttrack = list(track)  #make a copy - hoping this makes things more stable
      for ei,env in enumerate(ttrack):
        if env[2] < begin_tm or env[3] < begin_tm:  #don't stretch notes
          print("Note is before begin")
          continue
        #endif
        track[ei] = (env[0],env[1],env[2]+dt,env[3]+dt)
      #endfor
    #endfor
  #enddef
        
#endclass
