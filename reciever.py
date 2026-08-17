import socket
import json
import pyautogui

# Failsafe: slamming the mouse to the corner of the screen aborts the script
pyautogui.FAILSAFE = True 

UDP_IP = "0.0.0.0" # Listen on all available network interfaces
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Listening for kinetic telemetry...")

# Get the absolute pixel dimensions of this specific monitor (e.g., 1920x1080)
screen_width, screen_height = pyautogui.size()

while True:
    # Buffer size is 1024 bytes. Our JSON payload is tiny, so this is plenty.
    data, addr = sock.recvfrom(1024) 
    
    try:
        # Reconstruct the string from bytes, then parse the JSON back into a dictionary
        telemetry = json.loads(data.decode('utf-8'))
        
        # Translate the normalized (0.0 - 1.0) coordinates to physical screen pixels
        target_x = int(telemetry["x"] * screen_width)
        target_y = int(telemetry["y"] * screen_height)
        
        # Move the cursor instantly to the new coordinates
        pyautogui.moveTo(target_x, target_y, _pause=False)
        
    except Exception as e:
        # UDP packets can arrive mangled or drop entirely. We ignore errors and wait for the next frame.
        pass
