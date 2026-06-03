# Inspired by Source - https://stackoverflow.com/a/24136884 Posted by Marcin, modified by community. See post 'Timeline' for change history Retrieved 2026-04-29, License - CC BY-SA 3.0

from tkinter import filedialog, simpledialog, messagebox
from tkinter import ttk
import tkinter as tk # this is in python 3.4. For python 2.x import Tkinter
from PIL import Image, ImageTk
import math, os
import midoMidi
#import fluidsynth
import fluid
from datetime import datetime
import platform

parser = midoMidi.midiParser()
synth = fluid.fluid()
instruments = synth.set_font()  #currently loads GeneralUserGS.sf2

def getNoteName(midi_note):
  oc = math.floor(midi_note / 12)
  st = midi_note % 12
  nms = "CCDDEFFGGAAB"
  nm = nms[st] + str(oc)
  if is_sharp(midi_note):
    nm += "# ="
  else:
    nm += "_ ="
  nm += str(midi_note)
  return nm
#enddef

def is_on_stave_line(midi_note):
    treble_lines = [64, 67, 71, 74, 77]
    bass_lines = [45, 48, 52, 55, 59]
    return midi_note in treble_lines or midi_note in bass_lines
#enddef

def is_sharp(midi_note):
  sharp_notes = (1,3,6,8,10)
  st = midi_note % 12
  return st in sharp_notes

