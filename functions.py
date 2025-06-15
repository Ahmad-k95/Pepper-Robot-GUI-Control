#!/usr/bin/python2.7
# coding=utf-8
# shared functions between different frames

import Tkinter as tk  # type: ignore
import time
from naoqi import ALProxy
import os
import pyttsx3  # type: ignore
import threading
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sqlite3
import tkMessageBox
from data_base import get_connection


def stand_init(app_state):
    if not app_state.robot_session.isConnected():
        return
    app_state.robot_session.service("ALRobotPosture").goToPosture("StandInit", 0.2)


def robot_motion(app_state, posture, post_time):
    if not app_state.robot_session.isConnected():
        return
    m = app_state.robot_session.service("ALMotion")
    chainName = "Arms"
    m.setExternalCollisionProtectionEnabled(chainName, False)

    names = ['RElbowRoll', 'RElbowYaw', 'RHand', 'RShoulderPitch', 'RShoulderRoll', 'RWristYaw',
             'LElbowRoll', 'LElbowYaw', 'LHand', 'LShoulderPitch', 'LShoulderRoll', 'LWristYaw',
             'HipPitch', 'HipRoll', 'KneePitch',
             'HeadPitch', 'HeadYaw']

    times = list()
    angles = list()

    for i in range(1, len(posture)):
        angles.append([float(posture[i])])
        times.append([post_time])
    m.angleInterpolation(names, angles, times, True)


def load_prompt(app_state):
    frame3 = app_state.frame3
    frame5 = app_state.frame5
    try:
        with open(app_state.prompt_path, "r") as file:
            text_content = file.read()
            frame5.LLM_prompt.delete(1.0, tk.END)
            frame5.LLM_prompt.insert(tk.END, text_content)
    except IOError:
        log_message = "> Error: The file could not be opened or found.\n"
        frame3.log_terminal.insert(tk.END, log_message, "red")
        frame3.log_terminal.yview_moveto(1.0)


def clear_video_frame(app_state):
    frame4 = app_state.frame4
    blank = Image.new("RGB", (520, 376), (220, 220, 220))
    draw = ImageDraw.Draw(blank)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()

    text = "No camera detected!"
    text_width, text_height = draw.textsize(text, font=font)
    x = (520 - text_width) // 2
    y = (376 - text_height) // 2

    draw.text((x, y), text, fill="red", font=font)

    blank_tk = ImageTk.PhotoImage(blank)
    frame4.video_label.configure(image=blank_tk)
    frame4.video_label.image = blank_tk


def say(app_state, text):
    if not app_state.robot_session.isConnected():
        return
    s1 = app_state.robot_session.service("ALTextToSpeech")
    s1.setLanguage(app_state.Language)
    s1.say(text)
    """
    script_path = 'C:\Users\Robotics2\Desktop\say.py'
    subprocess.Popen(['python', script_path])"""


def track_object(app_state, marker_id):
    frame3 = app_state.frame3
    if marker_id in app_state.detected_objects:
        app_state.desired_aruco_marker = marker_id
    else:
        log_message = "> Object not found!\n"
        frame3.log_terminal.insert(tk.END, log_message, "red")
        frame3.log_terminal.yview_moveto(1.0)
    while app_state.desired_aruco_marker != -1: ()
    return


def say_pc(text):
    engine = pyttsx3.init()
    engine.setProperty('voice', 'french+f1')
    engine.setProperty('rate', 140)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()


def show_image(app_state, image, show):
    tabletService = app_state.robot_session.service("ALTabletService")
    if show:
        image_thread = threading.Thread(
            target=tabletService.showImage("http://198.18.0.1/apps/pepper_gui_images-e650cd/" + image))
        image_thread.setDaemon(True)
        image_thread.start()
    else:
        image_thread = threading.Thread(target=tabletService.hideImage())
        image_thread.setDaemon(True)
        image_thread.start()


def list_images_in_directory(app_state):
    directory = 'data/images/tablet/html'
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    frame3 = app_state.frame3
    image_files = [
        file for file in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, file)) and os.path.splitext(file)[1].lower() in image_extensions
    ]
    log_message = "> Images:\n"
    frame3.log_terminal.insert(tk.END, log_message, "yellow")
    frame3.log_terminal.yview_moveto(1.0)
    log_message = ""
    for file in image_files:
        log_message = "> " + file + "\n"
        frame3.log_terminal.insert(tk.END, log_message, "white")
        frame3.log_terminal.yview_moveto(1.0)
        log_message = ""


