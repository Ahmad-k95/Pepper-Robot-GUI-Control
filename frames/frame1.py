#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
import os
import tkMessageBox  # type: ignore
import re
import threading
import functions as fc
from data_base import insert_posture, update_posture


class Frame1(tk.Frame):

    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=390, height=155, bd=1, relief="solid")
        self.place(x=391, y=2)

        self.grid_propagate(False)

        self.app_state = app_state
        self.app_state.frame1 = self

        self.body_part = tk.StringVar()
        self.body_part.set("None")

        self.build_ui(button_width, button_height)

    def build_ui(self, button_width, button_height):
        self.posture_name_label = tk.Label(self, text="Posture name:")
        self.posture_name_label.place(x=10, y=10)

        self.posture_entry = tk.Entry(self, width=15)
        self.posture_entry.insert(0, "pxmx")
        self.posture_entry.place(x=130, y=10)

        self.save_post_button = tk.Button(self, text="Save", command=self.get_join_angles,
                                          width=button_width, height=button_height)
        self.save_post_button.place(x=285, y=7)

        self.body_part_label = tk.Label(self, text="Select part:")
        self.body_part_label.place(x=10, y=55)

        self.option_menu = tk.OptionMenu(self, self.body_part, *self.app_state.choices, command=self.on_option_change)
        self.option_menu.place(x=130, y=50)
        self.option_menu.config(width=10)

        self.stiff_button = tk.Button(self, text="Stiff", command=self.stiff_ctrl,
                                      width=button_width, height=button_height)
        self.stiff_button.place(x=285, y=50)

        self.hand_label = tk.Label(self, text="  Hand CTRL", fg="green")
        self.hand_label.place(x=285, y=88)

        self.hand_button = tk.Button(self, text="hand", command=self.hand_control_in_thread,
                                     width=button_width, height=button_height)
        self.hand_button.place(x=285, y=110)

    def get_join_angles(self):
        session = self.app_state.robot_session
        if not session.isConnected():
            return

        posture_name = re.sub(r'\s', '', self.posture_entry.get()).lower()

        if posture_name.isdigit():
            tkMessageBox.showinfo("Warning!", "Posture name could not be a digit!")
            return

        if posture_name == "":
            tkMessageBox.showinfo("Warning!", "You must insert a name for this posture!")
            return

        m = session.service("ALMotion")
        a = False  # ActiveSensors

        data = [
            posture_name,
            m.getAngles("RElbowRoll", a)[0], m.getAngles("RElbowYaw", a)[0], m.getAngles("RHand", a)[0],
            m.getAngles("RShoulderPitch", a)[0], m.getAngles("RShoulderRoll", a)[0], m.getAngles("RWristYaw", a)[0],
            m.getAngles("LElbowRoll", a)[0], m.getAngles("LElbowYaw", a)[0], m.getAngles("LHand", a)[0],
            m.getAngles("LShoulderPitch", a)[0], m.getAngles("LShoulderRoll", a)[0], m.getAngles("LWristYaw", a)[0],
            m.getAngles("HipPitch", a)[0], m.getAngles("HipRoll", a)[0], m.getAngles("KneePitch", a)[0],
            m.getAngles("HeadPitch", a)[0], m.getAngles("HeadYaw", a)[0]
        ]

        success = insert_posture(data)

        if success:
            tkMessageBox.showinfo("Success", "Posture saved successfully.")
        else:
            response = tkMessageBox.askokcancel("Posture Name Already Used",
                                                "Posture name is used before! Do you want to edit the old posture?")
            if response:
                update_posture(posture_name, data[1:])
                tkMessageBox.showinfo("Updated", "Posture updated successfully.")
            else:
                tkMessageBox.showinfo("Cancelled", "You must change the posture name.")
                return
        fc.load_data(self.app_state)

    def on_option_change(self, value):
        if value in ["Head", "Torso", "Knee"]:
            self.master.focus_set()

    def hand_control_in_thread(self):
        hand_control_thread = threading.Thread(target=self.hand_control)
        hand_control_thread.setDaemon(True)
        hand_control_thread.start()

    def hand_control(self):
        if not self.app_state.robot_session.isConnected():
            return
        frame3 = self.app_state.frame3
        motion_service = self.app_state.robot_session.service("ALMotion")
        selected_part = self.body_part.get()

        if selected_part == "Left Arm":
            if not self.app_state.hand_opened:
                motion_service.openHand('LHand')
                self.app_state.hand_opened = True
                self.hand_button.config(text="Close")
                frame3.log_terminal.insert(tk.END, "> Left Hand is Opened\n")
            else:
                motion_service.closeHand('LHand')
                self.app_state.hand_opened = False
                self.hand_button.config(text="Open")
                frame3.log_terminal.insert(tk.END, "> Left Hand is Closed\n")

        elif selected_part == "Right Arm":
            if not self.app_state.hand_opened:
                motion_service.openHand('RHand')
                self.app_state.hand_opened = True
                self.hand_button.config(text="Close")
                frame3.log_terminal.insert(tk.END, "> Right Hand is Opened\n")
            else:
                motion_service.closeHand('RHand')
                self.app_state.hand_opened = False
                self.hand_button.config(text="Open")
                frame3.log_terminal.insert(tk.END, "> Right Hand is Closed\n")

        frame3.log_terminal.yview_moveto(1.0)

    def stiff_ctrl(self):
        if not self.app_state.robot_session.isConnected():
            return

        if self.app_state.stiff_on:

            stiffness = 1
            self.app_state.stiff_on = False
        else:
            stiffness = 0
            self.app_state.stiff_on = True

        m = self.app_state.robot_session.service("ALMotion")
        frame3 = self.app_state.frame3
        if self.body_part.get() == self.app_state.choices[3]:
            frame3.log_terminal.insert(tk.END, "> Body part: Head\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            frame3.log_terminal.insert(tk.END, "> Stifness: {}".format(not self.app_state.stiff_on) + "\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            m.stiffnessInterpolation("Head", stiffness, 0.1)
        elif self.body_part.get() == self.app_state.choices[2]:
            frame3.log_terminal.insert(tk.END, "> Body part: Right Arm\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            frame3.log_terminal.insert(tk.END, "> Stifness: {}".format(not self.app_state.stiff_on) + "\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            m.stiffnessInterpolation("RArm", stiffness, 0.1)
        elif self.body_part.get() == self.app_state.choices[1]:
            frame3.log_terminal.insert(tk.END, "> Body part: Left Arm\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            frame3.log_terminal.insert(tk.END, "> Stifness: {}".format(not self.app_state.stiff_on) + "\n", "yellow")
            frame3.log_terminal.yview_moveto(1.0)
            m.stiffnessInterpolation("LArm", stiffness, 0.1)