class TeenyComposer(tk.Tk):

    filename = ""  #nothing loaded yet
    min_note = 59   #B3
    max_note = 83   #B4
    wide = 1000
    high = 800
    start_note_high = 140
    end_note_high = 80
    note_height = 20
    half_note_height = 10
    note_y_pos = {}
    first_note_line_y = int(high/2)
    last_note_line_y = int(high/2)
    pos_note = []
    x_scale = 1
    start_tm = 0
    end_tm = 20000
    edit_track = 0
    edit_vel = 64
    note_start_x = 120
    track_colors = ("black","blue","green","orange","cyan","brown","grey")
    select_colors = ("orange","red","yellow","blue","purple","black","red")
    play_step = 1  #1 millisecond per tick
    playing = False
    play_index = []
    play_line = None
    cursor_time = 0
    begin_time = 0
    fini_time = 0
    auto_pan = True
    snap = False
    note_playing = -1
    rect = None
    control_pressed = False
    shift_pressed = False
    zero_move = True
    
    render = None

    def __init__(self):
        root = tk.Tk.__init__(self)
        if platform.system() == "Linux":
          self.bind("<Button-4>", self.mouse_wheel)    # For Linux
          self.bind("<Button-5>", self.mouse_wheel)    # For Linux
        else:
          self.bind("<MouseWheel>", mouse_wheel)  # For Windows
        #endif

        self.title("TeenyComposer")
        self.x = self.y = 0
        self.canvas = tk.Canvas(self, width=self.wide, height=self.high, cursor="cross")
        self.canvas.pack(side="top", fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<ButtonPress-2>", self.on_mouse_press)
        self.canvas.bind("<B2-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-2>", self.on_mouse_release)
        self.canvas.bind("<ButtonPress-3>", self.on_mouse_press)
        self.canvas.bind("<B3-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-3>", self.on_mouse_release)
        #load = Image.open("media_icons/play.png")
        #print(load)
        #render = ImageTk.PhotoImage(load)
        #self.render = tk.PhotoImage("play.png")
        #print(self.render)
        #  , image=self.render, compound='left'
        self.play_btn = tk.Button(self, text='Play', bd='4', command=self.play_tune)
        self.play_btn.place(x=10,y=0)
        self.stop_btn = tk.Button(self, text='Stop', bd='4', command=self.stop_tune)
        self.stop_btn.place(x=80,y=0)
        self.stave_btn = tk.Button(self, text='Stave', bd='4', command=self.toggle_stave)
        self.stave_btn.place(x=150,y=0)
        lbl = tk.Label(self, text="Midi:")
        lbl.place(x=260,y=0)
        self.load_btn = tk.Button(self, text='New', bd='4', command=self.new_midi)
        self.load_btn.place(x=300,y=0)
        self.load_btn = tk.Button(self, text='Load', bd='4', command=self.load_midi)
        self.load_btn.place(x=370,y=0)
        self.save_btn = tk.Button(self, text='Save', bd='4', command=self.save_midi)
        self.save_btn.place(x=440,y=0)
        self.saveas_btn = tk.Button(self, text='SaveAs', bd='4', command=self.saveas_midi)
        self.saveas_btn.place(x=510,y=0)
        lbl = tk.Label(self, text="Track:")
        lbl.place(x=655,y=0)
        self.load_track_btn = tk.Button(self, text='Load', bd='4', command=self.load_track)
        self.load_track_btn.place(x=700,y=0)
        self.saveas_track_btn = tk.Button(self, text='SaveAs', bd='4', command=self.saveas_track)
        self.saveas_track_btn.place(x=780,y=0)
        btn = tk.Button(self, text='Quit', bd='4', command=self.quit)
        btn.place(x=900,y=0)
        self.left_btn = tk.Button(self, text='<', bd='4', command=self.shift_left)
        self.left_btn.place(x=self.note_start_x,y=self.high-50)
        self.right_btn = tk.Button(self, text='>', bd='4', command=self.shift_right)
        self.right_btn.place(x=self.wide-50,y=self.high-50)
        self.max_up_btn = tk.Button(self, text='^', bd='4', command=self.shift_max_up)
        self.max_up_btn.place(x=0,y=80)
        self.max_down_btn = tk.Button(self, text='v', bd='4', command=self.shift_max_down)
        self.max_down_btn.place(x=50,y=80)
        lbl = tk.Label(self, text="Transpose:")
        lbl.place(x=220,y=100)
        self.transpose_up_btn = tk.Button(self, text='^', bd='4', command=self.transpose_up)
        self.transpose_up_btn.place(x=300,y=80)
        self.transpose_down_btn = tk.Button(self, text='v', bd='4', command=self.transpose_down)
        self.transpose_down_btn.place(x=350,y=80)
        self.auto_pan_var = tk.IntVar()
        self.auto_pan_var.set(self.auto_pan);
        self.auto_pan_checkbox = ttk.Checkbutton(self, text='autopan', variable=self.auto_pan_var,\
          command=self.auto_pan_checkbox_change)
        self.auto_pan_checkbox.place(x=self.wide/2+150,y=100) 
        self.snap_var = tk.IntVar()
        self.snap_var.set(self.snap);
        self.snap_checkbox = ttk.Checkbutton(self, text='snap', variable=self.snap_var,\
          command=self.snap_checkbox_change)
        self.snap_checkbox.place(x=self.wide/2+250,y=100) 
        self.min_up_btn = tk.Button(self, text='^', bd='4', command=self.shift_min_up)
        self.min_up_btn.place(x=0,y=self.high-50)
        self.min_down_btn = tk.Button(self, text='v', bd='4', command=self.shift_min_down)
        self.min_down_btn.place(x=50,y=self.high-50)
        lbl = tk.Label(self, text="Speed:")
        lbl.place(x=self.wide/2-100,y=100)
        self.add_track_btn = tk.Button(self, text='+', bd='4', command=self.faster)
        self.add_track_btn.place(x=self.wide/2-50,y=80)
        self.add_track_btn = tk.Button(self, text='-', bd='4', command=self.slower)
        self.add_track_btn.place(x=self.wide/2,y=80)
        self.speed_lbl = tk.Label(self, text=f"{self.play_step:0.2f} mS/tick")
        self.speed_lbl.place(x=self.wide/2+50,y=100)
        lbl = tk.Label(self, text="Track:")
        lbl.place(x=10,y=50)
        self.track_combo = ttk.Combobox(self, values = parser.track_nms,width=10)
        self.track_combo.place(x=60,y=50)
        self.track_combo.current(0)
        self.track_combo.bind("<<ComboboxSelected>>",self.track_combo_change)
        lbl = tk.Label(self, text="Program:")
        lbl.place(x=170,y=50)
        mw = 4
        if len(instruments) == 0:
          try:
            with open("general_midi.txt") as f:
              programs = f.readlines()
            #endwith
            for i in range(128):
              programs[i] = str(i) + "=" + programs[i][programs[i].index(" ")+1:-1]
              if len(programs[i]) > mw:
                mw = len(programs[i])
              #endif
            #endfor
          except:
            for i in range(128):
              programs.append(str(i))
            #endfor 
          #endtry
        else:
          programs = list(instruments)
          for p in programs:
            if len(p) > mw:
              mw = len(p)
            #endif
          #endfor            
        #endif
        #print(programs)
        self.track_program_combo = ttk.Combobox(self, values = programs,width=mw)
        self.track_program_combo.place(x=240,y=50)
        self.track_program_combo.current(0)
        self.track_program_combo.bind("<<ComboboxSelected>>",self.track_program_combo_change)
        self.track_show_var = tk.IntVar()
        self.track_show_var.set(parser.track_show[0]);
        self.track_show_checkbox = ttk.Checkbutton(self, text="Show", variable=self.track_show_var,\
          command=self.track_show_checkbox_change)
        self.track_show_checkbox.place(x=440,y=35)
        self.track_mute_var = tk.IntVar()
        self.track_mute_var.set(False);
        self.track_mute_checkbox = ttk.Checkbutton(self, text="Mute", variable=self.track_mute_var,\
          command=self.track_mute_checkbox_change)
        self.track_mute_checkbox.place(x=440,y=50)
        self.track_solo_var = tk.IntVar()
        self.track_solo_var.set(False);
        self.track_solo_checkbox = ttk.Checkbutton(self, text="Solo", variable=self.track_solo_var,\
          command=self.track_solo_checkbox_change)
        self.track_solo_checkbox.place(x=440,y=65)
        self.add_track_btn = tk.Button(self, text='Add Track', bd='4', command=self.add_track)
        self.add_track_btn.place(x=550,y=40)
        self.add_track_btn = tk.Button(self, text='Del Track', bd='4', command=self.del_track)
        self.add_track_btn.place(x=650,y=40)
        self.add_track_btn = tk.Button(self, text='Name Track', bd='4', command=self.nm_track)
        self.add_track_btn.place(x=750,y=40)
        self.edit_track_btn = tk.Button(self, text='Edit Track', bd='4', command=self.track_edit_window)
        self.edit_track_btn.place(x=870,y=40)
        self.smash_btn = tk.Button(self, text='Smash', bd='4', command=self.smash)
        self.smash_btn.place(x=800,y=90)
        self.stretch_btn = tk.Button(self, text='Stretch', bd='4', command=self.stretch)
        self.stretch_btn.place(x=900,y=90)
        
        #self.bind("<Configure>", self.on_window_resize) - too many false triggers
        self.bind("<Key>", self.key_press)
        self.bind("<KeyRelease>", self.key_release)
        self.rect = None

        self.start_x = None
        self.start_y = None

        self.stave = False
        parser.duration = self.end_tm
        self.fini_time = parser.duration
        self.refresh()
    #enddef
    
    def checkForSave(self):
      if len(parser.edit_history) > 0:
        answer = messagebox.askyesnocancel("Quit", "Do you want to save your changes?")
        if answer == None:
          return False
        #endif
        if answer:
          if not self.saveas_midi():
            return False #no file selected or canceled
          #endif
        #endif
      #endif
      return True
    #enddef
    
    def quit(self):
      if self.checkForSave():
        self.destroy()
      #endif
    #endif
    
    def trim_front(self):
        print("Trim front")
        parser.trim_tm(self.cursor_time,True)
        self.cursor_time = 0
        self.refresh()
    #enddef
    
    def trim_rear(self):
        print("Trim rear")
        parser.trim_tm(self.cursor_time,False)
        self.refresh()
    #enddef
    
    def octave_up(self):
        print("octave_up")
        parser.transpose_track(12,self.edit_track)
        self.refresh()
    #enddef
    
    def octave_dn(self):
        print("octave_dn")
        parser.transpose_track(-12,self.edit_track)
        self.refresh()
    #enddef
    
    def select_highest(self):
        print("Select highest")
        parser.top_notes(self.edit_track,int(self.overlap_var.get()))
        self.refresh()
    #enddef
    
    def invert_selection(self):
        print("Invert selection")
        parser.invert_selection(self.edit_track)
        self.refresh()
    #enddef
    
    def select_errors(self):
        print("Select errors")
        parser.select_track_errors(self.edit_track)
        self.refresh()
    #enddef
    
    def track_edit_window(self):
        te = tk.Toplevel()
        te.geometry("350x400") 
        te.title("Track edits")
        te.trim_front_btn = tk.Button(te, text='TrimFront', bd='4', command=self.trim_front)
        te.trim_front_btn.place(x=10,y=10)
        te.trim_front_btn = tk.Button(te, text='TrimRear', bd='4', command=self.trim_rear)
        te.trim_front_btn.place(x=10,y=60)
        te.octave_up_btn = tk.Button(te, text='OctaveUp', bd='4', command=self.octave_up)
        te.octave_up_btn.place(x=10,y=110)
        te.octave_dn_btn = tk.Button(te, text='OctaveDown', bd='4', command=self.octave_dn)
        te.octave_dn_btn.place(x=10,y=160)
        te.select_highest_btn = tk.Button(te, text='Highest', bd='4', command=self.select_highest)
        te.select_highest_btn.place(x=10,y=210)
        lbl = tk.Label(te, text="Overlap:")
        lbl.place(x=100,y=210)
        self.overlap_var = tk.StringVar()
        self.overlap_var.set(str(int(parser.ticks_per_beat/4)))
        te.overlap_entry = tk.Entry(te,textvariable=self.overlap_var)
        te.overlap_entry.place(x=170,y=210)
        te.invert_btn = tk.Button(te, text='Invert Selection', bd='4', command=self.invert_selection)
        te.invert_btn.place(x=10,y=260)
        te.select_error_btn = tk.Button(te, text='Select errors', bd='4', command=self.select_errors)
        te.select_error_btn.place(x=10,y=310)
        self.track_edit_window = te
        te.bind("<Key>", self.key_press)  #keyboard works from both focus
    #enddef
    
    def key_press(self,event):
        #print("Keyboard event:",event)
        #print("State:",event.state)
        if (event.state & 4) != 0:  # 'Control' 
          #print("Control actions")
          if event.keysym == 'z':  #cntrl + z
            print("Undo")
            parser.undo()
            self.refresh()
          elif event.keysym == 'y': #cntrl + y
            print("Redo")
            parser.redo()
            self.refresh()
          elif event.keysym == 'h':  # cntrl + h  #print history
            parser.print_history()
          elif event.keysym == 't':  # cntrl + t  #print track
            parser.print_track(self.edit_track)
          elif event.keysym == 's':  # cntrl + t  #print selection
            parser.print_selection(self.edit_track)
          elif event.keysym == 'c':  # cntrl + c
            print("Copy")
            parser.copy_selected(self.edit_track)
          elif event.keysym == 'x':  # cntrl + x
            print("Cut")
            parser.cut_selected(self.edit_track)
            self.refresh()
          elif event.keysym == 'v':  # cntrl + v
            print("Paste")
            parser.paste_clipboard(self.edit_track,self.cursor_time)
            self.refresh()
          else:
            print("Control + Keyboard event:",event) 
          #endif
        else:
          if event.keysym== 'Tab':
            self.edit_track = (self.edit_track + 1) % len(parser.tracks)
            self.track_combo.current(self.edit_track)
          elif event.keysym== 'Delete':
            print("Delete")
            parser.delete_selected(self.edit_track)
            self.refresh() 
          elif event.keysym== 'Insert':
            print("Insert - does nothing at present - maybe add beat in track")
          elif event.keysym=='Control_L' or event.keysym=='Control_R':
            print("Control on")
            self.control_pressed = True          
          elif event.keysym=='Shift_L' or event.keysym=='Shift_R':
            print("Shift on")
            self.shift_pressed = True          
          else:
            print("Keyboard event:",event) 
          #endif
        #endif        
    #enddef
    
    def key_release(self,event):
        if event.keysym=='Control_L' or event.keysym=='Control_R':
          print("Control off")
          self.control_pressed = False          
        elif event.keysym=='Shift_L' or event.keysym=='Shift_R':
          print("Shift off")
          self.shift_pressed = False          
        #endif        
    #enddef
    
    def mouse_wheel(self,event):
      print("ScrollState:",event.state)
      dtm = self.end_tm - self.start_tm
      if event.num == 4:
        print("4=Up")
        if (event.state & 1) != 0: #shift to increase ticks_per_beat
          parser.ticks_per_beat = int(parser.ticks_per_beat * 1.01)
        elif (event.state & 4) != 0:  #cntrl for zoom out
          self.end_tm = self.start_tm + dtm*1.1
        else:
          self.start_tm = max(0,self.start_tm - dtm*0.1)
          self.end_tm = self.start_tm + dtm
        #endif
        self.refresh()
      elif event.num == 5:
        print("5=Dn")
        if (event.state & 1) != 0: #shift to decrease ticks_per_beat
          parser.ticks_per_beat = int(parser.ticks_per_beat / 1.01)
        elif (event.state & 4) != 0: #cntrl for zoom in
          self.end_tm = self.start_tm + dtm/1.1
        else:  #scroll right
          self.start_tm = max(0,self.start_tm + dtm*0.1)
          self.end_tm = self.start_tm + dtm
        #endif
        self.refresh()
      #endif
    #enddef
    
    def on_window_resize(self, event):  # not used as gets false events
        print("Resize event:",event)
        width = event.width
        height = event.height
        print(f"Window resized to {width}x{height}")
        self.refresh()
    #enddef
    
    def toggle_stave(self):
        self.stave = not self.stave
        self.refresh()
    #enddef_synth.
        
    def refresh(self):
        self.canvas.delete("all")
        if self.stave:
          self.draw_staves()
          self.stave_btn.configure(text ="Piano")
        else:
          self.draw_piano()
          self.stave_btn.configure(text="Stave")
        #endif
        y_tm = self.first_note_line_y - 20
        s_str = "%0.1f"%(self.start_tm,)
        e_str = "%0.1f"%(self.end_tm,)
        self.canvas.create_text(self.note_start_x,y_tm,\
         text=s_str,anchor="w",justify="center",fill="black")
        self.canvas.create_text(self.wide-100,y_tm,text= e_str,anchor="w",justify="right",fill="black")
        if self.start_tm == 0:
          self.left_btn.config(state=tk.DISABLED)
        else:
          self.left_btn.config(state=tk.NORMAL)
        #endif
        #draw position rect
        bx1 = self.note_start_x+80
        bx2 = self.wide-80
        by1 = self.high-self.end_note_high+30
        by2 = self.high-10
        self.canvas.create_rectangle(bx1,by1,bx2,by2)
        bw = bx2-bx1
        if parser.duration > 0:
          px1 = min(bx2,self.start_tm/parser.duration*bw + bx1)
          px2 = min(bx2,self.end_tm/parser.duration*bw + bx1) 
          self.canvas.create_rectangle(px1+4,by1+4,px2-4,by2-4,fill="black")
        #end
        y1 = self.first_note_line_y
        x = self.note_start_x + (self.begin_time-self.start_tm)*self.x_scale
        if x > self.note_start_x and x < self.wide:
          y2 = self.last_note_line_y
        else:
          y2 = y1 
        #endif 
        self.begin_line = self.canvas.create_line(x,y1,x,y2,width=4,fill="green")
        x = self.note_start_x + (self.fini_time-self.start_tm)*self.x_scale
        if x > self.note_start_x and x < self.wide:
          y2 = self.last_note_line_y
        else:
          y2 = y1 
        #endif 
        self.fini_line = self.canvas.create_line(x,y1,x,y2,width=4,fill="blue")
        x = self.note_start_x + (self.cursor_time-self.start_tm)*self.x_scale
        if x > self.note_start_x and x < self.wide:
          y2 = self.last_note_line_y
        else:
          y2 = y1 
        #endif 
        self.play_line = self.canvas.create_line(x,y1,x,y2,width=2,fill="red")
    #enddef
        
    def draw_staves(self):
        nr = 0
        for n in range(self.min_note,self.max_note+1):
          if not is_sharp(n):
            nr += 1
          #endif
        #endfor
        hnr = nr>>1
        
        y = (self.high-self.start_note_high-self.end_note_high)/2 - hnr*self.note_height + self.start_note_high
        self.first_note_line_y = y
        self.note_y_pos = {}
        self.pos_note = []

        for n in range(self.max_note,self.min_note-1,-1):
          ny = y - self.note_height/2
          self.note_y_pos[n] = ny
          self.pos_note.append((ny,n))
          if not is_sharp(n):
            if is_on_stave_line(n):
              self.canvas.create_line(0,y,self.wide,y,width=2)
            #endif
            self.canvas.create_text((0,y+self.note_height/2),text=getNoteName(n),\
            anchor="w",justify="left",fill="black")
            y += self.note_height
          #endif
        #endfor
        self.canvas.create_line(self.note_start_x,self.first_note_line_y,self.note_start_x,y,width=2)
        self.last_note_line_y = y
        
        show_width = self.wide-self.note_start_x
        tm_wide = self.end_tm - self.start_tm
        self.x_scale = show_width/tm_wide
        for ti,track in enumerate(parser.tracks):
          #print("Display track stave:",ti)
          if parser.track_show[ti]:
            for ei,env in enumerate(track):
              if env[1] == 0:  #ignore noteoff events
                continue
              if env[2] > self.end_tm:
                break   #no point going further
              if env[0] > self.min_note and env[0] < self.max_note and env[2] < self.end_tm and env[3] > self.start_tm:
                #print("Show note:",env)
                startTm = max(env[2],self.start_tm)
                endTm = min(env[3],self.end_tm)
                x1 = (startTm - self.start_tm)/tm_wide*show_width
                x2 = (endTm - self.start_tm)/tm_wide*show_width
                y = self.note_y_pos[env[0]]
                #print("N:",y,x1,x2)
                if ti < len(self.track_colors):
                  col = self.track_colors[ti]
                else:
                  col = "purple"
                #endif
                if is_sharp(env[0]):
                  col = "red"
                #endif
                stip = ''
                si = ei*128 + ti
                if si in parser.selected:
                  stip = 'gray50'
                #endif
                self.canvas.create_rectangle(self.note_start_x+x1,y,\
                     self.note_start_x+x2,y+self.note_height,fill=col,outline=col,stipple=stip)
              #endif
            #endfor
          #endif
        #endfor      
    #enddef    

    def draw_piano(self):
        nr = self.max_note - self.min_note +1
        hnr = nr>>1
        
        y = (self.high-self.start_note_high-self.end_note_high)/2 - hnr*self.note_height + self.start_note_high
        self.note_y_pos = {}
        self.pos_note = []
        self.first_note_line_y = y

        for n in range(self.max_note,self.min_note-1,-1):
          if n >= 0 or n < 128:
            self.note_y_pos[n] = y
            self.pos_note.append((y,n))
            self.canvas.create_line(0,y,self.wide,y,width=2)
            col = "black"
            if is_sharp(n):
              self.canvas.create_rectangle(0,y,100,y+self.note_height,fill="black")
              col = "white"
            #endif
            self.canvas.create_text((0,y+self.note_height/2),text=getNoteName(n),\
              anchor="w",justify="left",fill=col)
          y += self.note_height
        #endfor  
        self.canvas.create_line(0,y,self.wide,y,width=2)
        self.last_note_line_y = y

        show_width = self.wide-self.note_start_x
        if self.end_tm <= self.start_tm:  #shouldn't happen
          self.end_tm = self.start_tm + 100
          print("ERROR: end time < start time")
        #end if  
        tm_wide = self.end_tm - self.start_tm
        self.x_scale = show_width/tm_wide
        
        bi = self.start_tm%parser.ticks_per_beat
        bx = self.note_start_x - bi*self.x_scale
        sx = parser.ticks_per_beat*self.x_scale
        while bx < self.wide:
          if bx > self.note_start_x:
            if (bi % parser.denominator) == 0:
              col = "orange"
            else:
              col = "yellow"
            self.canvas.create_line(bx,self.first_note_line_y,bx,y,width=2,fill=col)
          #endif
          bx += sx
          bi += 1
        #endwhile
        self.canvas.create_line(self.note_start_x,self.first_note_line_y,self.note_start_x,y,width=4)
        for ti,track in enumerate(parser.tracks):
          if parser.track_show[ti]:
            #print("Display track:",ti)
            for ei,env in enumerate(track):
              #print("Show note:",env)
              if env[1] == 0:  #ignore noteoff events
                continue
              if env[2] > self.end_tm:
                break   #no point going further
              #endif
              if env[0] > self.min_note and env[0] < self.max_note and env[2] < self.end_tm and env[3] > self.start_tm:
                #print("Show note:",env)
                startTm = max(env[2],self.start_tm)
                endTm = min(env[3],self.end_tm)
                x1 = self.note_start_x+(startTm - self.start_tm)*self.x_scale
                x2 = self.note_start_x+(endTm - self.start_tm)*self.x_scale
                y1 = self.note_y_pos[env[0]]
                y2 = y1+self.half_note_height
                y3 = y1+self.note_height
                #print("N:",y,x1,x2)
                if ti < len(self.track_colors):
                  col = self.track_colors[ti]
                else:
                  col = "purple"
                #endif
                stip = ''
                si = ei*128 + ti
                #print("Selected:",si," in ",parser.selected,"?")
                if si in parser.selected:
                  stip = 'gray50'
                #endif
                #self.canvas.create_rectangle(x1,y1,x2,y3,fill=col)
                self.canvas.create_polygon(x1,y1,x2,y2,x2,y3,x1,y3,fill=col,outline=col,stipple=stip)
              #endif
            #endfor
          #endif
        #endfor      
    #enddef
    
    def find_note(self,y):
        for np in self.pos_note:  #scan (y,n) values
          if y > np[0] and y < np[0] + self.note_height:
            return np
          #endif
        #endfor
        return None
    #enndef

    def _draw_image(self):
         self.im = Image.open('./resource/lena.jpg')
         self.tk_im = ImageTk.PhotoImage(self.im)
         self.canvas.create_image(0,0,anchor="nw",image=self.tk_im)
    #enddef    

    def on_mouse_press(self, event):
        #print(dir(event))
        #print(event)
        self.note_playing = -1
        self.start_x = event.x
        self.start_y = event.y
        self.start_typ = event.num
        self.zero_move = True
        if event.num == 1 and self.control_pressed:  #for multi select
          self.start_typ = 3
        #endif
        if event.y < self.first_note_line_y or event.y > self.last_note_line_y:
          return
        # save mouse drag start position
        np = self.find_note(event.y)
        if not np:
          return
        #endif
        note = np[1]
        if event.x < self.note_start_x:
          synth.set_program(self.edit_track,parser.track_program[self.edit_track])
          synth.play(note,64,self.edit_track)
          print(f"Play {note} on")
          self.note_playing = note
          return
        #endif
        if event.num == 1:
          self.start_y = np[0]  #note vertical position
          #print(np)
        #endif  
   #enddef    

    def on_mouse_move(self, event):
        if event.y < self.first_note_line_y or event.y > self.last_note_line_y or event.x < self.note_start_x:
          return
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        #print("****************",dx,dy)
        if abs(dx) < 2 and abs(dy) < self.note_height:
          return
        #endif
        self.zero_move = False
        if self.start_typ == 2:  #drag view
          #print(dx,dy)
          self.start_x = event.x
          tm_wide = self.end_tm - self.start_tm
          dtm = dx/(self.wide - self.note_start_x)*tm_wide
          self.start_tm = max(0,int(self.start_tm - dtm))
          self.end_tm = self.start_tm + tm_wide
          dnote = int(dy/self.note_height)
          if abs(dnote) > 0:
            self.start_y = event.y
            note_high = self.max_note - self.min_note
            #print("Drag notes by ",dnote)
            self.min_note = max(0,self.min_note+dnote)
            self.max_note = self.min_note + note_high
          #endif
          self.refresh()
          return
        #endif
        if self.start_typ == 1 and len(parser.selected) > 0:
          dnote = math.floor(-dy/self.note_height)
          dtm = dx/self.x_scale
          if self.snap:
            dtm = dtm/self.ticks_per_beat*self.ticks_per_beat;
          #endif
          dtm = round(dtm)  
          parser.shift_selected(dtm,dnote)
          #print(f"Shift:{dtm,dnote}")
          self.refresh()
          self.start_x += dtm*self.x_scale
          self.start_y -= dnote*self.note_height
          return
        #endif
        if not self.rect:
          col = "lightblue"
          # create rectangle if not yet exist
          if self.start_typ == 1:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, fill=col)
          elif self.start_typ == 3:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1)  #no fill
          #endif
        else:
          curX, curY = (event.x, event.y)
          # expand rectangle as you drag the mouse
          if self.start_typ == 1 and event.x > self.start_x:
            self.canvas.coords(self.rect, self.start_x, self.start_y, curX, self.start_y + self.note_height)
          elif self.start_typ == 3 or self.start_x > event.x:
            self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
          #endif
        #endif
    #enddef 
    
    def get_stave_note(self,y):
      n = -1
      for sn in range(self.max_note,self.min_note-1,1):
        dy = y - self.note_y_pos[sn]
        if dy > 0 and dx < self.note_high:
          n  = sn
          if event.num == 1 and self.is_sharp(n):  #this is natural
            n -= 1
          #endif  
        #endif
      #endfor
      return n
    #enddef
    
    def get_piano_note(self,y):
      n = self.max_note - int((y - self.first_note_line_y)/self.note_height)
      return n
    #enddef
    
    def get_note_pressed(self,y):
      if self.stave:  #bit more complicated to work out what note for stave view
        n = self.get_stave_note(y)
      else:
        n = self.get_piano_note(y)  
      #endif
      return n
    #enddef

    def on_mouse_release(self, event):
        #print(self.max_note,self.min_note)
        #print(self.note_y_pos.keys())
        if self.rect:
          self.canvas.delete(self.rect)
          self.rect = None
        #endif
        if self.start_x < self.note_start_x and self.note_playing >= 0:
            synth.play(self.note_playing,0,self.edit_track)
            print(f"Play {self.note_playing} off")
            self.note_playing = -1
            return
        #endif
        if event.y < self.first_note_line_y or event.y > self.last_note_line_y:
          return
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        #print("****************",dx,dy)
        if self.zero_move:
          print("No move")
          if event.num == 2:  #move the time cursor
            y1 = self.first_note_line_y
            y2 = self.last_note_line_y
            # x should be opposite of
            #         x = self.note_start_x + (tm-self.start_tm)*self.x_scale
            tm = int((event.x - self.note_start_x)/self.x_scale + self.start_tm)
            if self.snap:
              tm = int(round(tm / parser.ticks_per_beat) * parser.ticks_per_beat)
            if self.control_pressed:
              self.begin_time = tm
              print("Begin time=",tm)
              #if self.begin_line:
              #  self.canvas.coords(self.begin_line, event.x, y1, event.x, y2)
              #endif
            elif self.shift_pressed:
              self.fini_time = tm
              print("Fini time=",tm)
              #if self.fini_line:
              #  self.canvas.coords(self.fini_line, event.x, y1, event.x, y2)
              #endif
            else:
              self.cursor_time = tm
              #if self.play_line:
              #  self.canvas.coords(self.play_line, event.x, y1, event.x, y2)
              #endif
              self.begin_time = 0
              self.fini_time = parser.duration
            #endif             
            self.play_index = parser.find_index(self.cursor_time)
            self.refresh()
          elif event.num == 1:  #select existing notes
            n = self.get_note_pressed(self.start_y)
            if n < 0 or n >= 128:  #midi limits
              return
            #endif
            tm_wide = self.end_tm - self.start_tm
            stave_wide = self.wide - self.note_start_x
            tm = int(self.start_tm + (event.x - self.note_start_x)*tm_wide/stave_wide)
            parser.select_existing(n,tm,self.edit_track,self.control_pressed)
            self.refresh()
          #endif
          return
        else:
          if self.start_typ == 1 and len(parser.selected) > 0:
            print("Correct order")
            parser.correct_note_order()  #things may have got muddled during a shift_selected
            self.refresh()
            return
          #endif
        #endif  
        if event.num == 3:
          zoom_tm = True
          zoom_note = True
          if abs(dx) > abs(dy)*2:
            zoom_note = False
          elif abs(dy) > abs(dx)*2:  
            zoom_tm = False
          #endif 
          if zoom_tm: 
            if dx < 0:
              print("zoom out tm")
              self.scale_tm()
            else:
              print("zoom in tm")
              current_tm_wide = self.end_tm - self.start_tm
              stave_wide = self.wide - self.note_start_x
              new_tm_wide = current_tm_wide * dx / stave_wide
              self.start_tm += (self.start_x - self.note_start_x)*current_tm_wide/stave_wide
              self.end_tm = self.start_tm + new_tm_wide
              print(f"Show tm from: {self.start_tm} to {self.end_tm}")
            #endif
          #endif
          if zoom_note:
            if dy < 0:
              print("zoom out note")
              self.scale_notes()
            else:  
              current_notes_high = self.max_note - self.min_note
              print(self.note_y_pos)
              print("Max Note:",self.max_note," Min Note:",self.min_note)
              print("y max:",self.first_note_line_y)
              print("y_min:",self.last_note_line_y)
              stave_high = self.last_note_line_y - self.first_note_line_y
              new_notes_high = current_notes_high * dy / stave_high
              print("Stave high:", stave_high)
              print("New notes high:",new_notes_high)
              self.max_note -= math.floor((self.start_y - self.first_note_line_y)*current_notes_high/stave_high)
              self.min_note = math.floor(self.max_note - new_notes_high)
              print(f"Show notes from: {self.min_note} to {self.max_note}")
            #endif
          #endif
          self.canvas.delete(self.rect)
        #elif event.num == 2:  #drag view - all done in mouse move, but if this proves too slow then restore
        #  tm_wide = self.end_tm - self.start_tm
        #  dtm = dx/(self.wide - self.note_start_x)*tm_wide
        #  self.start_tm = max(0,self.start_tm + dtm)
        #  self.end_tm = self.start_tm + tm_wide
        #  note_high = self.max_note - self.min_note
        #  dnote = int(dy/self.note_height)
        #  if abs(dnote) > 0:
        #    self.min_note = max(0,self.min_note+dnote)
        #    self.max_note = self.min_note + note_high
        #  #endif
        elif event.num == 1:
          n = self.get_note_pressed(self.start_y)
          print("Start note:", n)
          if n > self.max_note:
            self.max_note = n
          elif n < self.min_note:
            self.min_note = n
          #endif
          tm_wide = self.end_tm - self.start_tm
          stave_wide = self.wide - self.note_start_x
          print("TmWide:",self.end_tm,"-",self.start_tm,"=",tm_wide)
          print("Stave wide:",stave_wide)
          start_tm = int(self.start_tm + (self.start_x - self.note_start_x)*tm_wide/stave_wide)
          end_tm = int(self.start_tm + (event.x - self.note_start_x)*tm_wide/stave_wide)
          if self.snap:
            start_tm = int(round(start_tm / parser.ticks_per_beat) * parser.ticks_per_beat)
            end_tm = int(round(end_tm / parser.ticks_per_beat) * parser.ticks_per_beat)
          #endif
          print("Start-end:",start_tm,end_tm)
          if self.control_pressed:  #this is note selection not marking
            n2 = self.get_note_pressed(event.y)
            print("End note:", n2)
            if n2 > self.max_note:
              self.max_note = n2
            elif n2 < self.min_note:
              self.min_note = n2
            #endif           
            parser.select_range(n,n2,start_tm,end_tm,self.edit_track,self.shift_pressed)
          else:
            if n < 0 or n >= 128:  #midi limits
              return
            #endif
            if start_tm > end_tm:  #back swipe means erase
              if self.stave:  #bit more complicated to work out what note for stave view
                end_n = self.get_stave_note(event.y)
              else:
                end_n = self.get_piano_note(event.y)  
              #endif
              if end_n < 0 or end_n >= 128:  #midi limits
                return
              #endif
              print("Marked end note:", end_n)
              if n > self.max_note:
                self.max_note = end_n
              elif n < self.min_note:
                self.min_note = end_n
              #endif
              parser.remove_notes(n,end_n,end_tm,start_tm,self.edit_track)  #note start end reversed 
              if self.rect:
                self.canvas.delete(self.rect)
              #endif
            else:  #add or modify note
              if self.edit_track >= len(parser.tracks):  # shouldn't happen
                print("Edit track beyond existing tracks")
                return -1
              #endif  
              i = parser.mod_note(n,start_tm,end_tm,self.edit_track,self.edit_vel)
              if i < 0:
                print("Insert noteon at ",start_tm)
                parser.insert_note(n,self.edit_vel,start_tm,end_tm,self.edit_track)
              #endif
            #endif
          #endif
        #endif
        self.refresh()
    #enddef 
    
    def new_midi(self):
      if self.checkForSave():
        parser.clear()
        self.track_combo.config(values = parser.track_nms)
        self.track_combo.current(0)
        self.track_program_combo.current(parser.track_program[0])
      #endif
      self.refresh()
    #enddef
    
    def load_midi(self):
      self.filename = filedialog.askopenfilename(filetypes = (("Midi","*.mid"),("All files","*.*")))
      if self.filename:
          # Read and print the content (in bytes) of the file.
          #print(self.filename)
          parser.load(self.filename)
          self.play_step = parser.tempo / parser.ticks_per_beat / 1000
          self.speed_lbl.config(text= f"{self.play_step:0.2f} mS/tick")
          self.title("TeenyComposer = " + self.filename)
      else:
          print("No file selected.")
          return
      #endif
      if len(parser.track_nms) > 0:
        self.track_combo.config(values = parser.track_nms)
        self.track_combo.current(0)
        self.track_program_combo.current(parser.track_program[0])
      #endif
      self.scale_tm()
      self.scale_notes()
      self.test_shift_up_down_limits()
      #self.refresh() - included in 
    #enddef
    
    def load_track(self):
      self.filename = filedialog.askopenfilename(filetypes = (("Track","*.trk"),("All files","*.*")))
      if not self.filename:
          print("No file selected.")
          return
      #endif
      # Read and print the content (in bytes) of the file.
      print("Loading:",self.filename)
      fp = os.path.splitext(os.path.basename(self.filename))  #split into name and 
      np = fp[0].split("_")  #get track part of name
      track_name = np[-1]
      print("Track:",track_name)
      parser.load_track(self.filename,track_name)  #will place at end of existing tracks
      self.title("TeenyComposer = " + self.filename)
      if len(parser.track_nms) > 0:
        self.track_combo.config(values = parser.track_nms)
        self.track_combo.current(0)
        self.track_program_combo.current(parser.track_program[0])
      #endif
      self.scale_tm()
      self.scale_notes()
      self.test_shift_up_down_limits()
      #self.refresh() - included in 
    #enddef
    
    def save_midi(self):
      parser.save(self.filename)
    #enddef
    
    def saveas_midi(self):
      self.filename = filedialog.asksaveasfilename(filetypes = (("Midi","*.mid"),("All files","*.*")))
      if self.filename:
          # Read and print the content (in bytes) of the file.
          #print(self.filename)
          parser.save(self.filename)
          self.title("TeenyComposer = " + self.filename)
          return True
      else:
          print("No file selected.")
          return False
      #endif
    #enddef
    
    def saveas_track(self):
      track_name = self.track_combo.get()
      if len(self.filename) > 0:
        fnm = os.path.splitext(os.path.basename(self.filename))[0]
        if fnm.endswith(track_name):
          track_name = fnm
        else: 
          track_name = fnm + "_" + track_name
      else:
        track_name = datetime.now().strftime("%Y%02m%02d-%02H%02M%02S_") + track_name
      trackfilename = filedialog.asksaveasfilename(initialfile = track_name,filetypes = (("Track","*.trk"),("All files","*.*")))
      if trackfilename:
          # Read and print the content (in bytes) of the file.
          #print(trackfilename)
          parser.save_track(trackfilename,self.track_combo.current())
          if self.filename == "":
            self.filename = trackfilename.split("_")[0] + ".mid"  #assumes no underscore in base path
            self.title("TeenyComposer = " + self.filename)
          #endif  
      else:
          print("No file selected.")
      #endif
    #enddef
    
    def scale_tm(self):
      self.start_tm = 0
      self.end_tm = max(20000,parser.duration + 4*parser.ticks_per_beat)
    #enddef
    
    def scale_notes(self):
      parser.test_all_range()
      dn = parser.max_note - parser.min_note
      spare = (self.high - self.start_note_high - self.end_note_high)/self.note_height - dn
      ts = int(spare/2)
      self.max_note = parser.max_note + ts
      self.min_note = parser.min_note - ts
      print("Min note:",self.min_note)
      print("Max note:",self.max_note)
      self.test_shift_up_down_limits()
    #enddef  
    
    def shift_left(self):
      if self.start_tm == 0:
        return
      dt = self.end_tm-self.start_tm
      self.start_tm -= dt*0.5
      if self.start_tm < 0:
        self.start_tm = 0
      #endif
      self.end_tm = self.start_tm + dt
      self.refresh()
    #enddef
    
    def shift_right(self):
      dt = self.end_tm-self.start_tm
      self.start_tm += dt*0.5
      self.end_tm = self.start_tm + dt
      self.refresh()
    #enddef
    
    def shift_max_up(self):
      self.max_note += 1
      self.test_shift_up_down_limits()
    #enddef
    
    def shift_max_down(self):
      self.max_note -= 1
      self.test_shift_up_down_limits()
    #enddef
    
    def shift_min_up(self):
      self.min_note += 1
      self.test_shift_up_down_limits()
    #enddef
    
    def shift_min_down(self):
      self.min_note -= 1
      self.test_shift_up_down_limits()
    #enddef
    
    def test_shift_up_down_limits(self):
      if self.max_note >= 127:
        self.max_note = 127
        self.max_up_btn.config(state=tk.DISABLED)
      else:
        self.max_up_btn.config(state=tk.NORMAL)
      #endif
      if self.max_note <= self.min_note+4:
        self.max_note = self.min_note+4
        self.max_down_btn.config(state=tk.DISABLED)
      else:
        self.max_down_btn.config(state=tk.NORMAL)
      #endif
      if self.min_note >= self.max_note-4:
        self.min_note = self.max_note-4
        self.min_up_btn.config(state=tk.DISABLED)
      else:
        self.min_up_btn.config(state=tk.NORMAL)
      #endif
      if self.max_note < 0:
        self.max_note = 0
        self.min_down_btn.config(state=tk.DISABLED)
      else:
        self.min_down_btn.config(state=tk.NORMAL)
      #endif
      self.refresh()
    #enddef  
  
    def add_track(self):
      new_track = "Track "+str(len(parser.track_nms)+1)
      self.edit_track = len(parser.track_nms)     
      parser.add_track(new_track) 
      self.track_combo.config(values = parser.track_nms)
      self.track_combo.current(len(parser.track_nms)-1)
      self.track_program_combo.current(0)
    #enddef
    
    def del_track(self):
      ti = self.track_combo.current()
      print(f"Preparing to delete track: {ti} of {len(parser.track_nms)} track_nms")
      if ti < 0:
        return
      if len(parser.track_nms) < 2:
        print("Track delete abort: There must be at least one track")
        return
      #endif  
      parser.delete_track(ti)
      self.refresh()
      if ti >= len(parser.track_nms):
        ti -= 1  #go to previous otherwise next
      self.track_combo.config(values = parser.track_nms)
      self.track_combo.current(ti)
      self.track_program_combo.current(parser.track_program[ti])
    #enddef
    
    def nm_track(self):
      nm = simpledialog.askstring("Input", "Enter track name:")
      if not nm:
        return
      #endif
      if len(nm) == 0:
        return
      #endif
      parser.track_nms[self.track_combo.current()] = nm
      self.track_combo.config(values = parser.track_nms)
      self.track_combo.current(self.edit_track)  #to refresh combo
    #enddef
    
    def smash(self):
      parser.smash(self.begin_time,self.fini_time)
      self.cursor_time = self.begin_time
      self.begin_time = 0
      self.fini_time = parser.duration 
      self.refresh()
    #enddef
    
    def stretch(self):
      parser.stretch(self.begin_time,self.fini_time)
      self.refresh()
    #enddef
    
    def track_combo_change(self,ev):
      print("Change:",ev)
      self.edit_track = self.track_combo.current()
      self.track_program_combo.current(parser.track_program[self.edit_track])
      print("Track " + self.track_combo.get() + "selected ",self.edit_track)
      self.track_show_var.set(parser.track_show[self.edit_track])
      self.track_mute_var.set(parser.track_mute[self.edit_track])
      self.track_solo_var.set(False) #otherwise too confusing
    #enddef
    
    def track_program_combo_change(self,ev):
      print("Change:",ev)
      parser.track_program[self.track_combo.current()]= self.track_program_combo.current()
      print("Track " + self.track_combo.get() + " program changed to:" + self.track_program_combo.get())
    #enddef
    
    def track_show_checkbox_change(self):
      print("Track show changed for:",self.track_combo.current()," to ",self.track_show_var.get())
      parser.track_show[self.track_combo.current()] = self.track_show_var.get();
      self.refresh()
    #enddef
    
    def track_mute_checkbox_change(self):
      print("Track mute changed for:",self.track_combo.current()," to ",self.track_mute_var.get())
      parser.track_mute[self.track_combo.current()] = self.track_mute_var.get()
      self.refresh()
    #enddef
    
    def track_solo_checkbox_change(self):
      print("Track solo changed for:",self.track_combo.current()," to ",self.track_solo_var.get())
      if self.track_solo_var.get():
        parser.track_solo = self.edit_track
      else:
        parser.track_solo = -1
      #endif  
      self.refresh()
    #enddef
       
    def auto_pan_checkbox_change(self):
      self.auto_pan = self.auto_pan_var.get();
    #enddef
    
    def snap_checkbox_change(self):
      self.snap = self.snap_pan_var.get();
    #enddef
    
    def play_tune(self):
      if self.playing:
        self.playing = False
        self.play_btn.config(text="play")
      else:
        self.play_index = [0]*len(parser.tracks)
        #print(parser.track_program)
        for ti,tp in enumerate(parser.track_program):
          synth.set_program(ti,tp)
        #endfor
        self.play_btn.config(text="pause")
        self.playing = True
        self.play_next()
    #enddef
    
    def stop_tune(self):
      synth.stop()
      self.playing = False
      self.play_btn.config(text="play")
      #self.canvas.delete(self.play_line)
      #self.play_line = None
      self.cursor_time = self.begin_time  #in milliseconds
    #enddef
    
    def play_next(self):
      #print("Cursor callback:",self.cursor_time)
      x = self.note_start_x + (self.cursor_time-self.start_tm)*self.x_scale
      y1 = self.first_note_line_y
      y2 = self.last_note_line_y
      if self.auto_pan:
        if x < self.note_start_x or x > self.wide:
          self.end_tm = self.cursor_time + self.end_tm - self.start_tm
          self.start_tm = self.cursor_time
          x = self.note_start_x
          self.refresh()
        #endif
      elif x < self.note_start_x and x >= self.wide:
        y2 = y1 
      #endif
      #print("Cursor x:",x,y1,y2)
      if self.play_line: 
        self.canvas.coords(self.play_line, x, y1, x, y2)
      is_playing = False #assumption
      for ti,track in enumerate(parser.tracks):
        if parser.track_solo >= 0:
          if parser.track_solo != ti:
            continue
          #endif
        elif parser.track_mute[ti]:
          continue
        #endif
        while self.play_index[ti] < len(track):
          env = track[self.play_index[ti]]
          if env[2] > self.cursor_time:
            break
          #endif
          print(self.play_index[ti]," Playing event:",env)
          synth.play(env[0],env[1],ti)  #channel = track for the moment  
          self.play_index[ti] += 1
        #endwhile
        if self.play_index[ti] < len(track):
          is_playing = True
        #endif  
      #endfor
      if not is_playing:
        self.stop_tune() #reached end
      elif self.playing:
        self.cursor_time += self.play_step  # in milliseconds
        if self.cursor_time > self.fini_time:
          self.stop_tune()
        else:
          self.after(1,self.play_next)  #poll every millisecond
        #endif
      #endif
    #enddef
    
    def faster(self):
      self.play_step *= 1.2
      self.speed_lbl.config(text= f"{self.play_step:0.2f} mS/tick")
    #enddef
    
    def slower(self):
      self.play_step /= 1.2
      self.speed_lbl.config(text= f"{self.play_step:0.2f} mS/tick")
    #enddef
    
    def transpose_up(self):
      parser.transpose_all(1)
      self.refresh()
    #enddef
    
    def transpose_down(self):
      parser.transpose_all(-1)
      self.refresh()
    #enddef
    
#endclass

if __name__ == "__main__":
    app = TeenyComposer()
    app.mainloop()
