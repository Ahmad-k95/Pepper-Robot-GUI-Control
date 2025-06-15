#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
from functools import partial
import functions as fc
from app_state import AppState
from frames.frame0 import Frame0
from frames.frame1 import Frame1
from frames.frame2 import Frame2
from frames.frame3 import Frame3
from frames.frame4 import Frame4
from frames.frame5 import Frame5
import app_events as ap
from vicon_trigger import ArduinoSerialManager

window = tk.Tk()
window.title("Pepper Manager")
window.geometry("1470x898")
window.resizable(width=False, height=False)
app_state = AppState()

button_width = 8
button_height = 1

frame0 = Frame0(window, app_state, button_width, button_height)
frame1 = Frame1(window, app_state, button_width, button_height)
frame2 = Frame2(window, app_state, button_width, button_height)
frame3 = Frame3(window, app_state, button_width, button_height)
frame4 = Frame4(window, app_state, button_width, button_height)
frame5 = Frame5(window, app_state, button_width, button_height)

window.bind("<KeyPress>", partial(ap.manual_ctrl_in_thread, window=window, app_state=app_state))
app_state.frame2.post_motion_listbox.bind('<<ListboxSelect>>', partial(ap.select_motion, app_state=app_state))
app_state.frame2.posture_listbox.bind("<<ListboxSelect>>", partial(ap.select_posture, app_state=app_state))
app_state.frame2.motions_listbox.bind('<<ListboxSelect>>', partial(ap.select_motion, app_state=app_state))

app_state.frame3.experiments.bind('<<ComboboxSelected>>', partial(ap.select_experiment, app_state=app_state))

window.protocol("WM_DELETE_WINDOW", partial(ap.on_closing, master=window, app_state=app_state))

fc.load_data(app_state)
fc.load_prompt(app_state)
fc.clear_video_frame(app_state)

app_state.arduino_manager = ArduinoSerialManager(log_widget=app_state.frame3.log_terminal)
window.after(100, fc.initialize_ports(app_state))

window.mainloop()
