#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
import time
from naoqi import ALProxy
import tkMessageBox  # type: ignore
import threading
import functions as fc


class Frame0(tk.Frame):
    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=390, height=155, bd=1, relief="solid")
        self.place(x=2, y=2)

        self.app_state = app_state
        self.app_state.frame0 = self

        self.fr_language_var = tk.IntVar()
        self.en_language_var = tk.IntVar(value=1)

        self.build_ui(button_width, button_height)

    def build_ui(self, button_width, button_height):
        self.ip_label = tk.Label(self, text="Enter Robot IP:", font=("Arial", 12))
        self.ip_label.place(x=10, y=10)

        self.ip_entry = tk.Entry(self, width=13)
        self.ip_entry.insert(0, self.app_state.robot_ip)
        self.ip_entry.place(x=140, y=10)

        self.connect_button = tk.Button(self, text="Connect", width=button_width, height=button_height,
                                        command=self.connect_to_robot_in_thread)
        self.connect_button.place(x=280, y=10)

        self.status_label = tk.Label(self, text="Connect!", fg="red")
        self.status_label.place(x=160, y=40)

        self.fr_language_button = tk.Checkbutton(self, text="FR", variable=self.fr_language_var,
                                                 command=self.toggle_language_fr)
        self.fr_language_button.place(x=242, y=50)
        self.en_language_button = tk.Checkbutton(self, text="EN", variable=self.en_language_var,
                                                 command=self.toggle_language_en)
        self.en_language_button.place(x=328, y=50)

        self.wake_button = tk.Button(self, text="Wake", width=button_width, height=button_height,
                                     command=self.wake_in_thread)
        self.wake_button.place(x=10, y=70)
        self.sleep_button = tk.Button(self, text="Sleep", width=button_width, height=button_height,
                                      command=self.sleep_in_thread)
        self.sleep_button.place(x=120, y=70)

        self.stand_init_button = tk.Button(self, text="Pose init", width=button_width, height=button_height,
                                           command=self.stand_init_in_thread)
        self.stand_init_button.place(x=10, y=110)
        self.leds_button = tk.Button(self, text="LEDs", width=button_width, height=button_height,
                                     command=self.leds_control)
        self.leds_button.place(x=120, y=110)

        self.sound_scale = tk.Scale(self, from_=0, to=100, orient="horizontal", label="       Volume",
                                    command=self.update_sound_value,
                                    length=120, width=16, sliderlength=20, troughcolor="blue", sliderrelief="raised")
        self.sound_scale.place(x=250, y=80)
        self.sound_scale.set(50)

    def connect_to_robot_in_thread(self):
        connection_thread = threading.Thread(target=self.connect_to_robot)
        connection_thread.setDaemon(True)
        connection_thread.start()

    def toggle_language_fr(self):
        self.app_state.Language = "French"
        self.en_language_var.set(0)

    def toggle_language_en(self):
        self.app_state.Language = "English"
        self.fr_language_var.set(0)

    def wake_in_thread(self):
        frame3 = self.app_state.frame3
        frame3.log_terminal.insert(tk.END, "> Wake Up\n", "green")
        frame3.log_terminal.yview_moveto(1.0)
        #
        wake_thread = threading.Thread(target=self.wake)
        wake_thread.setDaemon(True)
        wake_thread.start()

    def sleep_in_thread(self):
        frame3 = self.app_state.frame3
        frame3.log_terminal.insert(tk.END, "> Sleep mode\n", "green")
        frame3.log_terminal.yview_moveto(1.0)
        sleep_thread = threading.Thread(target=self.sleep)
        sleep_thread.setDaemon(True)
        sleep_thread.start()

    def stand_init_in_thread(self):
        frame3 = self.app_state.frame3
        frame3.log_terminal.insert(tk.END, "> Stand init\n", "green")
        frame3.log_terminal.yview_moveto(1.0)
        # Create the thread
        stand_init_thread = threading.Thread(target=fc.stand_init, args=(self.app_state,))
        stand_init_thread.setDaemon(True)
        stand_init_thread.start()

    def leds_control(self):
        if not self.app_state.robot_session.isConnected():
            return
        frame3 = self.app_state.frame3
        leds_service = self.app_state.robot_session.service("ALLeds")
        if self.app_state.leds_on:
            leds_service.setIntensity("FaceLeds", 0)
            frame3.log_terminal.insert(tk.END, "> LEDs are OFF\n", "green")
        else:
            leds_service.setIntensity("FaceLeds", 1)
            frame3.log_terminal.insert(tk.END, "> LEDs are ON\n", "green")
        frame3.log_terminal.yview_moveto(1.0)
        self.app_state.leds_on = not self.app_state.leds_on

    def update_sound_value(self, value):
        if not self.app_state.robot_session.isConnected():
            return
        audio_device = ALProxy("ALAudioDevice", self.app_state.robot_ip, self.app_state.robot_port)
        audio_device.setOutputVolume(int(value))

    def connect_to_robot(self):
        self.app_state.robot_ip = self.ip_entry.get()
        frame3 = self.app_state.frame3
        frame4 = self.app_state.frame4
        frame5 = self.app_state.frame5
        self.master.focus()
        if self.app_state.robot_session.isConnected():
            if not self.app_state.pepper_camera is None:
                self.app_state.pepper_camera.release_camera()
            frame3.log_terminal.insert(tk.END, "> Robot is disconnected\n", "red")
            frame3.log_terminal.yview_moveto(1.0)
            s = self.app_state.robot_session.service("ALTextToSpeech")
            s.setLanguage("English")
            s.say("Disconnected!")
            fc.clear_video_frame(self.app_state)
            self.app_state.robot_session.close()
            self.status_label.config(text="Connect!", fg="red")
            if not self.app_state.LLM_process is None:
                self.app_state.LLM_process.terminate()
            frame5.LLM_var.set(False)
            frame4.Aruco_var.set(False)

            frame5.recognized_speech.delete(1.0, tk.END)
        else:
            try:
                self.app_state.robot_session.connect(self.app_state.robot_ip)
            except Exception as e:
                tkMessageBox.showinfo("Warning",
                                      "Invalid Ip address!")
                return
            motion_service = self.app_state.robot_session.service("ALMotion")
            leds_service = self.app_state.robot_session.service("ALLeds")
            leds_service.setIntensity("FaceLeds", 0)

            time.sleep(2)
            s = self.app_state.robot_session.service("ALTextToSpeech")
            s.setLanguage("English")
            audio_device = ALProxy("ALAudioDevice", self.app_state.robot_ip, self.app_state.robot_port)
            audio_device.setOutputVolume(self.sound_scale.get())
            s.say("Connected!")
            fc.stand_init(self.app_state)
            self.status_label.config(text="Connected", fg="green")
            autonomous_life_proxy = ALProxy("ALAutonomousLife", self.app_state.robot_ip, self.app_state.robot_port)
            autonomous_life_proxy.setAutonomousAbilityEnabled("All", False)
            frame3.log_terminal.insert(tk.END, "> Robot is Connected\n", "green")
            frame3.log_terminal.yview_moveto(1.0)

        fc.load_data(self.app_state)
        if self.app_state.robot_session.isConnected():
            frame3.log_terminal.insert(tk.END, "> Data is loaded\n", "green")
            frame3.log_terminal.yview_moveto(1.0)

    def wake(self):
        if not self.app_state.robot_session.isConnected():
            return
        self.app_state.robot_session.service("ALMotion").wakeUp()

    def sleep(self):
        if not self.app_state.robot_session.isConnected():
            return
        self.app_state.robot_session.service("ALMotion").rest()
