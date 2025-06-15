#!/usr/bin/python2.7
# coding=utf-8
import Tkinter as tk  # type: ignore
import os
import tkMessageBox  # type: ignore
import ttk  # type: ignore
import tkFileDialog  # type: ignore
import shutil
import threading
import ttk  # type: ignore
from pepper_cam_reader import NaoCamera
import cv2  # type: ignore
from PIL import Image, ImageTk, ImageDraw, ImageFont
import numpy as np
import cv2.aruco as aruco  # type: ignore
import cv2 as cv  # type: ignore
import math
import functions as fc


class Frame4(tk.Frame):
    def __init__(self, master, app_state, button_width=8, button_height=1):
        tk.Frame.__init__(self, master, width=688, height=400, bd=1, relief="solid")
        self.button_width = button_width
        self.button_height = button_height
        self.app_state = app_state
        self.enable_vision_var = tk.IntVar()
        self.Aruco_var = tk.IntVar()
        self.video_label = None
        self.tracking_entry = None
        self.marker_size_entry = None
        self.dictionaries = None
        self.app_state.frame4 = self

        self.build_ui()

    def build_ui(self):
        self.place(x=780, y=2)

        self.cam_frame = tk.Frame(self, width=524, height=380, bd=1, relief="solid")
        self.cam_frame.place(x=10, y=7)

        self.video_label = tk.Label(self.cam_frame)
        self.video_label.place(x=0, y=0)

        enable_vision_button = tk.Checkbutton(self, text=" Enable", variable=self.enable_vision_var,
                                              command=self.video_activation)
        enable_vision_button.place(x=570, y=10)

        switch_button = tk.Button(self, text="Switch CAM", command=self.switch_camera_in_thread,
                                  width=self.button_width, height=self.button_height)
        switch_button.place(x=565, y=40)

        Capture_button = tk.Button(self, text="Snap", command=self.snap_photo, width=self.button_width,
                                   height=self.button_height)
        Capture_button.place(x=565, y=80)

        import_button = tk.Button(self, text="Import", command=self.import_image_in_thread, width=self.button_width,
                                  height=self.button_height)
        import_button.place(x=565, y=120)

        tracking_label = tk.Label(self, text="Track:")
        tracking_label.place(x=570, y=165)

        self.tracking_entry = tk.Entry(self, width=3)
        self.tracking_entry.insert(0, "-1")
        self.tracking_entry.place(x=615, y=165)

        select_dictionary_label = tk.Label(self, text="Dictionary")
        select_dictionary_label.place(x=575, y=200)

        self.dictionaries = ttk.Combobox(self, values=self.app_state.aruco_dictionaries, width=13)
        self.dictionaries.current(10)
        self.dictionaries.place(x=555, y=225)

        marker_size_label = tk.Label(self, text="Size \"mm\":")
        marker_size_label.place(x=555, y=265)

        self.marker_size_entry = tk.Entry(self, width=4)
        self.marker_size_entry.insert(0, "29")
        self.marker_size_entry.place(x=635, y=265)

        Calibrate_button = tk.Button(self, text="Calibrate", command=self.calibrate_camera, width=self.button_width,
                                     height=self.button_height)
        Calibrate_button.place(x=565, y=300)

        Aruco_button = tk.Checkbutton(self, text=" ArUco", variable=self.Aruco_var, command=None)
        Aruco_button.place(x=570, y=350)

    def video_activation(self):
        if not self.app_state.robot_session.isConnected():
            return

        if self.enable_vision_var.get():
            self.app_state.pepper_camera = NaoCamera(self.app_state.robot_ip, self.app_state.robot_port,
                                                     self.app_state.camera_index)
            self.start_video_thread()
        elif self.app_state.pepper_camera is not None:
            fc.clear_video_frame(self.app_state)
            self.app_state.pepper_camera.release_camera()

    def switch_camera_in_thread(self):
        switch_cam_thread = threading.Thread(target=self.switch_camera)
        switch_cam_thread.setDaemon(True)
        switch_cam_thread.start()

    def switch_camera(self):
        if not self.app_state.robot_session.isConnected():
            return

        frame3 = self.app_state.frame3
        self.app_state.pepper_camera.release_camera()
        self.app_state.camera_index = 0 if self.app_state.camera_index == 1 else 1
        if self.app_state.camera_index == 0:
            frame3.log_terminal.insert(tk.END, "> Top Camera Selected\n")
            frame3.log_terminal.yview_moveto(1.0)
        else:
            frame3.log_terminal.insert(tk.END, "> Buttom Camera Selected\n")
            frame3.log_terminal.yview_moveto(1.0)
        if self.app_state.pepper_camera is not None:
            self.app_state.pepper_camera.release_camera()
        self.app_state.pepper_camera = NaoCamera(self.app_state.robot_ip, self.app_state.robot_port,
                                                 self.app_state.camera_index)
        self.start_video_thread()

    def start_video_thread(self):
        video_thread = threading.Thread(target=self.update_frame)
        video_thread.setDaemon(True)
        video_thread.start()

    def update_frame(self):
        if not self.app_state.robot_session.isConnected():
            return

        if self.Aruco_var.get():
            frame = self.app_state.pepper_camera.get_frame()
            if not frame is None:
                frame = self.process_aruco_markers(frame)
                cross_size = 20
                center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
                cv2.line(frame, (center_x - cross_size, center_y), (center_x + cross_size, center_y), (0, 0, 255), 2)
                cv2.line(frame, (center_x, center_y - cross_size), (center_x, center_y + cross_size), (0, 0, 255), 2)
        else:
            frame = self.app_state.pepper_camera.get_frame()
            if self.app_state.snap_taken:
                self.app_state.snap_taken = False
                self.capture_image(frame)
        if not frame is None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = img.resize((520, 376))
            img_tk = ImageTk.PhotoImage(img)
            self.video_label.img_tk = img_tk
            self.video_label.configure(image=img_tk)
            self.video_label.after(1, self.update_frame)

    def process_aruco_markers(self, frame):
        frame3 = self.app_state.frame3
        cam_frame_height = frame.shape[0]
        cam_frame_width = frame.shape[1]
        m = self.app_state.robot_session.service("ALMotion")
        """Detects and processes ArUco markers in a given frame."""
        selected_dict = cv2.aruco.Dictionary_get(int(self.dictionaries.current()))
        corners, ids, _ = cv2.aruco.detectMarkers(frame, selected_dict, parameters=self.app_state.parameters)
        if self.tracking_entry.get() != "-1" and self.tracking_entry.get() != '' and self.tracking_entry.get() != "-":
            log_message = "> Traking Mode\n"
            frame3.log_terminal.insert(tk.END, log_message, "green")
            frame3.log_terminal.yview_moveto(1.0)
            self.app_state.desired_aruco_marker = int(self.tracking_entry.get()) - 1
        if ids is not None and len(ids) > 0:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, int(self.marker_size_entry.get()), self.app_state.cam_matrix, self.app_state.dist_coefficients
            )
            for id in ids.flatten():
                if id not in self.app_state.detected_objects:
                    self.app_state.detected_objects.append(id)
            frame = aruco.drawDetectedMarkers(frame, corners)
            for i in range(len(ids)):
                if ids[i][0] == self.app_state.desired_aruco_marker:
                    center_x, center_y = cam_frame_width // 2, cam_frame_height // 2
                    marker_center_x = int(corners[i][0][:, 0].mean())
                    marker_center_y = int(corners[i][0][:, 1].mean())
                    dx = marker_center_x - center_x
                    dy = -1 * (marker_center_y - center_y)
                    cv2.putText(frame, "dx: {}px, dy: {}px".format(dx, dy), (marker_center_x, marker_center_y + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    cv2.putText(frame, str(ids[i][0] + 1), tuple(corners[i][0][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                (0, 255, 0), 2)
                    cv2.aruco.drawAxis(frame, self.app_state.cam_matrix, self.app_state.dist_coefficients, rvecs[i][0],
                                       tvecs[i][0], int(self.marker_size_entry.get()))
                    if abs(dx) < 10 and abs(dy) < 10:
                        self.app_state.desired_aruco_marker = -1
                    gain = 0.35
                    Relative_head_yaw = -1 * gain * dx * (55.2 / cam_frame_width) * (math.pi / 180)
                    Relative_head_pitch = -1 * gain * dy * (44.3 / cam_frame_height) * (math.pi / 180)
                    Actual_head_pitch_angle = m.getAngles("HeadPitch", False)[0]
                    m.setAngles("HeadPitch", Actual_head_pitch_angle + Relative_head_pitch, 0.4)
                    Actual_head_yaw_angle = m.getAngles("HeadYaw", False)[0]
                    m.setAngles("HeadYaw", Actual_head_yaw_angle + Relative_head_yaw, 0.4)

        return frame

    def capture_image(self, frame, folder='data/images/captured'):
        img_path = os.path.join(folder, 'image_{}.png'.format(len(os.listdir(folder)) + 1))
        cv2.imwrite(img_path, frame)

    def snap_photo(self):
        self.app_state.snap_taken = True

    def import_image_in_thread(self):
        importing_thread = threading.Thread(target=self.import_image)
        importing_thread.setDaemon(True)
        importing_thread.start()

    def import_image(self):
        file_path = tkFileDialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image Files", ("*.png", "*.jpg", "*.jpeg", "*.gif"))]
        )
        if file_path:
            destination_dir = self.app_state.data_folder + "/images/tablet/html"
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            destination = os.path.join(destination_dir, os.path.basename(file_path))

            try:
                shutil.copy(file_path, destination)
                tkMessageBox.showinfo("Warning!",
                                      "You have to run \"pepper_gui_behavior\" in choregraphe to update the "
                                      "html package!")
                fc.load_data(self.app_state)
            except IOError as e:
                return
        else:
            return

    def calibrate_camera(self):
        frame3 = self.app_state.frame3
        image_dir_path = "data/images/calibration"
        chess_board_dim = (9, 6)
        square_size = 20
        CHECK_DIR = os.path.isdir("data/Aruco_calib_data")
        if not CHECK_DIR:
            os.makedirs("data/Aruco_calib_data")

        obj_3D = np.zeros((chess_board_dim[0] * chess_board_dim[1], 3), np.float32)
        obj_3D[:, :2] = np.mgrid[0:chess_board_dim[0], 0:chess_board_dim[1]].T.reshape(-1, 2)
        obj_3D *= square_size
        obj_points_3D = []
        img_points_2D = []
        files = os.listdir(image_dir_path)
        for file in files:
            imagePath = os.path.join(image_dir_path, file)
            image = cv.imread(imagePath)
            grayScale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            ret, corners = cv.findChessboardCorners(image, chess_board_dim, None)
            if ret:
                obj_points_3D.append(obj_3D)
                corners2 = cv.cornerSubPix(grayScale, corners, (3, 3), (-1, -1),
                                           (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                img_points_2D.append(corners2)
                image_with_corners = cv.drawChessboardCorners(image, chess_board_dim, corners2, ret)
        cv.destroyAllWindows()

        ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
            obj_points_3D, img_points_2D, grayScale.shape[::-1], None, None
        )

        log_message = "> Calibration successful.\n> Saving calibration data...\n"
        frame3.log_terminal.insert(tk.END, log_message)
        frame3.log_terminal.yview_moveto(1.0)
        log_message = ""

        np.savez(
            "data/Aruco_calib_data/MultiMatrix",
            camMatrix=mtx,
            distCoef=dist,
            rVector=rvecs,
            tVector=tvecs,
        )

        log_message = "> Calibration data saved successfully.\n"
        frame3.log_terminal.insert(tk.END, log_message, "green")
        frame3.log_terminal.yview_moveto(1.0)
        log_message = ""
