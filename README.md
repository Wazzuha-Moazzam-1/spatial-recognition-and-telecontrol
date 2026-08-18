
## System Architecture

This project is built on a decoupled, pipeline-driven architecture. The biological intent is captured, mathematically filtered, serialized, and blasted across a network before being executed by independent nodes.

| Subsystem | Technology | Purpose |
| --- | --- | --- |
| **Sensory Input** | OpenCV & MediaPipe | High-speed, sub-millimeter 3D spatial landmark extraction from a raw BGR video feed. |
| **State Estimation** | Alpha-Beta Filter | Predictive kinetic smoothing that anticipates trajectory and eliminates optical sensor jitter. |
| **Network Transport** | UDP Sockets & JSON | Zero-handshake, low-latency transmission of serialized telemetry data across local airwaves. |
| **Hardware Actuation** | Arduino C++ Firmware | Translating standard byte arrays into PWM (Pulse Width Modulation) signals for a micro servo. |
| **Remote Telepresence** | PyAutoGUI | A hysteresis-based state machine executing cross-network cursor manipulation and click events. |

---

## Core Engineering Features

### 1. Alpha-Beta Predictive Filtering

Raw optical data from webcams is inherently chaotic and plagued by thermal noise. Feeding raw coordinates into physical motors will physically destroy the plastic gears. This system implements an Alpha-Beta filter to blend historical position with calculated velocity, predicting the next coordinate and locking the motor into a smooth, disciplined track.

### 2. Chirality Correction

Because camera sensors act as objective observers rather than mirrors, the digital X-axis is inherently inverted compared to human psychological expectation. This pipeline applies a mathematical mirror transformation (`1.0 - x_norm`) before serialization, ensuring the remote system flawlessly mirrors the physical hand.

### 3. Hysteresis Pinch Detection (The Discrete Trigger)

Continuous spatial coordinates cannot trigger discrete events without introducing artificial lag. This system calculates the Euclidean distance between the spatial coordinates of the thumb tip ($x_1, y_1, z_1$) and index finger tip ($x_2, y_2, z_2$) in 3D space:

$$d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2 + (z_2 - z_1)^2}$$

When $d$ drops below a predefined mathematical threshold, a hysteresis state machine triggers a clean `mouseDown` or `mouseUp` event, entirely eliminating double-click stuttering.

### 4. Hardware Safety Clamps

8-bit microcontrollers possess severe mechanical constraints. The Python transmitter assumes all heavy floating-point calculation responsibilities, applying strict mathematical clamps to ensure the resulting integer never commands the micro servo to exceed its mechanical $0^\circ$ to $180^\circ$ physical limit.

---

## Deployment & Execution

### Prerequisites

* Python 3.x
* Arduino IDE & an Arduino Uno (or compatible ATmega328P board)
* A physical Micro Servo
* Target computer (for remote telepresence) connected to the same LAN.

### The Pipeline Flow

1. **Hardware Node:** Flash the `servo_receiver.cpp` firmware to the Arduino Uno.
2. **Target Node:** Execute `remote_listener.py` on the computer you wish to legally commandeer. Ensure UDP Port 5005 is unblocked by the host firewall.
3. **Command Node:** Execute `vision_transmitter.py` on the host machine.

As soon as the camera initializes, the physical constraints between your biological movement and the digital/hardware environments are dissolved.
