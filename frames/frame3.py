#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
import time
import os
import tkMessageBox  # type: ignore
import ttk  # type: ignore
import re
from datetime import datetime
import threading
import ttk  # type: ignore
import functions as fc
import app_events as ap
from data_base import delete_experiment_by_name, insert_experiment, get_connection


class Frame3(tk.Frame):
    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=780, height=454, bd=1, relief="solid", )
        self.place(x=2, y=442)
        self.grid_propagate(False)

        self.app_state = app_state
        self.button_width = button_width
        self.app_state.frame3 = self
        self.button_height = button_height

        self.build_ui()

    def build_ui(self):
        self.experiment_name_label = tk.Label(self, text="Experiment Name:")
        self.experiment_name_label.place(x=55, y=14)

        self.experiment_name_entry = tk.Entry(self, width=10)
        self.experiment_name_entry.insert(0, "---")
        self.experiment_name_entry.place(x=185, y=14)

        self.Code_entry = tk.Text(self, width=38, height=23, background="blue", foreground="white",
                                  insertbackground="white")
        self.Code_entry.place(x=10, y=45)

        self.select_label = tk.Label(self, text="Select:")
        self.select_label.place(x=362, y=75)

        self.selected_experiment = tk.StringVar(value="None")
        self.experiments = ttk.Combobox(self, textvariable=self.selected_experiment, width=9)
        self.experiments.place(x=344, y=100)

        self.check_button = tk.Button(self, text="Check", command=self.check_code, width=self.button_width,
                                      height=self.button_height)
        self.check_button.place(x=342, y=140)

        self.save_button = tk.Button(self, text="  Save ", command=self.save_code, width=self.button_width,
                                     height=self.button_height)
        self.save_button.place(x=342, y=180)

        self.run_button = tk.Button(self, text="  Run  ", command=self.run_experiment_in_thread,
                                    width=self.button_width, height=self.button_height)
        self.run_button.place(x=342, y=220)

        self.continue_button = tk.Button(self, text=">>>>", command=self.run_experiment_in_thread,
                                         width=self.button_width, height=self.button_height)
        self.continue_button.place(x=342, y=260)

        self.delete_button = tk.Button(self, text="Delete", command=self.delete_experiment, width=self.button_width,
                                       height=self.button_height)
        self.delete_button.place(x=342, y=300)

        self.save_log_button = tk.Button(self, text="Save Log", command=self.save_log, width=self.button_width,
                                         height=self.button_height)
        self.save_log_button.place(x=342, y=340)

        self.stop_button = tk.Button(self, text="STOP", command=self.stop_robot_in_thread, bg="red", fg="black",
                                     width=self.button_width, height=self.button_height)
        self.stop_button.place(x=342, y=380)

        self.log_label = tk.Label(self, text="Log terminal:")
        self.log_label.place(x=560, y=15)

        self.log_terminal = tk.Text(self, width=38, height=23, background="black", foreground="white")
        self.log_terminal.place(x=457, y=45)
        self.log_terminal.bind("<Return>", lambda event: ap.on_enter_pressed(event, self.app_state))

        log_message = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
        self.log_terminal.insert(tk.END, log_message, "yellow")
        self.log_terminal.yview_moveto(1.0)
        self.log_terminal.tag_configure("yellow", foreground="yellow")
        self.log_terminal.tag_configure("red", foreground="red")
        self.log_terminal.tag_configure("green", foreground="green")
        self.log_terminal.tag_configure("blue", foreground="blue")

    def check_code(self):

        checked_code = True
        self.app_state.code = self.Code_entry.get("1.0", tk.END).splitlines()
        for i in range(0, len(self.app_state.code)):
            self.app_state.code[i] = self.app_state.code[i].encode('utf-8').lower()
        self.app_state.code = [item for item in self.app_state.code if item != '']
        for i in range(0, len(self.app_state.code)):
            try:
                self.app_state.code[i] = re.sub(r'=+', '=', self.app_state.code[i])
                self.app_state.code[i] = self.app_state.code[i].split("=")
                self.app_state.code[i][0] = self.app_state.code[i][0].replace(" ", "")
                if self.app_state.code[i][0] == "say" or self.app_state.code[i][0] == "say_pc":
                    pass
                else:
                    self.app_state.code[i][1] = self.app_state.code[i][1].replace(" ", "")
            except Exception as e:
                checked_code = False
                log_message = "> " + self.app_state.code[i][0] + " isn't a command\n"
                self.log_terminal.insert(tk.END, log_message, "red")
                self.log_terminal.yview_moveto(1.0)
                return checked_code
        if not self.app_state.code:
            return
        log_message = "> Checking code...\n"
        self.log_terminal.insert(tk.END, log_message)
        self.log_terminal.yview_moveto(1.0)
        index = 0
        while index < len(self.app_state.code):
            line = self.app_state.code[index]
            if line[0] == "move":
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM motions WHERE name = ?", (line[1],))
                    count = cursor.fetchone()[0]
                    if count == 0:
                        checked_code = False
                        log_message = "> {} = {} :: {} not found\n".format(line[0], line[1], line[1])
                        self.log_terminal.insert(tk.END, log_message, "red")
                        self.log_terminal.yview_moveto(1.0)
                finally:
                    conn.close()

            elif line[0] == "lookat":
                if not line[1].isdigit():
                    checked_code = False
                    log_message = "> " + line[0] + " = " + line[1] + " :: " + line[1] + " not an object ID\n"
                    self.log_terminal.insert(tk.END, log_message, "red")
                    self.log_terminal.yview_moveto(1.0)

            elif line[0] == "delay":
                if not (line[1].replace(".", "", 1).isdigit() and line[1].count(".") <= 1):
                    checked_code = False
                    log_message = "> " + line[0] + " = " + line[1] + " :: " + line[1] + " not a digit\n"
                    self.log_terminal.insert(tk.END, log_message, "red")
                    self.log_terminal.yview_moveto(1.0)

            elif line[0] == "image":
                folder_path = self.app_state.data_folder + "/images/tablet/html"
                full_path = os.path.join(folder_path, line[1])
                if line[1] == "hide" or line[1] == "list":
                    pass
                elif not os.path.exists(full_path):
                    checked_code = False
                    log_message = "> " + line[0] + " = " + line[1] + " :: " + line[1] + " doesn't exist"
                    log_message = log_message + "\n"
                    self.log_terminal.insert(tk.END, log_message, "red")
                    self.log_terminal.yview_moveto(1.0)

            elif line[0] == "break":
                if not line[1] == "true":
                    checked_code = False
                    log_message = "> " + line[0] + " = " + line[1] + " :: " + line[1] + " must be \"true\"\n"
                    self.log_terminal.insert(tk.END, log_message, "red")
                    self.log_terminal.yview_moveto(1.0)

            elif line[0] == "say" or line[0] == "say_pc":
                pass

            else:
                checked_code = False
                log_message = "> " + line[0] + " = " + line[1] + " :: " + line[0] + " is not a command\n"
                self.log_terminal.insert(tk.END, log_message, "red")
                self.log_terminal.yview_moveto(1.0)

            index += 1
        if checked_code:
            log_message = "> No errors" + "\n"
            self.log_terminal.insert(tk.END, log_message, "green")
            self.log_terminal.yview_moveto(1.0)
        final_code = ""
        for line in self.app_state.code:
            final_code = final_code + line[0] + "=" + line[1] + "\n"
        self.Code_entry.delete(1.0, tk.END)
        self.Code_entry.insert(1.0, final_code)
        return checked_code

    def run_experiment_in_thread(self):
        if self.app_state.run_code_flag:
            self.log_terminal.insert(tk.END, "> Another code is running!\n", "red")
            self.log_terminal.yview_moveto(1.0)
            return

        thread = threading.Thread(target=fc.run_experiment, args=(self.app_state,))
        thread.setDaemon(True)
        thread.start()

    def delete_experiment(self):

        file_name = self.selected_experiment.get()
        if not file_name or file_name == "None":
            return

        response = tkMessageBox.askokcancel("Confirm Deletion",
                                            "Are you sure you want to delete the experiment '{}'?".format(file_name))

        if not response:
            return
        delete_experiment_by_name(file_name)
        self.experiment_name_entry.delete(0, tk.END)
        self.experiment_name_entry.insert(0, "xxxx")
        self.selected_experiment.set("None")
        self.Code_entry.delete(1.0, tk.END)
        fc.load_data(self.app_state)

    def save_log(self):
        current_datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S").replace(" ", "_")
        file_path = os.path.join(self.app_state.data_folder + "/log",
                                 self.experiment_name_entry.get() + "_" + current_datetime + ".txt")
        with open(file_path, "w") as file:
            file.write(self.log_terminal.get("1.0", tk.END))

    def stop_all_actions(self):
        time.sleep(1)
        frame0 = self.app_state.frame0
        frame4 = self.app_state.frame4

        self.app_state.stop_code_flag = True
        self.app_state.run_code_flag = False
        if not self.app_state.pepper_camera is None:
            self.app_state.pepper_camera.release_camera()

        self.log_terminal.insert(tk.END, "> Robot is disconnected\n", "red")
        self.log_terminal.yview_moveto(1.0)

        s = self.app_state.robot_session.service("ALTextToSpeech")
        s.setLanguage("English")
        s.say("Disconnected!")

        frame4.video_label.config(image="")
        self.app_state.robot_session.close()
        frame0.status_label.config(text="Connect!", fg="red")

        fc.stand_init(self.app_state)
        self.app_state.robot_session.close()
        self.log_terminal.insert(tk.END, "> Stop!\n", "red")
        self.log_terminal.yview_moveto(1.0)

    def stop_robot_in_thread(self):
        stop_thread = threading.Thread(target=self.stop_all_actions)
        stop_thread.setDaemon(True)
        stop_thread.start()

    def save_code(self):

        file_name = self.experiment_name_entry.get().strip()
        code = self.Code_entry.get("1.0", tk.END).strip()

        if not file_name:
            tkMessageBox.showinfo("Warning!", "Experiment name cannot be empty!")
            return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM experiments WHERE name = ?", (file_name,))
        exists = cursor.fetchone()
        conn.close()

        if exists:
            response = tkMessageBox.askokcancel("Warning!",
                                                "Experiment name is used before! Do you want to edit the old experiment?")
            if not response:
                tkMessageBox.showinfo("Warning!", "You must change the Experiment name because it's used before!")
                return
            delete_experiment_by_name(file_name)

        insert_experiment(file_name, code)

        tkMessageBox.showinfo("Success", "Experiment saved successfully!")
        fc.load_data(self.app_state)
