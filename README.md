# openpilot-ui-challenge
Design challenge from leaderboard.

A functional prototype built using Python and PySide6 (Qt) demonstrating an improved flat UI/UX paradigm for the comma 3X hardware. This solution re-imagines how an autonomous system communicates continuous model confidence states and upcoming mechanical vehicle limitations to drivers non-intrusively.

##  Design Strategy & Core Solutions

Windshield-mounted hardware presents a unique challenge: the driver must interpret system states via quick peripheral glances without getting distracted by small text strings or startled by abrupt audible alerts.

### 1. Continuous Driving Confidence Spectrum (The Aura Path)
Instead of forcing discrete, stepped UI notifications, this application maps openpilot's self-awareness metric (`0.0` to `1.0`) across an interpolated mathematical color gradient onto the lane perspective visualization matrix:
* **High Confidence (1.0 - 0.75):** Renders as standard openpilot Teal, signaling steady operations.
* **Medium Confidence (0.75 - 0.30):** Interpolates smoothly into Amber, alerting the driver that disengagement may be necessary within a few minutes.
* **Imminent Takeover (< 0.30):** Shifts to solid Red. 
* **Peripheral Optimization:** When confidence slips into the danger threshold (< 0.30), the path triggers a sine-wave geometric opacity pulsation. This instantly catches human peripheral vision without relying on sound.

### 2. Actuator Force Safety Envelope (Real-time Limit Tracking)
The stock system sounds an alarm only *after* the steering torque has completely washed out and the vehicle starts drifting. This prototype resolves that limitation using a visual **Friction Circle / Limit Envelope** UI component located in the screen corner:
* **Dual Axis Telemetry:** Maps current real-time steering torque requirements ($X$-axis) against active braking and acceleration values ($Y$-axis).
* **Predictive Visual Warning:** The tracking point lights up Amber when crossing $70\%$ capacity and switches to Red at $90\%$ capacity. Drivers can visually see the vehicle running out of performance capacity *before* system limits force a disengagement event.
* **Throttled Auditory Chimes:** Replaces constant auditory alarms with a smart, delayed pre-alert ping system that prevents audio clutter when tracking near boundaries.

---

## Architecture & Performance Choices
* **Pure C++ Qt/PySide Graphic Framework:** Uses native `QPainter` layout vectors to guarantee a flat UI with zero 3D drop shadows, keeping rendering overhead minimum on embedded hardware.
* **Procedural Camera Simulator Layer:** Renders a moving environmental road background directly underneath the vector lanes to accurately replicate real-world windshield visibility conditions.

---

##  Installation & Quickstart

This workspace has been fully tested on Apple Silicon (M4 Architecture) using Python 3 and VS Code.

### 1. Setup Environment
Clone the repository, initialize a virtual environment, and activate it:
```bash
git clone <your-repository-url>
cd openpilot-ui-challenge
python3 -m venv venv
source venv/bin/activate

### 2. Install Dependencies

Bash
pip install -r requirements.txt

### 3. Execution
Launch the validation and simulation framework dashboard:

Bash
pythonmain.py

Validation InstructionsUtilize the integrated right-hand Telemetry Simulation Control Rig to test the specific engineering constraints:Slide the Confidence Matrix Down: Note the linear, seamless color transition from Teal to Amber to Red. Observe the automated flashing animation below 0.30.Shift Steering/Braking Controls towards Max Extents (1.00 or -1.00): Observe the indicator element smoothly move out towards the bounding envelope walls. Watch it transition its color profile to map warning vectors before terminal failure thresholds occur.
