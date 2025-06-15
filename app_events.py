#!/usr/bin/python2.7
# coding=utf-8

import Tkinter as tk  # type: ignore
import os
import tkMessageBox
from data_base import get_connection, load_selected_motion_from_db
import threading
from functions import manual_ctrl_part


def select_posture(event, app_state):
    frame1 = app_state.frame1
    frame2 = app_state.frame2
    frame2.post_motion_listbox.delete(0, tk.END)
    app_state.selected_posture_index = frame2.posture_listbox.curselection()
    if app_state.selected_posture_index:
        app_state.selected_posture_index = app_state.selected_posture_index[0]
        app_state.selected_posture = frame2.posture_listbox.get(app_state.selected_posture_index)
        frame1.posture_entry.delete(0, tk.END)
        frame1.posture_entry.insert(0, app_state.selected_posture)
        frame1.body_part.set("None")


def select_motion(event, app_state):
    frame1 = app_state.frame1
    frame2 = app_state.frame2
    if frame2.motions_listbox.curselection():
        frame1.body_part.set("None")
        frame2.post_motion_listbox.delete(0, tk.END)
        selected_motion_index = frame2.motions_listbox.curselection()[0]
        app_state.selected_motion = frame2.motions_listbox.get(selected_motion_index)
        frame2.motion_entry.delete(0, tk.END)
        frame2.motion_entry.insert(0, app_state.selected_motion)
        load_selected_motion_from_db(app_state, frame2)
    else:
        frame1.body_part.set("None")
        if not frame2.post_motion_listbox.curselection():
            frame2.post_motion_listbox.delete(0, tk.END)


def select_experiment(event, app_state):
    frame3 = app_state.frame3
    experiment_name = frame3.selected_experiment.get()

    frame3.experiment_name_entry.delete(0, tk.END)
    frame3.Code_entry.delete(1.0, tk.END)
    frame3.experiment_name_entry.insert(0, experiment_name)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM experiments WHERE name = ?", (experiment_name,))
        row = cursor.fetchone()

        if not row:
            tkMessageBox.showerror("Error", "Experiment not found in database.")
            return

        experiment_id = row[0]

        cursor.execute("""
            SELECT command_type, command_value 
            FROM experiment_steps 
            WHERE experiment_id = ? 
            ORDER BY step_index
        """, (experiment_id,))

        steps = cursor.fetchall()
        for command_type, command_value in steps:
            if command_type == "break":
                line = "break=true"
            elif command_value is not None:
                line = "{}={}".format(command_type, command_value)
            else:
                line = command_type
            frame3.Code_entry.insert(tk.END, line + "\n")

    except Exception as e:
        tkMessageBox.showerror("Database Error", str(e))
    finally:
        conn.close()


def on_closing(master, app_state):
    if app_state.pepper_camera is not None and app_state.robot_session.isConnected():
        app_state.pepper_camera.release_camera()
    if app_state.LLM_process:
        app_state.LLM_process.terminate()
    master.destroy()


def manual_ctrl_in_thread(event, window, app_state):
    manual_ctrl_thread = threading.Thread(target=manual_ctrl_part, args=(event, window, app_state,))
    manual_ctrl_thread.setDaemon(True)
    manual_ctrl_thread.start()


def on_enter_pressed(event, app_state):
    frame3 = app_state.frame3
    manager = app_state.arduino_manager
    if not app_state.arduino_ports == []:
        lines = frame3.log_terminal.get("1.0", "end-1c").split("\n")
        last_line = lines[-1].strip()

        if not last_line.startswith("port"):
            manager.log("\n> Please type like 'port1', etc.", "yellow")
            return "break"

        try:
            idx = int(last_line[4:]) - 1
            if idx < 0 or idx >= len(manager.ports):
                manager.log("\n> Invalid port number.", "red")
                return "break"
            selected_port = manager.ports[idx].device
            manager.log("\n> You selected: {}".format(selected_port), "white")
            manager.connect(selected_port)
        except ValueError:
            manager.log("\n> Invalid input format.", "red")

        return "break"
