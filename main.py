import sys
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QSlider, QLabel, QGroupBox, QFrame)
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QPolygonF, 
                           QFont, QLinearGradient)
from PySide6.QtCore import Qt, QPointF, QTimer, QDateTime

def interpolate_color(c1, c2, factor):
    """Interpolates between two QColors based on a factor (0.0 to 1.0)"""
    factor = max(0.0, min(1.0, factor))
    r = int(c1.red() + (c2.red() - c1.red()) * factor)
    g = int(c1.green() + (c2.green() - c1.green()) * factor)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
    return QColor(r, g, b, c1.alpha())


class CommaScreen(QWidget):
    """
    Advanced simulation screen representing the windshield-mounted comma 3X hardware.
    Renders a live procedural camera environment underneath the flat UI telemetry overlay.
    """
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 480)
        
        # Telemetry State Variables
        self.confidence = 1.0       
        self.steer_torque = 0.0     
        self.accel_brake = 0.0      
        
        # Audio / Notification Throttling
        self.last_audio_time = 0
        self.audio_cooldown_ms = 1500  # Non-intrusive spacing for audio warnings
        
        # UI Animation and Environmental Timers
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update_environment)
        self.anim_timer.start(33)  # ~30 FPS animation loop
        self.tick_count = 0.0

        # Strict Design Palette (Flat UI)
        self.color_teal = QColor("#17FFAB")
        self.color_amber = QColor("#FFAA00")
        self.color_red = QColor("#FF2222")

    def update_telemetry(self, confidence, steer, accel):
        self.confidence = confidence
        self.steer_torque = steer
        self.accel_brake = accel
        self.check_audio_triggers()
        self.update()

    def update_environment(self):
        self.tick_count += 0.05
        self.update()

    def check_audio_triggers(self):
        """
        Alludes to and includes ambient audio context. 
        Triggers a non-intrusive system alert ONLY when entering critical boundary conditions,
        safeguarded by an anti-annoyance throttle.
        """
        current_time = QDateTime.currentMSecsSinceEpoch()
        max_actuator_load = max(abs(self.steer_torque), abs(self.accel_brake))
        
        # Scenario A: Actuator limits approaching critical limits (85% to 98%)
        # System provides a single soft ambient notification instead of waiting for absolute failure
        if 0.85 <= max_actuator_load < 0.98:
            if current_time - self.last_audio_time > self.audio_cooldown_ms:
                # System beep acts as a placeholder for a soft UI chime
                QApplication.beep()
                print("[UX AUDIO] Soft Pre-Alert: Approaching physical actuator constraints.")
                self.last_audio_time = current_time
                
        # Scenario B: Disengagement Imminent due to low model confidence (< 0.15)
        elif self.confidence < 0.15:
            if current_time - self.last_audio_time > (self.audio_cooldown_ms / 2):
                QApplication.beep()
                print("[UX AUDIO] Critical Alert: Immediate take-over required.")
                self.last_audio_time = current_time

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Draw Simulated Road Camera Feed Background
        self.draw_procedural_camera_feed(painter)
        
        # 2. Draw Vision Model Path Layer
        self.draw_confidence_path(painter)
        
        # 3. Draw Instrumentation / Data Interfaces
        self.draw_actuator_limits(painter)
        self.draw_top_bar(painter)

    def draw_procedural_camera_feed(self, painter):
        """Generates a dynamic background environment mimicking a windshield perspective."""
        w, h = self.width(), self.height()
        horizon_y = h * 0.45

        # Draw Sky
        sky_gradient = QLinearGradient(0, 0, 0, horizon_y)
        sky_gradient.setColorAt(0.0, QColor("#0B0F19"))
        sky_gradient.setColorAt(1.0, QColor("#1A233D"))
        painter.fillRect(0, 0, w, int(horizon_y), sky_gradient)

        # Draw Road Surface
        painter.fillRect(0, int(horizon_y), w, int(h - horizon_y), QColor("#1C1D21"))

        # Draw Animating Road Lane Markings
        painter.setPen(QPen(QColor(255, 255, 255, 60), 2))
        num_lines = 4
        for i in range(num_lines):
            offset = (i + (self.tick_count % 1.0)) / num_lines
            line_y = horizon_y + (offset * (h - horizon_y))
            line_w = 4 + (offset * 24)
            
            # Left Lane Stripe
            lx = (w * 0.2) + (offset * (w * -0.3))
            painter.drawLine(int(lx - line_w), int(line_y), int(lx + line_w), int(line_y))
            # Right Lane Stripe
            rx = (w * 0.8) + (offset * (w * 0.3))
            painter.drawLine(int(rx - line_w), int(line_y), int(rx + line_w), int(line_y))

        # Draw Simulated Lead Car Box (Model Tracking Representation)
        car_w, car_h = 70, 45
        car_cx = (w / 2) + (math.sin(self.tick_count * 0.2) * 30)  # Gentle weaving pattern
        car_cy = horizon_y + 40
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2, Qt.CustomDashLine))
        painter.drawRoundedRect(int(car_cx - car_w/2), int(car_cy - car_h/2), car_w, car_h, 4, 4)

    def draw_confidence_path(self, painter):
        """Translates openpilot confidence states continuously into an explicit analog path overlay."""
        w, h = self.width(), self.height()
        horizon_y = h * 0.45
        bot_y = h * 1.0

        # Calculate Color along a seamless continuous spectrum
        if self.confidence >= 0.5:
            factor = (self.confidence - 0.5) * 2.0
            path_color = interpolate_color(self.color_amber, self.color_teal, factor)
        else:
            factor = self.confidence * 2.0
            path_color = interpolate_color(self.color_red, self.color_amber, factor)

        # Peripheral Visibility Optimization: Oscillate opacity if disengagement is imminent
        alpha = 160
        if self.confidence < 0.3:
            pulse_mod = math.sin(self.tick_count * 8)  # Faster pulse frequency at low confidence
            alpha = int(110 + 90 * pulse_mod)

        # Establish Perspective Geometry Path
        top_width = w * 0.04
        bot_width = w * 0.55
        center_offset = math.sin(self.tick_count * 0.2) * 30  # Snap path to track the simulated lead car
        
        poly = QPolygonF([
            QPointF((w/2) - top_width/2 + center_offset, horizon_y + 5),
            QPointF((w/2) + top_width/2 + center_offset, horizon_y + 5),
            QPointF((w/2) + bot_width/2, bot_y),
            QPointF((w/2) - bot_width/2, bot_y)
        ])

        path_gradient = QLinearGradient(0, horizon_y, 0, bot_y)
        path_gradient.setColorAt(0.0, QColor(path_color.red(), path_color.green(), path_color.blue(), 10))
        path_gradient.setColorAt(1.0, QColor(path_color.red(), path_color.green(), path_color.blue(), alpha))

        painter.setBrush(QBrush(path_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)

    def draw_actuator_limits(self, painter):
        """Displays the 2D Force Envelope showing safety envelopes non-intrusively."""
        w, h = self.width(), self.height()
        box_dim = 130
        margin = 25
        cx = w - (box_dim / 2) - margin
        cy = h - (box_dim / 2) - margin

        # Background Container
        painter.setBrush(QColor(15, 18, 26, 220))
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
        painter.drawRoundedRect(int(cx - box_dim/2), int(cy - box_dim/2), box_dim, box_dim, 10, 10)

        # Crosshairs representing pure neutral state (0.0)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1, Qt.DashLine))
        painter.drawLine(int(cx - box_dim/2), int(cy), int(cx + box_dim/2), int(cy))
        painter.drawLine(int(cx), int(cy - box_dim/2), int(cx), int(cy + box_dim/2))

        # Reticle Coordinates mapping Torque (X) and Accel/Brake (Y)
        radius_bounds = box_dim / 2
        dot_x = cx + (self.steer_torque * radius_bounds)
        dot_y = cy - (self.accel_brake * radius_bounds)  # Inverted UI coordinates

        max_load = max(abs(self.steer_torque), abs(self.accel_brake))
        if max_load >= 0.9:
            dot_color = self.color_red
            glow = 14
        elif max_load >= 0.7:
            dot_color = self.color_amber
            glow = 10
        else:
            dot_color = self.color_teal
            glow = 7

        # Render Tracking Dot
        painter.setBrush(dot_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(dot_x, dot_y), glow, glow)

        # Minimalist Text Metrics label
        painter.setFont(QFont("Inter", 8, QFont.Bold))
        painter.setPen(QColor(255, 255, 255, 120))
        painter.drawText(int(cx - box_dim/2 + 6), int(cy - box_dim/2 + 16), "LIMIT ENVELOPE")

    def draw_top_bar(self, painter):
        """Minimalist head-up notification text bar optimized for peripheral glances."""
        painter.setFont(QFont("Inter", 15, QFont.Bold))
        if self.confidence > 0.15:
            painter.setPen(self.color_teal)
            painter.drawText(25, 40, "openpilot ENGAGED")
        else:
            painter.setPen(self.color_red)
            painter.drawText(25, 40, "TAKE CONTROL IMMEDIATELY")


class SimulationControlPanel(QWidget):
    """Generates a contextual configuration control rig to alter live telemetry variables."""
    def __init__(self, target_ui):
        super().__init__()
        self.target_ui = target_ui
        self.setFixedWidth(280)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("<h3>Telemetry Simulation</h3>"))
        
        # Confidence Controller Component
        group_conf = QGroupBox("Model Driving Confidence Spectrum")
        vbox_conf = QVBoxLayout()
        self.slide_conf = QSlider(Qt.Horizontal)
        self.slide_conf.setRange(0, 100)
        self.slide_conf.setValue(100)
        self.label_conf = QLabel("1.00 - Pretty Reliable")
        vbox_conf.addWidget(self.slide_conf)
        vbox_conf.addWidget(self.label_conf)
        group_conf.setLayout(vbox_conf)
        
        # Steering Torque Controller Component
        group_steer = QGroupBox("Steering Torque Request")
        vbox_steer = QVBoxLayout()
        self.slide_steer = QSlider(Qt.Horizontal)
        self.slide_steer.setRange(-100, 100)
        self.slide_steer.setValue(0)
        self.label_steer = QLabel("0.00 - Center Equilibrium")
        vbox_steer.addWidget(self.slide_steer)
        vbox_steer.addWidget(self.label_steer)
        group_steer.setLayout(vbox_steer)

        # Acceleration/Deceleration Pressure Component
        group_accel = QGroupBox("Accel / Brake Application")
        vbox_accel = QVBoxLayout()
        self.slide_accel = QSlider(Qt.Horizontal)
        self.slide_accel.setRange(-100, 100)
        self.slide_accel.setValue(0)
        self.label_accel = QLabel("0.00 - Neutral Coasting")
        vbox_accel.addWidget(self.slide_accel)
        vbox_accel.addWidget(self.label_accel)
        group_accel.setLayout(vbox_accel)

        main_layout.addWidget(group_conf)
        main_layout.addWidget(group_steer)
        main_layout.addWidget(group_accel)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # Signals Map
        self.slide_conf.valueChanged.connect(self.process_signals)
        self.slide_steer.valueChanged.connect(self.process_signals)
        self.slide_accel.valueChanged.connect(self.process_signals)

    def process_signals(self):
        conf_val = self.slide_conf.value() / 100.0
        steer_val = self.slide_steer.value() / 100.0
        accel_val = self.slide_accel.value() / 100.0

        if conf_val >= 0.75:
            conf_desc = "Pretty Reliable (Model Certain)"
        elif conf_val >= 0.30:
            conf_desc = "May/May Not Work (Degrading)"
        else:
            conf_desc = "Expected Failure (Disengage Imminent)"

        self.label_conf.setText(f"{conf_val:.2f} - {conf_desc}")
        self.label_steer.setText(f"{steer_val:.2f} - Torque")
        self.label_accel.setText(f"{accel_val:.2f} - Load Vector")

        self.target_ui.update_telemetry(conf_val, steer_val, accel_val)


class ApplicationWorkspace(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("comma.ai UI/UX Solution Validation Framework")
        self.setStyleSheet("background-color: #11141C; color: #E2E8F0; font-family: 'Inter', sans-serif;")

        root_widget = QWidget()
        layout = QHBoxLayout()

        self.display_screen = CommaScreen()
        self.control_rig = SimulationControlPanel(self.display_screen)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Plain)
        divider.setStyleSheet("color: #2D3748;")

        layout.addWidget(self.display_screen, stretch=1)
        layout.addWidget(divider)
        layout.addWidget(self.control_rig)

        root_widget.setLayout(layout)
        self.setCentralWidget(root_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    workspace = ApplicationWorkspace()
    workspace.resize(1180, 540)
    workspace.show()
    sys.exit(app.exec())