def clear_first_line(app_state):
    frame3 = app_state.frame3
    next_code = frame3.Code_entry.get("1.0", "end")
    lines = next_code.split('\n')
    if len(lines) > 1:
        modified_content = '\n'.join(lines[1:])
    else:
        modified_content = ''
    modified_lines = [line for line in modified_content.split('\n') if line.strip()]
    modified_content = '\n'.join(modified_lines)
    frame3.Code_entry.delete("1.0", "end")
    frame3.Code_entry.insert("1.0", modified_content)


def run_experiment(app_state):
    app_state.arduino_manager.send_message("1")
    if not app_state.robot_session.isConnected():
        return
    frame4 = app_state.frame4
    frame3 = app_state.frame3
    frame4.tracking_entry.delete(0, tk.END)
    frame4.tracking_entry.insert(0, "-1")
    if frame3.check_code():
        app_state.run_code_flag = True
        log_message = "> Running:\n"
        frame3.log_terminal.insert(tk.END, log_message, "green")
        frame3.log_terminal.yview_moveto(1.0)
        log_message = ""
        for line in app_state.code:
            if line[0] == "move":
                motion_name = line[1]
                log_message += "> {} :: {}\n".format(line[0], motion_name)
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)

                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM motions WHERE name = ?", (motion_name,))
                    row = cursor.fetchone()
                    if not row:
                        log_message = "> {} = {} :: Not found in database\n".format(line[0], motion_name)
                        frame3.log_terminal.insert(tk.END, log_message, "red")
                        frame3.log_terminal.yview_moveto(1.0)
                    else:
                        motion_id = row[0]
                        cursor.execute("""
                            SELECT posture_name, duration 
                            FROM motion_steps 
                            WHERE motion_id = ? 
                            ORDER BY id
                        """, (motion_id,))
                        steps = cursor.fetchall()

                        for posture_name, duration in steps:
                            cursor.execute("SELECT * FROM postures WHERE name = ?", (posture_name,))
                            posture = cursor.fetchone()
                            if posture:
                                robot_motion(app_state, posture, duration)
                            else:
                                log_message = "> Posture '{}' not found for motion '{}'\n".format(posture_name,
                                                                                                  motion_name)
                                frame3.log_terminal.insert(tk.END, log_message, "red")
                                frame3.log_terminal.yview_moveto(1.0)
                except Exception as e:
                    tkMessageBox.showerror("Database Error", str(e))
                finally:
                    conn.close()


            elif line[0] == "say":
                log_message = log_message + "> " + line[0] + "::" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)
                say(app_state, line[1])

            elif line[0] == "lookat":
                log_message = log_message + "> " + line[0] + ":: object" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)
                track_object(app_state, int(line[1]) - 1)

            elif line[0] == "say_pc":
                log_message = log_message + "> " + line[0] + "::" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)
                say_pc(line[1])

            elif line[0] == "delay":
                log_message = log_message + "> " + line[0] + "::" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)
                time.sleep(float(line[1]))
                pass

            elif line[0] == "image":
                log_message = log_message + "> " + line[0] + "::" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)

                if line[1] == "hide":
                    show_image(app_state, line[1], False)
                elif line[1] == "list":
                    list_images_in_directory(app_state)
                else:
                    show_image(app_state, line[1], True)

            elif line[0] == "break":
                log_message = log_message + "> " + line[0] + "::" + line[1] + "\n"
                frame3.log_terminal.insert(tk.END, log_message, "blue")
                frame3.log_terminal.yview_moveto(1.0)
                battery_proxy = ALProxy("ALBattery", app_state.robot_ip, app_state.robot_port)
                battery_level = battery_proxy.getBatteryCharge()
                frame3.log_terminal.insert(tk.END, "> Battery level: {}%".format(battery_level) + "\n", "yellow")
                frame3.log_terminal.yview_moveto(1.0)
                clear_first_line(app_state)
                app_state.run_code_flag = False
                return
            log_message = ""

            if app_state.stop_code_flag:
                app_state.stop_code_flag = False
                app_state.run_code_flag = False
                return

            clear_first_line(app_state)

        battery_proxy = ALProxy("ALBattery", app_state.robot_ip, app_state.robot_port)
        battery_level = battery_proxy.getBatteryCharge()
        frame3.log_terminal.insert(tk.END, "> Battery level: {}%".format(battery_level) + "\n", "yellow")
        frame3.log_terminal.yview_moveto(1.0)
        app_state.run_code_flag = False
    else:
        return


