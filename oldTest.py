import queue
import threading as thr
import time
import cv2
import mediapipe as mp
import math
import pyautogui as pag
import numpy as np
import spatialClass as sc

pag.PAUSE = 0 
pag.FAILSAFE = False 

SCREEN_W, SCREEN_H = pag.size()
CAM_W, CAM_H = 640, 480
SCREEN_W, SCREEN_H = pag.size()
MARGIN = 100 

# Spatial History (The X/Y Plane)
prev_x, prev_y = 0, 0
SMOOTHING = 8

# Kinematic History (The Z-Axis / Scroll)
prev_scroll_y = None
SCROLL_SENSITIVITY = 5  # Adjust based on your OS scroll speed preference


s1 = sc.state_stuff (12,(100,100,200,300),(0,255,0),1.0)

# Evaluate both states


# Initialize MediaPipe Hand Solutions
mp_hands = mp.solutions.hands  # type: ignore

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)
frame_q = queue.Queue(maxsize=5)
   


def producer():
    while True:
            ret, frame = vid.read() #ret catches the bool, frame gets the matrix 
            if ret:
                frame_q.put(frame)
            else:
                break


def consumer():
    
    c_thread = thr.Thread(target=producer, daemon=True)
    c_thread.start()

    
    prev_x, prev_y = 0, 0
    curr_x, curr_y = 0, 0
    SMOOTHING = 5 # Mathematically equivalent to an alpha of 0.2 (1/5)


    while True:
        start = time.time()
        frame = frame_q.get(True, timeout=5)
        frame = cv2.flip(frame, 1)

        height, width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        hand_in_box = False

        # 1. Spatial Processing  checking collisoins  ..... 
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                index_tip = hand_landmarks.landmark[8]
                cx = int(index_tip.x * width)
                cy = int(index_tip.y * height)

                thumb_tip = hand_landmarks.landmark[4]
                tx = int(thumb_tip.x * width)
                ty = int(thumb_tip.y * height)

                middle_tip = hand_landmarks.landmark[12]
                mx = int(middle_tip.x * width)
                my = int(middle_tip.y * height)

                
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
                cv2.circle(frame, (tx, ty), 10, (255,255, 0), -1)
                cv2.circle(frame, (mx, my), 10, (255,255, 0), -1)

                # 1. Extract raw coordinates
                cx, cy = int(index_tip.x * CAM_W), int(index_tip.y * CAM_H)
                tx, ty = int(thumb_tip.x * CAM_W), int(thumb_tip.y * CAM_H)
                mx, my = int(middle_tip.x * CAM_W), int(middle_tip.y * CAM_H)
                
                # Calculate the new distance
                                # Extract the Gesture Vector
                finger_vector = get_finger_states(hand_landmarks)

                # TELEKINETIC SCROLL STATE: [Index: Extended, Middle: Extended, Ring: Folded, Pinky: Folded]
                if finger_vector[1:] == [1, 1, 0, 0]: 
                    if prev_scroll_y is not None:  #type: ignore
                        delta_y = cy - prev_scroll_y #type: ignore
                        
                        # Deadzone filter to ignore tensor micro-jitters
                        if abs(delta_y) > 2: 
                            pag.scroll(int(-delta_y * SCROLL_SENSITIVITY))
                    
                    # Update temporal anchor and bypass cursor repositioning
                    prev_scroll_y = cy 

                else:
                    # Reset scroll anchor when executing any other gesture or idling
                    prev_scroll_y = None

                # 2. Evaluate Euclidean Pinch State FIRST
                dist = calc_Thumb_Distance(cx, tx, cy, ty)
                is_locked = s1.check_pinch(dist)


                
                if not is_locked:
                  
                    screen_x = np.interp(cx, (MARGIN, CAM_W - MARGIN), (0, SCREEN_W))
                    screen_y = np.interp(cy, (MARGIN, CAM_H - MARGIN), (0, SCREEN_H))

                    
                    curr_x = prev_x + (screen_x - prev_x) / SMOOTHING
                    curr_y = prev_y + (screen_y - prev_y) / SMOOTHING

                    # Instant Execution
                    pag.moveTo(curr_x, curr_y, duration=0)

                    # Save history
                    prev_x, prev_y = curr_x, curr_y
                
                dist = calc_Thumb_Distance(cx,tx,cy,ty)
                if  dist > 30:
                    cv2.line(frame,(cx,cy),(tx,ty),(0,0,255),2)
                    
                else:
                    cv2.line(frame,(cx,cy),(tx,ty),(0,255,0),2)

                dist_drag = calc_Thumb_Distance(mx, tx, my, ty)
                if  dist_drag > 30:
                    cv2.line(frame,(mx,my),(tx,ty),(0,0,255),2)
                    s1.check_drag(dist_drag)
                else:
                    cv2.line(frame,(mx,my),(tx,ty),(0,255,0),2)                    

                
        
                if s1.roi[0] <= cx <= s1.roi[2] and s1.roi[1] <= cy <= s1.roi[3]:
                    hand_in_box = True
        
        if hand_in_box:
           s1.state_change()
           
        else:
            s1.reset_state()

        
        s1.draw_rect(frame)

        
        end = time.time()
        duration = end - start
        if duration > 0:
            c_fps = 1 / duration
            cv2.putText(frame, f"FPS: {int(c_fps)}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('hand tracking frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def calc_Thumb_Distance(x1,x2,y1,y2):

    euc_dist = math.hypot(x1 - x2, y1 - y2)
    return euc_dist

def get_finger_states(hand_landmarks) -> list[int]:
    """
    Translates raw MediaPipe geometry into a binary state vector:
    [Thumb, Index, Middle, Ring, Pinky]
    1 = Extended, 0 = Folded
    """
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]
    states = []
    
    # Thumb: Evaluated along the X-axis against the IP joint (Landmark 3)
    # (Note: This logic flips if using the left hand, but for a right-handed mouse, it holds)
    thumb_open = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    states.append(int(thumb_open))
    
    # Remaining four digits: Evaluated along the Y-axis (Tip higher than PIP)
    for tip, pip in zip(finger_tips, finger_pips):
        is_extended = hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y
        states.append(int(is_extended))
        
    return states


consumer()

vid.release()
cv2.destroyAllWindows()


    
