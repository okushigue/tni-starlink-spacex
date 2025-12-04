"""
TNI Technical Presentation - 30 Second Demo
Focuses on real-time Δv savings and precision comparison
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List

pygame.init()

@dataclass
class ComparisonData:
    """Stores comparison metrics between standard and TNI navigation"""
    time: float = 0.0
    standard_pos_error: float = 3.0  # meters
    tni_pos_error: float = 3.0
    standard_vel_error: float = 0.1  # m/s
    tni_vel_error: float = 0.1
    dv_saved: float = 0.0

class TNIPresentationSim:
    """30-second technical presentation comparing Standard vs TNI navigation"""
    
    WIDTH = 1400
    HEIGHT = 900
    FPS = 60
    
    # Colors
    BG = (5, 10, 25)
    STANDARD_COLOR = (255, 80, 80)
    TNI_COLOR = (80, 255, 150)
    GRID_COLOR = (40, 50, 70)
    TEXT_COLOR = (255, 255, 255)
    HIGHLIGHT = (255, 200, 0)
    
    def __init__(self):
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("TNI vs Standard Navigation - Technical Comparison")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_title = pygame.font.SysFont('Courier New', 42, bold=True)
        self.font_large = pygame.font.SysFont('Courier New', 32, bold=True)
        self.font_medium = pygame.font.SysFont('Courier New', 24)
        self.font_small = pygame.font.SysFont('Courier New', 18)
        
        # Simulation state
        self.time = 0.0
        self.running = True
        self.data = ComparisonData()
        
        # Graph history
        self.pos_history_std = []
        self.pos_history_tni = []
        self.vel_history_std = []
        self.vel_history_tni = []
        self.max_history = 300  # 5 seconds at 60fps
        
    def update(self, dt: float):
        """Update simulation state"""
        self.time += dt
        t = self.time
        
        # Phase 1: 0-5s - Both systems identical (pre-TNI)
        if t < 5.0:
            self.data.standard_pos_error = 3.0 + random.uniform(-0.2, 0.2)
            self.data.tni_pos_error = 3.0 + random.uniform(-0.2, 0.2)
            self.data.standard_vel_error = 0.1 + random.uniform(-0.01, 0.01)
            self.data.tni_vel_error = 0.1 + random.uniform(-0.01, 0.01)
            self.data.dv_saved = 0.0
            
        # Phase 2: 5-10s - TNI activation (rapid improvement)
        elif t < 10.0:
            activation_time = t - 5.0
            self.data.standard_pos_error = 3.0 + random.uniform(-0.2, 0.2)
            self.data.tni_pos_error = max(0.03, 3.0 * math.exp(-activation_time / 2))
            self.data.standard_vel_error = 0.1 + random.uniform(-0.01, 0.01)
            self.data.tni_vel_error = max(0.001, 0.1 * math.exp(-activation_time / 2))
            
        # Phase 3: 10-25s - TNI maintaining precision
        elif t < 25.0:
            self.data.standard_pos_error = 3.0 + random.uniform(-0.2, 0.2)
            self.data.tni_pos_error = 0.03 + random.uniform(-0.005, 0.005)
            self.data.standard_vel_error = 0.1 + random.uniform(-0.01, 0.01)
            self.data.tni_vel_error = 0.001 + random.uniform(-0.0002, 0.0002)
            
        # Phase 4: 25-30s - Final stats display
        else:
            self.data.standard_pos_error = 3.0 + random.uniform(-0.2, 0.2)
            self.data.tni_pos_error = 0.03 + random.uniform(-0.005, 0.005)
            self.data.standard_vel_error = 0.1 + random.uniform(-0.01, 0.01)
            self.data.tni_vel_error = 0.001 + random.uniform(-0.0002, 0.0002)
        
        # Calculate Δv savings based on error reduction
        error_reduction = (self.data.standard_pos_error - self.data.tni_pos_error) / 3.0
        self.data.dv_saved = min(45.0, error_reduction * 45.0)
        
        # Update history
        self.pos_history_std.append(self.data.standard_pos_error)
        self.pos_history_tni.append(self.data.tni_pos_error)
        self.vel_history_std.append(self.data.standard_vel_error * 1000)  # Convert to mm/s
        self.vel_history_tni.append(self.data.tni_vel_error * 1000)
        
        if len(self.pos_history_std) > self.max_history:
            self.pos_history_std.pop(0)
            self.pos_history_tni.pop(0)
            self.vel_history_std.pop(0)
            self.vel_history_tni.pop(0)
    
    def draw_graph(self, x: int, y: int, w: int, h: int, 
                   data_std: List[float], data_tni: List[float],
                   title: str, y_label: str, max_val: float):
        """Draw a real-time comparison graph"""
        # Background
        pygame.draw.rect(self.screen, (15, 20, 35), (x, y, w, h))
        pygame.draw.rect(self.screen, self.GRID_COLOR, (x, y, w, h), 2)
        
        # Title
        title_surf = self.font_medium.render(title, True, self.TEXT_COLOR)
        self.screen.blit(title_surf, (x + 10, y + 5))
        
        # Grid lines
        for i in range(5):
            grid_y = y + h - (i * h // 4)
            pygame.draw.line(self.screen, self.GRID_COLOR, 
                           (x, grid_y), (x + w, grid_y), 1)
            val_text = self.font_small.render(f"{(i * max_val / 4):.1f}", 
                                             True, (150, 150, 150))
            self.screen.blit(val_text, (x + 5, grid_y - 10))
        
        # Y-axis label
        label_surf = self.font_small.render(y_label, True, (180, 180, 180))
        self.screen.blit(label_surf, (x + 10, y + 35))
        
        # Plot data
        if len(data_std) > 1:
            # Standard system (red)
            points_std = []
            for i, val in enumerate(data_std):
                px = x + (i / self.max_history) * w
                py = y + h - (val / max_val) * (h - 40)
                points_std.append((px, max(y, min(y + h, py))))
            if len(points_std) > 1:
                pygame.draw.lines(self.screen, self.STANDARD_COLOR, False, points_std, 3)
            
            # TNI system (green)
            points_tni = []
            for i, val in enumerate(data_tni):
                px = x + (i / self.max_history) * w
                py = y + h - (val / max_val) * (h - 40)
                points_tni.append((px, max(y, min(y + h, py))))
            if len(points_tni) > 1:
                pygame.draw.lines(self.screen, self.TNI_COLOR, False, points_tni, 3)
        
        # Legend
        legend_y = y + h - 30
        pygame.draw.line(self.screen, self.STANDARD_COLOR, 
                        (x + w - 180, legend_y), (x + w - 150, legend_y), 3)
        std_text = self.font_small.render("Standard", True, self.STANDARD_COLOR)
        self.screen.blit(std_text, (x + w - 145, legend_y - 8))
        
        pygame.draw.line(self.screen, self.TNI_COLOR, 
                        (x + w - 180, legend_y + 15), (x + w - 150, legend_y + 15), 3)
        tni_text = self.font_small.render("TNI", True, self.TNI_COLOR)
        self.screen.blit(tni_text, (x + w - 145, legend_y + 7))
    
    def draw_metrics_panel(self):
        """Draw current metrics comparison panel"""
        panel_x = 50
        panel_y = 650
        panel_w = 1300
        panel_h = 200
        
        # Background
        pygame.draw.rect(self.screen, (20, 25, 40), 
                        (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(self.screen, self.HIGHLIGHT, 
                        (panel_x, panel_y, panel_w, panel_h), 3)
        
        # Current values
        metrics = [
            ("POSITION ERROR", 
             f"{self.data.standard_pos_error:.2f} m", 
             f"{self.data.tni_pos_error*100:.1f} cm",
             f"{self.data.standard_pos_error/self.data.tni_pos_error:.0f}x"),
            ("VELOCITY ERROR", 
             f"{self.data.standard_vel_error*1000:.1f} mm/s", 
             f"{self.data.tni_vel_error*1000:.2f} mm/s",
             f"{self.data.standard_vel_error/self.data.tni_vel_error:.0f}x"),
            ("Δv SAVED", 
             "0.0 m/s", 
             f"{self.data.dv_saved:.1f} m/s",
             f"+{self.data.dv_saved:.1f}")
        ]
        
        col_width = panel_w // 3
        for i, (label, std_val, tni_val, improvement) in enumerate(metrics):
            x_offset = panel_x + 20 + (i * col_width)
            
            # Label
            label_surf = self.font_small.render(label, True, (180, 180, 180))
            self.screen.blit(label_surf, (x_offset, panel_y + 15))
            
            # Standard value (red)
            std_surf = self.font_large.render(std_val, True, self.STANDARD_COLOR)
            self.screen.blit(std_surf, (x_offset, panel_y + 50))
            
            # TNI value (green)
            tni_surf = self.font_large.render(tni_val, True, self.TNI_COLOR)
            self.screen.blit(tni_surf, (x_offset, panel_y + 95))
            
            # Improvement factor
            imp_surf = self.font_medium.render(improvement, True, self.HIGHLIGHT)
            self.screen.blit(imp_surf, (x_offset, panel_y + 150))
    
    def draw_phase_indicator(self):
        """Draw current phase of demonstration"""
        phase_text = ""
        if self.time < 5.0:
            phase_text = "STANDARD NAVIGATION (GPS + TDRSS)"
        elif self.time < 10.0:
            phase_text = "TNI ACTIVATION - LASER MESH LOCK"
        elif self.time < 25.0:
            phase_text = "TNI ACTIVE - PRECISION NAVIGATION"
        else:
            phase_text = "MISSION COMPLETE - OPTIMAL ORBIT"
        
        phase_surf = self.font_large.render(phase_text, True, self.HIGHLIGHT)
        rect = phase_surf.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(phase_surf, rect)
        
        # Time indicator
        time_text = f"T+{self.time:.1f}s / 30.0s"
        time_surf = self.font_medium.render(time_text, True, (150, 150, 150))
        time_rect = time_surf.get_rect(center=(self.WIDTH // 2, 85))
        self.screen.blit(time_surf, time_rect)
    
    def draw(self):
        """Main draw function"""
        self.screen.fill(self.BG)
        
        # Phase indicator
        self.draw_phase_indicator()
        
        # Graphs
        graph_y = 120
        graph_h = 240
        graph_spacing = 20
        
        # Position error graph
        self.draw_graph(50, graph_y, 640, graph_h,
                       self.pos_history_std, self.pos_history_tni,
                       "Position Error", "meters", 3.5)
        
        # Velocity error graph
        self.draw_graph(710, graph_y, 640, graph_h,
                       self.vel_history_std, self.vel_history_tni,
                       "Velocity Error", "mm/s", 120)
        
        # Metrics panel
        self.draw_metrics_panel()
        
        pygame.display.flip()
    
    def run(self):
        """Main loop"""
        while self.running and self.time < 30.0:
            dt = self.clock.tick(self.FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            self.update(dt)
            self.draw()
        
        # Hold final frame for 2 seconds
        if self.time >= 30.0:
            pygame.time.wait(2000)
        
        pygame.quit()

def main():
    sim = TNIPresentationSim()
    sim.run()

if __name__ == "__main__":
    main()