def load_data(app_state):
    frame2 = app_state.frame2
    frame3 = app_state.frame3
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM postures")
        posture_names = cursor.fetchall()
    except Exception as e:
        tkMessageBox.showerror("Database Error (postures)", str(e))
        return
    finally:
        conn.close()

    frame2.posture_listbox.delete(0, tk.END)
    for name in posture_names:
        frame2.posture_listbox.insert(tk.END, name[0])
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM motions")
        motion_names = cursor.fetchall()
    except Exception as e:
        tkMessageBox.showerror("Database Error (motions)", str(e))
        return
    finally:
        conn.close()

    frame2.motions_listbox.delete(0, tk.END)
    for name in motion_names:
        frame2.motions_listbox.insert(tk.END, name[0])
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM experiments")
        experiment_names = cursor.fetchall()
    except Exception as e:
        tkMessageBox.showerror("Database Error (experiments)", str(e))
        return
    finally:
        conn.close()

    frame3.experiments['values'] = [name[0] for name in experiment_names]

    html_folder_path = "data/images/tablet/html"
    image_extensions = [".jpg", ".jpeg", ".png", ".gif"]
    try:
        file_list = os.listdir(html_folder_path)
        photo_names = [file for file in file_list if any(file.endswith(ext) for ext in image_extensions)]
    except Exception:
        photo_names = []

    app_state.photo_names = photo_names


def manual_ctrl_part(event, window, app_state):
    if not app_state.robot_session.isConnected():
        return
    m = app_state.robot_session.service("ALMotion")
    Active_sensors = False
    frame1 = app_state.frame1
    if frame1.body_part.get() == "Head":
        if event.keysym == "Up":
            window.focus()
            head_pitch_angle = m.getAngles("HeadPitch", Active_sensors)[0]
            m.angleInterpolation("HeadPitch", head_pitch_angle - 0.05, 0.05, True)
        elif event.keysym == "Down":
            window.focus()
            head_pitch_angle = m.getAngles("HeadPitch", Active_sensors)[0]
            m.angleInterpolation("HeadPitch", head_pitch_angle + 0.05, 0.05, True)
        elif event.keysym == "Right":
            window.focus()
            head_yaw_angle = m.getAngles("HeadYaw", Active_sensors)[0]
            m.angleInterpolation("HeadYaw", head_yaw_angle - 0.05, 0.05, True)
        elif event.keysym == "Left":
            window.focus()
            head_yaw_angle = m.getAngles("HeadYaw", Active_sensors)[0]
            m.angleInterpolation("HeadYaw", head_yaw_angle + 0.05, 0.05, True)
        else:
            pass

    elif frame1.body_part.get() == "Torso":
        if event.keysym == "Up":
            window.focus()
            hip_pitch_angle = m.getAngles("HipPitch", Active_sensors)[0]
            m.angleInterpolation("HipPitch", hip_pitch_angle - 0.025, 0.05, True)
        elif event.keysym == "Down":
            window.focus()
            hip_pitch_angle = m.getAngles("HipPitch", Active_sensors)[0]
            m.angleInterpolation("HipPitch", hip_pitch_angle + 0.025, 0.05, True)
        elif event.keysym == "Right":
            window.focus()
            hip_Roll_angle = m.getAngles("HipRoll", Active_sensors)[0]
            m.angleInterpolation("HipRoll", hip_Roll_angle - 0.025, 0.05, True)
        elif event.keysym == "Left":
            window.focus()
            hip_Roll_angle = m.getAngles("HipRoll", Active_sensors)[0]
            m.angleInterpolation("HipRoll", hip_Roll_angle + 0.025, 0.05, True)
        else:
            pass

    elif frame1.body_part.get() == "Knee":
        if event.keysym == "Up":
            window.focus()
            Knee_pitch_angle = m.getAngles("KneePitch", Active_sensors)[0]
            m.angleInterpolation("KneePitch", Knee_pitch_angle - 0.02, 0.05, True)
        elif event.keysym == "Down":
            window.focus()
            Knee_pitch_angle = m.getAngles("KneePitch", Active_sensors)[0]
            m.angleInterpolation("KneePitch", Knee_pitch_angle + 0.02, 0.05, True)
        else:
            pass
    else:
        return


def initialize_ports(app_state):
    manager = app_state.arduino_manager
    app_state.arduino_ports = manager.list_ports()
    if not app_state.arduino_ports == []:
        manager.log("> Type port'n' and press Enter to connect.", "yellow")
