"""
TNI Simulator - Transient Node Integration for Satellite Networks

This simulator demonstrates the Transient Node Integration (TNI) concept,
which uses Starlink satellites as temporary navigation nodes to assist
in orbital insertion and reduce delta-v requirements.
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
import sys
import os
from datetime import datetime


# Initialize Pygame
pygame.init()
pygame.display.set_caption("TNI Simulator – Starlink Transient Node Integration")


@dataclass
class Satellite:
    """
    Represents a Starlink satellite in the simulation.

    Attributes:
        id: Unique identifier for the satellite.
        x: X-coordinate in the simulation space.
        y: Y-coordinate in the simulation space.
        angle: Orbital angle in radians.
        omega: Angular velocity (default 0.0011 rad/s).
    """
    id: int
    x: float
    y: float
    angle: float
    omega: float = 0.0011


@dataclass
class Vehicle:
    """
    Represents the launch vehicle in the simulation.

    Attributes:
        x: X-coordinate in the simulation space.
        y: Y-coordinate in the simulation space.
        alt: Altitude in kilometers.
        angle: Orbital angle in radians.
    """
    x: float = 0.0
    y: float = 0.0
    alt: float = 0.0
    angle: float = 0.0


class TNISimulator:
    """
    Main class for the TNI (Transient Node Integration) Simulator.

    This simulator demonstrates the TNI concept where a launch vehicle
    dynamically connects to Starlink satellites to refine its trajectory
    during orbital insertion, potentially saving fuel (delta-v).
    """

    # Physical constants
    EARTH_RADIUS_KM = 6371
    STARLINK_ALT_KM = 550
    # Scale: pixels per kilometer
    SCALE_PX_PER_KM = 0.045
    CENTER_X = 400
    CENTER_Y = 400  # Assuming HEIGHT // 2 = 400 for default

    # Colors (RGB)
    COLORS = {
        'BACKGROUND': (0, 8, 20),
        'EARTH_BLUE': (30, 58, 95),
        'EARTH_OUTLINE': (58, 134, 255),
        'STARLINK_ORBIT': (255, 255, 255, 34),
        'STARLINK_SAT': (131, 56, 236),
        'ROCKET_INACTIVE': (255, 0, 110),
        'ROCKET_ACTIVE': (6, 255, 165),
        'LASER_COLOR': (6, 255, 165),
        'TEXT_COLOR': (255, 255, 255),
        'PANEL_BG': (30, 35, 45, 220),
        'PANEL_BORDER': (70, 130, 180),
        'GREEN': (0, 255, 100),
        'YELLOW': (255, 255, 0),
        'BLUE': (100, 180, 255),
        'RED': (255, 50, 50),
        'DARK_GRAY': (40, 40, 40),
        'LIGHT_GRAY': (180, 180, 180),
    }

    # Time phases in seconds
    TIME_PHASES = {
        'ASCENT': (0, 150),
        'TNI_ACTIVATION': (150, 170),
        'ORBITAL_INSERTION': (170, 290),
        'TNI_DISCONNECT': (290, 310),
        'NOMINAL_ORBIT': (310, float('inf'))
    }

    # Speed multipliers
    SPEED_MULTIPLIERS = [0.25, 0.5, 1.0, 2.0, 4.0]
    SPEED_LABELS = ["1/4x", "1/2x", "1x", "2x", "4x"]

    def __init__(self, width: int = 1200, height: int = 800) -> None:
        """
        Initializes the TNI Simulator.

        Args:
            width: Width of the simulation window in pixels.
            height: Height of the simulation window in pixels.
        """
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.CENTER_Y = height // 2  # Update CENTER_Y based on actual height

        # Simulation state
        self.time_s = 0.0
        self.is_running = False
        self.current_phase = "PRE-LAUNCH"
        self.altitude_km = 0.0
        self.position_error_m = 25.0
        self.velocity_error_mps = 0.15
        self.dv_saved_mps = 0.0
        self.active_links = 0
        self.is_tni_active = False

        # Speed control
        self.speed_index = 2  # Default to 1x
        self.current_speed_multiplier = self.SPEED_MULTIPLIERS[self.speed_index]

        # Initialize objects
        self.satellites = self._init_satellites()
        self.vehicle = Vehicle()

        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_medium = pygame.font.SysFont('Arial', 18)
        self.font_title = pygame.font.SysFont('Arial', 28, bold=True)
        self.font_large = pygame.font.SysFont('Arial', 32, bold=True)

        # Video recording setup
        self.RECORD_VIDEO = True
        self.video_writer = None
        self.frames = []
        self.video_name = f"TNI_demo_{datetime.now():%Y%m%d_%H%M%S}.mp4"

        if self.RECORD_VIDEO:
            try:
                import imageio.v3 as iio
                self.iio = iio
            except ImportError:
                print("imageio not installed. Video recording disabled.")
                self.RECORD_VIDEO = False

    def _init_satellites(self) -> List[Satellite]:
        """
        Initializes the Starlink satellite constellation.

        Returns:
            A list of Satellite objects arranged in orbit.
        """
        num_sats = 18
        satellites = []
        for i in range(num_sats):
            angle = (i / 18) * 2 * math.pi + (i % 2) * 0.3
            x = (self.EARTH_RADIUS_KM + self.STARLINK_ALT_KM) * math.cos(angle)
            y = (self.EARTH_RADIUS_KM + self.STARLINK_ALT_KM) * math.sin(angle)
            satellites.append(Satellite(i, x, y, angle))
        return satellites

    def _update_simulation_state(self, dt: float) -> None:
        """
        Updates the simulation state based on the elapsed time.

        Args:
            dt: Delta time since last update in seconds.
        """
        if not self.is_running:
            return

        # Apply speed multiplier to delta time
        effective_dt = dt * self.current_speed_multiplier
        self.time_s += effective_dt
        t = self.time_s

        # Define phase and update state variables based on time
        if t < self.TIME_PHASES['ASCENT'][1]:
            self.current_phase = "ASCENT"
            self.altitude_km = (t / 150) * 200
            self.is_tni_active = False
            self.active_links = 0
            self.position_error_m = 25.0
            self.velocity_error_mps = 0.15

        elif t < self.TIME_PHASES['TNI_ACTIVATION'][1]:
            self.current_phase = "TNI ACTIVATION"
            self.is_tni_active = True
            self.active_links = min(10, int((t - 150) * 0.5))
            tni_time = t - 150
            self.position_error_m = max(0.03, 20 * math.exp(-tni_time / 9))
            self.velocity_error_mps = max(0.003, 0.15 * math.exp(-tni_time / 7))

        elif t < self.TIME_PHASES['ORBITAL_INSERTION'][1]:
            self.current_phase = "ORBITAL INSERTION"
            self.altitude_km = 200 + (t - 170) * 0.91
            self.position_error_m = 0.03 + random.random() * 0.02
            self.velocity_error_mps = 0.002 + random.random() * 0.001
            self.dv_saved_mps = 45 * (1 - self.position_error_m / 25)

        elif t < self.TIME_PHASES['TNI_DISCONNECT'][1]:
            self.current_phase = "TNI DISCONNECT"
            self.active_links = max(0, 10 - int((t - 290) * 0.5))

        else:  # t >= 310
            self.current_phase = "NOMINAL ORBIT"
            self.is_running = False

        # Update vehicle position
        r = self.EARTH_RADIUS_KM + self.altitude_km
        vehicle_angle = t * 0.02
        self.vehicle.x = r * math.cos(vehicle_angle)
        self.vehicle.y = r * math.sin(vehicle_angle)
        self.vehicle.angle = vehicle_angle
        self.vehicle.alt = self.altitude_km

        # Update satellite positions
        for sat in self.satellites:
            sat.angle += sat.omega * effective_dt
            rs = self.EARTH_RADIUS_KM + self.STARLINK_ALT_KM
            sat.x = rs * math.cos(sat.angle)
            sat.y = rs * math.sin(sat.angle)

    def _draw_earth_and_orbits(self) -> None:
        """Draws the Earth and the Starlink satellite orbit with enhanced visuals."""
        # Draw Earth with a subtle gradient effect
        earth_radius_px = int(self.EARTH_RADIUS_KM * self.SCALE_PX_PER_KM)
        pygame.draw.circle(
            self.screen, self.COLORS['EARTH_BLUE'],
            (self.CENTER_X, self.CENTER_Y), earth_radius_px
        )
        # Draw a subtle outline
        pygame.draw.circle(
            self.screen, self.COLORS['EARTH_OUTLINE'],
            (self.CENTER_X, self.CENTER_Y), earth_radius_px, 2
        )

        # Draw a faint glow around Earth
        glow_radius = earth_radius_px + 10
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.COLORS['EARTH_BLUE'], 50), (glow_radius, glow_radius), glow_radius)
        self.screen.blit(glow_surf, (self.CENTER_X - glow_radius, self.CENTER_Y - glow_radius))

        # Draw Starlink orbit
        starlink_orbit_radius_px = int((self.EARTH_RADIUS_KM + self.STARLINK_ALT_KM) * self.SCALE_PX_PER_KM)
        # Draw orbit path with alpha
        orbit_surf = pygame.Surface((starlink_orbit_radius_px * 2, starlink_orbit_radius_px * 2), pygame.SRCALPHA)
        pygame.draw.circle(orbit_surf, self.COLORS['STARLINK_ORBIT'], (starlink_orbit_radius_px, starlink_orbit_radius_px), starlink_orbit_radius_px, 1)
        self.screen.blit(orbit_surf, (self.CENTER_X - starlink_orbit_radius_px, self.CENTER_Y - starlink_orbit_radius_px))

    def _draw_laser_links(self) -> None:
        """Draws the laser links between the vehicle and active satellites."""
        if not self.is_tni_active or self.active_links == 0:
            return

        # Calculate vehicle screen position
        vx = self.CENTER_X + self.vehicle.x * self.SCALE_PX_PER_KM
        vy = self.CENTER_Y + self.vehicle.y * self.SCALE_PX_PER_KM

        # Calculate distances to all satellites
        distances_and_sats = []
        for sat in self.satellites:
            sx = self.CENTER_X + sat.x * self.SCALE_PX_PER_KM
            sy = self.CENTER_Y + sat.y * self.SCALE_PX_PER_KM
            distance = math.hypot(vx - sx, vy - sy)
            distances_and_sats.append((distance, sat, sx, sy))

        # Sort by distance and draw links to closest active_links satellites
        distances_and_sats.sort(key=lambda x: x[0])
        for i, (_, sat, sx, sy) in enumerate(distances_and_sats[:self.active_links]):
            pulse = 0.7 + 0.3 * math.sin(self.time_s * 10 + i)
            width = 3 if pulse > 0.9 else 2
            color = self.COLORS['LASER_COLOR']

            # Draw a pulsing line with alpha effect
            # For simplicity, we use the base color with slight variation for pulse
            adjusted_color = tuple(min(255, int(c * pulse)) for c in color)
            pygame.draw.line(self.screen, adjusted_color, (sx, sy), (vx, vy), width)

            # Draw a fainter, wider line underneath for a glow effect
            pygame.draw.line(self.screen, (*adjusted_color, 100), (sx, sy), (vx, vy), width + 2)

    def _draw_vehicle(self) -> None:
        """Draws the launch vehicle with enhanced visuals."""
        if self.altitude_km <= 0:
            return

        vx = self.CENTER_X + self.vehicle.x * self.SCALE_PX_PER_KM
        vy = self.CENTER_Y + self.vehicle.y * self.SCALE_PX_PER_KM
        size = 28

        # Create a surface for the vehicle
        surf = pygame.Surface((size, size * 2), pygame.SRCALPHA)
        color = self.COLORS['ROCKET_ACTIVE'] if self.is_tni_active else self.COLORS['ROCKET_INACTIVE']

        # Draw main body
        pygame.draw.rect(surf, color, (size // 2 - 4, 0, 8, size * 2))
        # Draw nose cone
        pygame.draw.polygon(surf, color, [
            (size // 2, 0), (size // 2 - 6, 8), (size // 2 + 6, 8)
        ])
        # Draw fins
        pygame.draw.polygon(surf, color, [
            (size // 2 - 4, size * 1.5), (size // 2 - 12, size * 2), (size // 2 + 4, size * 2)
        ])
        pygame.draw.polygon(surf, color, [
            (size // 2 + 4, size * 1.5), (size // 2 + 12, size * 2), (size // 2 - 4, size * 2)
        ])

        # Add a small TNI indicator light if active
        if self.is_tni_active:
             pygame.draw.circle(surf, self.COLORS['LASER_COLOR'], (size // 2, 4), 3)

        # Rotate and draw the vehicle
        rotated_surf = pygame.transform.rotate(
            surf, -math.degrees(self.vehicle.angle + math.pi / 2)
        )
        rect = rotated_surf.get_rect(center=(int(vx), int(vy)))
        self.screen.blit(rotated_surf, rect)

    def _draw_satellites(self) -> None:
        """Draws the Starlink satellites with enhanced visuals."""
        for sat in self.satellites:
            sx = int(self.CENTER_X + sat.x * self.SCALE_PX_PER_KM)
            sy = int(self.CENTER_Y + sat.y * self.SCALE_PX_PER_KM)
            # Draw main dot
            pygame.draw.circle(self.screen, self.COLORS['STARLINK_SAT'], (sx, sy), 5)
            # Draw a fainter glow around it
            pygame.draw.circle(self.screen, (*self.COLORS['STARLINK_SAT'], 80), (sx, sy), 8, 1)

    def _draw_ui(self) -> None:
        """Draws the user interface panel."""
        panel_x = 850
        panel_y_start = 40
        line_height = 32

        ui_data = [
            ("Phase", self.current_phase, self.COLORS['YELLOW'] if "ACTIV" in self.current_phase else self.COLORS['GREEN']),
            ("Time", f"{self.time_s:.1f} s", self.COLORS['TEXT_COLOR']),
            ("Altitude", f"{self.altitude_km:.1f} km", self.COLORS['TEXT_COLOR']),
            ("Links", f"{self.active_links}/10", self.COLORS['GREEN'] if self.active_links > 6 else self.COLORS['YELLOW']),
            ("Pos Error", f"{self.position_error_m * 100:.1f} cm" if self.position_error_m < 1 else f"{self.position_error_m:.1f} m", self.COLORS['GREEN']),
            ("Vel Error", f"{self.velocity_error_mps * 1000:.1f} mm/s", self.COLORS['GREEN']),
            ("Δv Saved", f"{self.dv_saved_mps:.1f} m/s", self.COLORS['GREEN']),
        ]

        for i, (label, value, color) in enumerate(ui_data):
            y_pos = panel_y_start + i * line_height
            self.screen.blit(
                self.font_small.render(label, True, (180, 180, 180)),
                (panel_x, y_pos)
            )
            self.screen.blit(
                self.font_small.render(str(value), True, color),
                (panel_x + 170, y_pos)
            )

        # Draw title
        self.screen.blit(
            self.font_title.render("TNI Simulator", True, self.COLORS['BLUE']),
            (30, 30)
        )

        # Draw speed control
        speed_label = f"Speed: {self.SPEED_LABELS[self.speed_index]}"
        self.screen.blit(
            self.font_medium.render(speed_label, True, self.COLORS['TEXT_COLOR']),
            (30, self.height - 130)
        )

        # Draw control button
        button_rect = pygame.Rect(30, self.height - 80, 200, 50)
        button_color = self.COLORS['GREEN'] if not self.is_running else (200, 80, 0)
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            # Lighten color on hover
            button_color = tuple(min(255, c + 50) for c in button_color)

        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.COLORS['TEXT_COLOR'], button_rect, 3, border_radius=10)

        button_text = "START" if not self.is_running else "PAUSE"
        text_surf = self.font_medium.render(button_text, True, self.COLORS['TEXT_COLOR'])
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

    def _handle_speed_change(self, direction: int) -> None:
        """
        Changes the simulation speed.

        Args:
            direction: 1 for increase, -1 for decrease.
        """
        new_index = self.speed_index + direction
        if 0 <= new_index < len(self.SPEED_MULTIPLIERS):
            self.speed_index = new_index
            self.current_speed_multiplier = self.SPEED_MULTIPLIERS[self.speed_index]

    def run(self) -> None:
        """
        Main loop for the simulator.
        Handles events, updates state, draws everything, and manages the video recording.
        """
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    # Check for button click
                    if 30 <= mouse_x <= 230 and self.height - 80 <= mouse_y <= self.height - 30:
                        self.is_running = not self.is_running
                    # Check for speed control clicks (simple area check)
                    elif 30 <= mouse_x <= 230 and self.height - 140 <= mouse_y <= self.height - 100:
                         # Click on speed label area to cycle through speeds
                         self._handle_speed_change(1)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_running = not self.is_running
                    elif event.key == pygame.K_r:
                        self.__init__(self.width, self.height)  # Re-initialize
                        self.is_running = False
                    elif event.key == pygame.K_UP:
                        self._handle_speed_change(1)
                    elif event.key == pygame.K_DOWN:
                        self._handle_speed_change(-1)

            # Update simulation
            self._update_simulation_state(dt)

            # Draw everything
            self.screen.fill(self.COLORS['BACKGROUND'])
            self._draw_earth_and_orbits()
            self._draw_satellites()
            self._draw_laser_links()
            self._draw_vehicle()
            self._draw_ui()

            # Record frame if enabled
            if self.RECORD_VIDEO:
                frame = pygame.surfarray.array3d(self.screen).swapaxes(0, 1)[:, :, ::-1]
                self.frames.append(frame.copy())

            pygame.display.flip()

        # Save video if frames were recorded
        if self.RECORD_VIDEO and self.frames:
            print(f"Saving video to {self.video_name} ... (~20 seconds)")
            try:
                # Use imageio to write the video
                self.iio.imwrite(
                    self.video_name,
                    self.frames,
                    fps=60,
                    codec="libx264",
                    pixel_format="yuv420p",
                    quality=8
                )
                print(f"Video saved successfully to {os.path.abspath(self.video_name)}")
            except Exception as e:
                print(f"Error saving video: {e}")

        # Quit Pygame
        pygame.quit()
        sys.exit()


def main() -> None:
    """Main entry point for the application."""
    simulator = TNISimulator()
    simulator.run()


if __name__ == "__main__":
    main()
