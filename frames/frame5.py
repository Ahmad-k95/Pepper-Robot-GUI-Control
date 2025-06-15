#!/usr/bin/python2.7
# coding=utf-8
import subprocess
import Tkinter as tk  # type: ignore
import time
import os
import tkMessageBox  # type: ignore
import threading
import socket
import functions as fc


class Frame5(tk.Frame):
    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=688, height=496, bd=1, relief="solid")
        self.button_width = button_width
        self.button_height = button_height
        self.app_state = app_state
        self.app_state.frame5 = self
        self.LLM_var = tk.IntVar()
        self.prompt_var = tk.StringVar()
        self.prompt_var.set(self.app_state.prompts[0])
        self.recognized_speech = None
        self.LLM_prompt = None
        self.build_ui()

    def build_ui(self):
        self.place(x=780, y=400)
        send_queries_button = tk.Button(self, text="Send", command=self.send_queries,
                                        width=self.button_width, height=self.button_height)
        send_queries_button.place(x=153, y=13)

        subFrame = tk.Frame(self, width=125, height=36, bd=1, relief="solid")
        subFrame.place(x=280, y=-1)

        LLM_button = tk.Checkbutton(self, text="Enable LLM", font=("Arial", 12),
                                    variable=self.LLM_var, command=self.run_LLM_thread)
        LLM_button.place(x=281, y=5)

        Prompt_label = tk.Label(self, text="Prompt:")
        Prompt_label.place(x=430, y=18)

        prompt_menu = tk.OptionMenu(self, self.prompt_var, *self.app_state.prompts, command=self.on_prompt_select)
        prompt_menu.config(width=2)
        prompt_menu.place(x=500, y=13)

        save_prompt_button = tk.Button(self, text="Save", command=self.save_prompt,
                                       width=self.button_width - 5, height=self.button_height)
        save_prompt_button.place(x=583, y=13)

        recognized_speech_label = tk.Label(self, text="Queries:")
        recognized_speech_label.place(x=90, y=18)

        self.recognized_speech = tk.Text(self, width=38, height=25, insertbackground="white", foreground="blue")
        self.recognized_speech.place(x=10, y=51)

        self.LLM_prompt = tk.Text(self, width=38, height=25, background="black",
                                  insertbackground="yellow", foreground="yellow")
        self.LLM_prompt.place(x=366, y=51)

    def send_queries(self):
        frame3 = self.app_state.frame3
        text = self.recognized_speech.get("1.0", tk.END).strip()
        log_message = "> Sending recognized speech to LLM...\n"
        frame3.log_terminal.insert(tk.END, log_message, "green")
        frame3.log_terminal.yview_moveto(1.0)
        self.app_state.client_socket.sendall(text)

    def receive_STA_messages(self):
        frame3 = self.app_state.frame3
        while self.LLM_var.get():
            try:
                data = self.app_state.client_socket.recv(4096)
                if data:
                    if data.startswith("S: "):
                        recognized_text = "> " + data[len("S: "):] + "\n"
                        self.recognized_speech.insert(tk.END, recognized_text)
                        self.recognized_speech.yview_moveto(1.0)

                    elif data.startswith("R: "):
                        STA_generated_code = data[len("R: "):] + "\n"
                        frame3.Code_entry.delete(1.0, tk.END)
                        STA_generated_code_lines = STA_generated_code.split('/')
                        for line in STA_generated_code_lines:
                            frame3.Code_entry.insert(tk.END, line + '\n')
                        frame3.Code_entry.yview_moveto(1.0)
                        time.sleep(1)
                        self.app_state.client_socket.sendall("start")
                        log_message = "> STA code is Running...\n"
                        frame3.log_terminal.insert(tk.END, log_message, "green")
                        frame3.log_terminal.yview_moveto(1.0)
                        fc.run_experiment(self.app_state)
                        self.app_state.client_socket.sendall("stop")

                    elif data.startswith("N: "):
                        log_message = "> " + data[len("N: "):] + "\n"
                        frame3.log_terminal.insert(tk.END, log_message, "green")
                        frame3.log_terminal.yview_moveto(1.0)

                    elif data.startswith("W: "):
                        log_message = "> " + data[len("W: "):] + "\n"
                        frame3.log_terminal.insert(tk.END, log_message, "yellow")
                        frame3.log_terminal.yview_moveto(1.0)

                    elif data.startswith("E: "):
                        log_message = "> " + data[len("E: "):] + "\n"
                        frame3.log_terminal.insert(tk.END, log_message, "red")
                        frame3.log_terminal.yview_moveto(1.0)
                    else:
                        print("Message from STA: {}".format(data))
                else:
                    break
            except Exception as e:
                print("Error receiving message: {}".format(e))
                break

    def receive_STA_messages_in_thread(self):
        receive_data_thread = threading.Thread(target=self.receive_STA_messages)
        receive_data_thread.setDaemon(True)
        receive_data_thread.start()

    def run_LLM(self):
        frame3 = self.app_state.frame3
        os.system('clear')
        if self.LLM_var.get():
            self.app_state.LLM_process = subprocess.Popen(["python3.10", "SpeechToAction.py"])
            time.sleep(2)
            try:
                self.app_state.client_socket.connect((self.app_state.HOST, self.app_state.PORT))
                log_message = "> Connected to server." + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "green")
                frame3.log_terminal.yview_moveto(1.0)
            except Exception as e:
                log_message = "> Failed to connect to server." + str(e) + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "red")
                frame3.log_terminal.yview_moveto(1.0)
            self.receive_STA_messages_in_thread()
        else:
            log_message = "> LLM Module not activated.\n"
            frame3.log_terminal.insert(tk.END, log_message, "red")
            frame3.log_terminal.yview_moveto(1.0)
            self.app_state.LLM_process.terminate()
            self.app_state.client_socket.close()
            del self.app_state.client_socket
            self.app_state.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.LLM_prompt.delete(1.0, tk.END)
            self.recognized_speech.delete(1.0, tk.END)

    def run_LLM_thread(self):
        fc.load_prompt(self.app_state)
        LLM_thread = threading.Thread(target=self.run_LLM)
        LLM_thread.setDaemon(True)
        LLM_thread.start()

    def on_prompt_select(self, selection):
        self.app_state.prompt_path = "data/LLM/{}.txt".format(selection)
        print("Updated prompt path:", self.app_state.prompt_path)
        fc.load_prompt(self.app_state)

    def save_prompt(self):
        frame3 = self.app_state.frame3
        confirm = tkMessageBox.askyesno("Save Confirmation", "Are you sure you want to save the edited prompt?")
        if not confirm:
            return
        try:
            text_to_save = self.LLM_prompt.get(1.0, tk.END).strip()
            with open(self.app_state.prompt_path, "w") as file:
                file.write(text_to_save.encode("utf-8"))
        except IOError:
            log_message = "> Error: The file '{}' could not be saved.\n".format(self.app_state.prompt_path)
            frame3.log_terminal.insert(tk.END, log_message, "red")
            frame3.log_terminal.yview_moveto(1.0)
        fc.load_prompt(self.app_state)
