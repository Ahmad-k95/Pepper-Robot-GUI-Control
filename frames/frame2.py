#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
import os
import tkMessageBox  # type: ignore
import re
import threading
import functions as fc
from data_base import delete_posture_by_name
from data_base import motion_exists, delete_motion_by_name, insert_motion_to_db
from data_base import get_motion, get_posture_by_name, get_connection


class Frame2(tk.Frame):
    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=780, height=287, bd=1, relief="solid")
        self.place(x=2, y=156)
        self.grid_propagate(False)
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.app_state = app_state
        self.app_state.frame2 = self
        self.build_ui(button_width, button_height)

    def build_ui(self, button_width, button_height):

        self.posture_list_label = tk.Label(self, text="Postures:")
        self.posture_list_label.place(x=20, y=10)

        self.posture_listbox = tk.Listbox(self, width=10, height=13)
        self.posture_listbox.place(x=10, y=35)

        self.posture_period_label = tk.Label(self, text="Time:")
        self.posture_period_label.place(x=115, y=80)

        self.posture_period_entry = tk.Entry(self, width=4)
        self.posture_period_entry.insert(0, "2.0")
        self.posture_period_entry.place(x=167, y=80)

        self.try_post_button = tk.Button(self, text="Try", command=self.try_posture_in_thread, width=button_width,
                                         height=button_height)
        self.try_post_button.place(x=115, y=120)

        self.addpost2motion_button = tk.Button(self, text="Add", command=self.add_post_2_motion, width=button_width,
                                               height=button_height)
        self.addpost2motion_button.place(x=115, y=160)

        self.del_post_button = tk.Button(self, text="Delete", command=self.delete_posture, width=button_width,
                                         height=button_height)
        self.del_post_button.place(x=115, y=200)

        tk.Label(self, text="Motion:").place(x=305, y=10)

        self.motion_listbox = tk.Listbox(self, width=10, height=13)
        self.motion_listbox.place(x=290, y=35)

        self.motion_entry = tk.Entry(self, width=10)
        self.motion_entry.insert(0, "mx")
        self.motion_entry.place(x=398, y=80)

        self.try_motion_button = tk.Button(self, text="Try", command=self.try_unsaved_motion_in_thread,
                                           width=button_width, height=button_height)
        self.try_motion_button.place(x=395, y=120)

        self.save_motion_button = tk.Button(self, text="Save", command=self.save_motion, width=button_width,
                                            height=button_height)
        self.save_motion_button.place(x=395, y=160)

        self.delete_motion_pos_button = tk.Button(self, text="Delete", command=self.delete_post_motion,
                                                  width=button_width, height=button_height)
        self.delete_motion_pos_button.place(x=395, y=200)

        self.motions_label = tk.Label(self, text="Motions:")
        self.motions_label.place(x=580, y=10)

        self.motions_listbox = tk.Listbox(self, width=10, height=13)
        self.motions_listbox.place(x=570, y=35)

        self.post_motion_listbox = tk.Listbox(self, width=11, height=8)
        self.post_motion_listbox.place(x=674, y=35)

        self.try_motion_button2 = tk.Button(self, text="Try", command=self.try_saved_motion_in_thread,
                                            width=button_width, height=button_height)
        self.try_motion_button2.place(x=674, y=200)

        self.delete_motion_button = tk.Button(self, text="Delete", command=self.delete_motion, width=button_width,
                                              height=button_height)
        self.delete_motion_button.place(x=674, y=240)

    def try_posture_in_thread(self):
        frame3 = self.app_state.frame3
        if self.app_state.try_posture_flag:
            frame3.log_terminal.insert(tk.END, "> Trying another posture...!\n", "red")
            frame3.log_terminal.yview_moveto(1.0)
            return
        try_posture_thread = threading.Thread(target=self.try_posture)
        try_posture_thread.setDaemon(True)
        try_posture_thread.start()

    def add_post_2_motion(self):
        if self.posture_listbox.curselection():
            period_text = self.posture_period_entry.get()
            if period_text.replace(".", "", 1).isdigit() and period_text.count("."):
                period = float(period_text)
            else:
                tkMessageBox.showinfo("Warning!", "Invalid time value!")
                return
            if not self.app_state.selected_posture:
                return
            self.app_state.motion_data.append([self.app_state.selected_posture, period])

            self.motion_listbox.insert(tk.END, self.app_state.selected_posture)

    def delete_posture(self):
        index = self.posture_listbox.curselection()
        if index:
            posture_name = self.posture_listbox.get(index)
            delete_posture_by_name(posture_name)
            fc.load_data(self.app_state)
        else:
            return

    def try_unsaved_motion_in_thread(self):
        frame3 = self.app_state.frame3
        if self.app_state.try_motion_flag:
            frame3.Code_entry.insert(tk.END, "> Testing another motion...!\n", "red")
            frame3.Code_entry.yview_moveto(1.0)
            return
        try_unsaved_motion_thread = threading.Thread(target=self.try_unsaved_motion)
        try_unsaved_motion_thread.setDaemon(True)
        try_unsaved_motion_thread.start()

    def save_motion(self):
        self.post_motion_listbox.delete(0, tk.END)
        motion_name = re.sub(r'\s', '', self.motion_entry.get()).lower()
        if motion_name.isdigit():
            tkMessageBox.showinfo("Warning!", "Motion name could not be a digit!")
            return
        if motion_name == "" or self.motion_listbox.size() == 0:
            tkMessageBox.showinfo("Warning!", "You must add a posture to the motion or insert its name!")
            return
        steps = [(data[0], data[1]) for data in self.app_state.motion_data]
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM motions WHERE name = ?", (motion_name,))
            result = cursor.fetchone()
            if result:
                response = tkMessageBox.askokcancel("Warning!",
                                                    "Motion name is used before! Do you want to edit the old motion?")
                if response:
                    delete_motion_by_name(motion_name)
                    insert_motion_to_db(motion_name, steps)
                    self.motion_listbox.delete(0, tk.END)
                    tkMessageBox.showinfo("Warning!", "Motion was changed!")
                else:
                    tkMessageBox.showinfo("Warning!", "You must change the motion name because it's used before!")
                    self.motion_entry.delete(0, tk.END)
                    return
            else:
                insert_motion_to_db(motion_name, steps)
                self.motion_listbox.delete(0, tk.END)
        except Exception as e:
            tkMessageBox.showerror("Database Error", str(e))
        finally:
            conn.close()
        self.motion_entry.delete(0, tk.END)
        self.app_state.motion_data = []
        fc.load_data(self.app_state)

    def delete_post_motion(self):
        selected_ind = self.motion_listbox.curselection()
        if selected_ind:
            selected_ind = selected_ind[0]
            self.app_state.motion_data.pop(selected_ind)
            self.motion_listbox.delete(selected_ind)
        else:
            pass

    def try_saved_motion_in_thread(self):
        frame3 = self.app_state.frame3
        if self.app_state.try_motion_flag:
            frame3.log_terminal.insert(tk.END, "> Testing another motion...!\n", "red")
            frame3.log_terminal.yview_moveto(1.0)
            return
        try_saved_motion_thread = threading.Thread(target=self.try_saved_motion)
        try_saved_motion_thread.setDaemon(True)
        try_saved_motion_thread.start()

    def delete_motion(self):
        selection = self.motions_listbox.curselection()
        if selection:
            index = selection[0]
            motion_name = self.motions_listbox.get(index)
            self.post_motion_listbox.delete(0, tk.END)
            delete_motion_by_name(motion_name)
            fc.load_data(self.app_state)
        else:
            pass

    def try_posture(self):
        if not self.app_state.robot_session.isConnected():
            return
        frame3 = self.app_state.frame3
        selection = self.posture_listbox.curselection()
        if not selection:
            return
        posture_name = self.posture_listbox.get(selection[0])
        self.app_state.try_posture_flag = True
        frame3.log_terminal.insert(tk.END, "> Try posture: {}\n".format(posture_name), "blue")
        frame3.log_terminal.yview_moveto(1.0)
        value = self.posture_period_entry.get()
        if value.replace(".", "", 1).isdigit() and value.count(".") <= 1:
            self.app_state.posture_period = float(value)
        else:
            tkMessageBox.showinfo("Warning!", "Invalid time value!")
            return
        posture = get_posture_by_name(posture_name)
        if posture:
            fc.robot_motion(self.app_state, posture, self.app_state.posture_period)
        else:
            tkMessageBox.showinfo("Error", "Posture not found in database!")
        self.app_state.try_posture_flag = False

    def try_unsaved_motion(self):
        if not self.app_state.robot_session.isConnected():
            return
        frame3 = self.app_state.frame3
        if not len(self.app_state.motion_data) == 0:
            self.app_state.try_motion_flag = True
            try:
                conn = get_connection()
                cursor = conn.cursor()

                for data in self.app_state.motion_data:
                    posture_name = data[0]
                    duration = data[1]
                    cursor.execute("SELECT * FROM postures WHERE name = ?", (posture_name,))
                    row = cursor.fetchone()
                    if row:
                        posture_tuple = (row[0],) + row[1:]
                        frame3.log_terminal.insert(tk.END, "> Try Posture: {}\n".format(posture_name), "blue")
                        frame3.log_terminal.yview_moveto(1.0)
                        fc.robot_motion(self.app_state, posture_tuple, duration)

                    else:
                        frame3.log_terminal.insert(tk.END, "> Posture not found: {}\n".format(posture_name), "red")
                        frame3.log_terminal.yview_moveto(1.0)

            finally:
                conn.close()

            self.app_state.try_motion_flag = False

    def try_saved_motion(self):
        if not self.app_state.robot_session.isConnected():
            return
        frame3 = self.app_state.frame3
        selection = self.motions_listbox.curselection()
        if not selection:
            return
        selected_motion = self.motions_listbox.get(selection[0])
        self.app_state.try_motion_flag = True
        frame3.log_terminal.insert(tk.END, "> Try motion: {}\n".format(selected_motion), "blue")
        frame3.log_terminal.yview_moveto(1.0)
        steps = get_motion(selected_motion)
        for posture_name, duration in steps:
            posture = get_posture_by_name(posture_name)
            if posture:
                fc.robot_motion(self.app_state, posture, duration)
            else:
                frame3.log_terminal.insert(tk.END, "> Posture '{}' not found.\n".format(posture_name), "red")
                frame3.log_terminal.yview_moveto(1.0)
        self.app_state.try_motion_flag = False
