import time
import cv2
import mediapipe as mp
import math
import socket
import pyautogui as pag
import numpy as np
import sys


TARGET_IP = "127.0.0.1"
TARGET_PORT = 5005
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class state_stuff:
    def __init__(self,button_id, roi_tuple, color, threshold) -> None:

        self.id = button_id
        self.roi = roi_tuple            # e.g., (100, 100, 200, 300)
        self.color = color


        # Global System State Initialization
        self.toggle_state = False       # Global System State: OFF (False) or ON (True)
        self.is_hovering = False        # Tracks if Landmark 8 is inside ROI
        self.start_time = 0.0           # Entry timestamp
        self.HOLD_THRESHOLD = threshold       # Required dwell time in seconds
        self.has_triggered = False      # Latch lock
        self.elapsed_time = 0.0
        self.is_scrolling = False
        self.is_dragging = False
    def state_change(self):

        if not self.is_hovering:

            self.is_hovering = True
            self.has_triggered = False
            self.start_time = time.time()
            self.elapsed_time = 0.0

        else:
            self.elapsed_time = time.time() - self.start_time
            if self.elapsed_time >= self.HOLD_THRESHOLD and not self.has_triggered:
                self.toggle_state = not self.toggle_state
                self.has_triggered = True
                print(f"STATE CHANGED: System is now {'ACTIVE' if self.toggle_state else 'IDLE'}")

        if self.elapsed_time >= self.HOLD_THRESHOLD and not self.has_triggered:
            self.toggle_state = not self.toggle_state
            self.has_triggered = True
    

    def reset_state(self):
        self.is_hovering = False
        self.has_triggered = False
        self.elapsed_time = 0.0


    def draw_rect(self, x_frame ): 
        cv2.rectangle(x_frame, (self.roi[0], self.roi[1]), (self.roi[2], self.roi[3]), (255, 0, 0), 3)
        
        status_text = f"SYSTEM: {'ACTIVE' if self.toggle_state else 'IDLE'}"
        text_color = (0, 255, 0) if self.toggle_state else (0, 0, 255)
        cv2.putText(x_frame, status_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)

        if self.is_hovering and not self.has_triggered:

            progress_ratio = min(1.0, self.elapsed_time / self.HOLD_THRESHOLD)
            box_width = self.roi[2] - self.roi[0]
            fill_width = int(box_width * progress_ratio)
        
            cv2.rectangle(
                x_frame, 
                (self.roi[0], self.roi[3] - 10), 
                (self.roi[0] + fill_width, self.roi[3]), 
                (0, 255, 255), 
                -1
            )

            # Inside state_stuff.state_change() or your pinch logic:
    def send_packet(self,command_str: str):
        """Serializes string data into raw bytes and fires across loopback."""
        payload = command_str.encode('utf-8')
        client_socket.sendto(payload, (TARGET_IP, TARGET_PORT))


    def check_pinch(self, dist, threshold=30):
        """Edge-Triggered Euclidean Pinch Engine (Prevents Network Flooding)."""
        currently_pinched = dist <= threshold

        # Rising Edge: Present Reality is True, but Historical Record is False
        if currently_pinched and not self.is_pinched:
            self.is_pinched = True
            pag.click()  #not working
            self.send_packet("command")
            #yahan pe packet send kro
        
        # Reset Latch: Hand relaxes beyond distance threshold
        elif not currently_pinched:
            self.is_pinched = False

        return self.is_pinched

    def check_drag(self, dist, threshold=30):
        currently_dragging = dist <= threshold

        # Rising Edge: Initiate the Grab
        if currently_dragging and not self.is_dragging:
            self.is_dragging = True
            pag.mouseDown() # Clamp down on the OS
            print("SYSTEM LOG: Drag sequence initiated.")
        
        # Falling Edge: Release the Grab
        elif not currently_dragging and self.is_dragging:
            self.is_dragging = False
            pag.mouseUp() # Let go of the OS
            print("SYSTEM LOG: Drag sequence terminated.")
            
        return self.is_dragging

    
