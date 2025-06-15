#!/usr/bin/python2.7
# coding=utf-8

import socket
import qi
import numpy as np
import cv2


class AppState:
    def __init__(self):
        # Socket client
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = '127.0.0.1'
        self.PORT = 12321

        self.frame0 = None
        self.frame1 = None
        self.frame2 = None
        self.frame3 = None
        self.frame4 = None
        self.frame5 = None

        # Flags
        self.stiff_on = False
        self.hand_opened = False
        self.leds_on = False
        self.try_posture_flag = False
        self.try_motion_flag = False
        self.run_code_flag = False
        self.stop_code_flag = False
        self.snap_taken = False

        # Robot
        self.choices = ["None", "Left Arm", "Right Arm", "Head", "Torso", "Knee"]
        self.robot_ip = "169.254.42.206"
        self.robot_port = 9559
        self.robot_session = qi.Session()

        # Data
        self.data_folder = "data"
        self.posture_data = []
        self.selected_posture = ""
        self.selected_posture_index = 0
        self.posture_period = 2.0

        self.motion_data = []
        self.selected_motion = ""
        self.motions_data = []

        self.experiment_names = []
        self.Language = "English"
        self.code = []
        self.photo_names = []

        # Camera
        self.camera_index = 0
        self.pepper_camera = None

        # ArUco
        self.aruco_dictionaries = [
            "DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250", "DICT_4X4_1000",
            "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250", "DICT_5X5_1000",
            "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250", "DICT_6X6_1000",
            "DICT_7X7_50", "DICT_7X7_100", "DICT_7X7_250", "DICT_7X7_1000"
        ]
        self.calib_data = np.load("data/Aruco_calib_data/MultiMatrix.npz")
        self.cam_matrix = self.calib_data["camMatrix"]
        self.dist_coefficients = self.calib_data["distCoef"]
        self.desired_aruco_marker = -1
        self.id_to_label = {i: chr(ord('A') + i) for i in range(25)}
        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
        self.parameters = cv2.aruco.DetectorParameters_create()
        self.real_marker_length_mm = 29
        self.detected_objects = []

        # LLM
        self.LLM_process = None
        self.LLM_received_message = ""
        self.prompts = ["STA", "STM"]
        self.prompt_path = "data/LLM/STA.txt"

        # Arduino
        self.arduino_manager = []
        self.arduino_ports = []
