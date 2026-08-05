import queue
import threading as thr
import time
import cv2
import mediapipe as mp

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

    
s1 = state_stuff (12,(100,100,200,300),(0,255,0),1.0)

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
    global toggle_state, is_hovering, start_time, has_triggered, elapsed_time

    c_thread = thr.Thread(target=producer, daemon=True)
    c_thread.start()
    

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
        
                cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)
        
                if s1.roi[0] <= cx <= s1.roi[2] and s1.roi[1] <= cy <= s1.roi[3]:
                    hand_in_box = True
        

        # Temporal State Machine
        if hand_in_box:
           s1.state_change()
        else:
            s1.reset_state()

        # 3. Canvas & HUD Rendering Pipeline

        s1.draw_rect(frame)

        # Telemetry Calculation
        end = time.time()
        duration = end - start
        if duration > 0:
            c_fps = 1 / duration
            cv2.putText(frame, f"FPS: {int(c_fps)}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('hand tracking frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


consumer()

vid.release()
cv2.destroyAllWindows()


    

