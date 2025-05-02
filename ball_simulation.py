import pygame
import sys
import math
import random
import dataflow_analysis
import numpy as np

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH = 1080
HEIGHT = 540
PANEL_WIDTH = 300  # Width of the new white panel
EXTENDED_WIDTH = WIDTH + PANEL_WIDTH
screen = pygame.display.set_mode((EXTENDED_WIDTH, HEIGHT))
pygame.display.set_caption("Pool Game Simulation")
prediction = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BROWN = (165, 42, 42)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 100, 0)

# Pool table color
TABLE_COLOR = DARK_GREEN

# Ball properties
BALL_RADIUS = 20
POCKET_RADIUS = BALL_RADIUS * 2  # Increased from 1.4 to 2.5 to make holes bigger
FRICTION = 0.992  # Friction coefficient
MIN_VELOCITY = 0.01  # Minimum velocity before stopping the ball

# Pocket positions
POCKETS = [
    (0, 0),          # Top-left
    (WIDTH // 2, 0), # Top-middle
    (WIDTH, 0),      # Top-right
    (0, HEIGHT),     # Bottom-left
    (WIDTH // 2, HEIGHT), # Bottom-middle
    (WIDTH, HEIGHT)  # Bottom-right
]

# UI elements
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 40
SLIDER_WIDTH = 200
SLIDER_HEIGHT = 20
UI_PADDING = 30

# Ball colors (one white cue ball, others with different colors)
BALL_COLORS = [WHITE, RED, YELLOW, BLUE, PURPLE, ORANGE, GREEN, BROWN, BLACK]

class Ball:
    def __init__(self, x, y, color, radius=BALL_RADIUS):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0
        self.alive = True
        self.is_cue_ball = (color == WHITE)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Draw direction arrow for cue ball when not moving
        if self.is_cue_ball and abs(self.velocity_x) < MIN_VELOCITY and abs(self.velocity_y) < MIN_VELOCITY and not simulation_started:
            arrow_length = initial_velocity * 20  # Scale the arrow by velocity
            end_x = self.x + arrow_length * math.cos(math.radians(initial_angle))
            end_y = self.y + arrow_length * math.sin(math.radians(initial_angle))
            pygame.draw.line(screen, RED, (self.x, self.y), (end_x, end_y), 3)
            # Draw arrowhead
            pygame.draw.circle(screen, RED, (int(end_x), int(end_y)), 5)


class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        self.font = pygame.font.SysFont(None, 24)
        
    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # Border
        
        text_surf = self.font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, discrete_values=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.handle_radius = height
        self.font = pygame.font.SysFont(None, 20)
        self.active = False
        self.discrete_values = discrete_values  # List of allowed values, or None for continuous

    def draw(self, screen):
        # Draw the track
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 1)
        # Calculate handle position
        if self.discrete_values:
            # Find index of current value
            idx = self.discrete_values.index(self.val)
            handle_x = self.rect.x + int(idx / (len(self.discrete_values) - 1) * self.rect.width)
        else:
            handle_x = self.rect.x + int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        # Draw the handle
        pygame.draw.circle(screen, WHITE, (handle_x, self.rect.y + self.rect.height // 2), self.handle_radius)
        pygame.draw.circle(screen, BLACK, (handle_x, self.rect.y + self.rect.height // 2), self.handle_radius, 1)
        # Draw the label and value
        label_text = self.font.render(f"{self.label}: {self.val:.2f}" if self.discrete_values else f"{self.label}: {self.val:.1f}", True, BLACK)
        screen.blit(label_text, (self.rect.x, self.rect.y - 20))

    def is_over_handle(self, pos):
        if self.discrete_values:
            idx = self.discrete_values.index(self.val)
            handle_x = self.rect.x + int(idx / (len(self.discrete_values) - 1) * self.rect.width)
        else:
            handle_x = self.rect.x + int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        handle_y = self.rect.y + self.rect.height // 2
        distance = math.sqrt((pos[0] - handle_x)**2 + (pos[1] - handle_y)**2)
        return distance <= self.handle_radius

    def update(self, pos):
        if self.active:
            x_pos = max(self.rect.x, min(pos[0], self.rect.x + self.rect.width))
            ratio = (x_pos - self.rect.x) / self.rect.width
            if self.discrete_values:
                idx = int(round(ratio * (len(self.discrete_values) - 1)))
                idx = max(0, min(idx, len(self.discrete_values) - 1))
                self.val = self.discrete_values[idx]
            else:
                self.val = self.min_val + ratio * (self.max_val - self.min_val)

def create_triangle_formation(start_x, start_y):
    balls = []
    rows = 4
    colors = BALL_COLORS.copy()
    
    # Create a white cue ball on the left side
    cue_ball = Ball(WIDTH // 4, HEIGHT // 2, WHITE)
    balls.append(cue_ball)
    colors.remove(WHITE)
    
    # Create the triangle formation
    ball_count = 1
    y_offset = 0
    for row in range(rows): #rows
        for i in range(ball_count): #ball_count
            x = start_x + row * (BALL_RADIUS * 2)
            y = start_y + y_offset + i * (BALL_RADIUS * 2.1)
            
            color = random.choice(colors)
            colors.remove(color)
            if not colors:  # If we run out of colors, reset the list
                colors = BALL_COLORS.copy()
                colors.remove(WHITE)  # Always keep white for the cue ball only
                
            ball = Ball(x, y, color)
            balls.append(ball)
        
        y_offset -= BALL_RADIUS
        ball_count += 1
        
    return balls


def update_balls(balls):
    """
    Update all balls: move, handle wall and ball collisions, and check if all stopped.
    Returns True if all balls have stopped, False otherwise.
    """
    # Move balls and handle wall collisions
    for ball in balls:
        if ball.alive:
            # Move
            ball.x += ball.velocity_x
            ball.y += ball.velocity_y
            # Friction
            ball.velocity_x *= FRICTION
            ball.velocity_y *= FRICTION
            # Stop if very slow
            if abs(ball.velocity_x) < MIN_VELOCITY and abs(ball.velocity_y) < MIN_VELOCITY:
                ball.velocity_x = 0
                ball.velocity_y = 0
            # Wall collision
            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.velocity_x = -ball.velocity_x * 0.9
            elif ball.x + ball.radius > WIDTH:
                ball.x = WIDTH - ball.radius
                ball.velocity_x = -ball.velocity_x * 0.9
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.velocity_y = -ball.velocity_y * 0.9
            elif ball.y + ball.radius > HEIGHT:
                ball.y = HEIGHT - ball.radius
                ball.velocity_y = -ball.velocity_y * 0.9
            # Pocket check
            for pocket_x, pocket_y in POCKETS:
                distance = math.sqrt((ball.x - pocket_x)**2 + (ball.y - pocket_y)**2)
                if distance < POCKET_RADIUS:
                    ball.alive = False
    # Ball-ball collision
    for i, ball1 in enumerate(balls):
        if not ball1.alive:
            continue
        for j, ball2 in enumerate(balls[i+1:], i+1):
            if not ball2.alive:
                continue
            dx = ball2.x - ball1.x
            dy = ball2.y - ball1.y
            distance = math.sqrt(dx*dx + dy*dy)
            if distance < ball1.radius + ball2.radius:
                nx = dx / distance
                ny = dy / distance
                dvx = ball2.velocity_x - ball1.velocity_x
                dvy = ball2.velocity_y - ball1.velocity_y
                velocity_along_normal = dvx * nx + dvy * ny
                if velocity_along_normal > 0:
                    continue
                # Calculate impulse. don't change this
                impulse = 1.5 * velocity_along_normal / 2
                ball1.velocity_x += impulse * nx
                ball1.velocity_y += impulse * ny
                ball2.velocity_x -= impulse * nx
                ball2.velocity_y -= impulse * ny

                overlap = (ball1.radius + ball2.radius - distance) / 2
                ball1.x -= overlap * nx
                ball1.y -= overlap * ny
                ball2.x += overlap * nx
                ball2.y += overlap * ny



    # Check if all balls stopped
    all_stopped = True
    for ball in balls:
        if ball.alive and (abs(ball.velocity_x) > MIN_VELOCITY or abs(ball.velocity_y) > MIN_VELOCITY):
            all_stopped = False
            break
    if all_stopped:
        for ball in balls:
            if ball.is_cue_ball and not ball.alive:
                # Reset cue ball position and velocity
                ball.x = WIDTH // 4
                ball.y = HEIGHT // 2
                ball.velocity_x = 0
                ball.velocity_y = 0
                ball.alive = True
    return all_stopped

def draw_pockets(screen):
    for x, y in POCKETS:
        pygame.draw.circle(screen, BLACK, (x, y), POCKET_RADIUS)

def reset_simulation():
    global balls, simulation_started, prediction
    # Create new balls in triangle formation
    balls = create_triangle_formation(WIDTH * 3 // 4, HEIGHT // 2)
    simulation_started = False
    prediction = None

def predict():
    analyzer = dataflow_analysis.Analyzer(balls, initial_velocity, initial_angle, randomness)
    result = analyzer.predict()
    return result

# Initial values
initial_velocity = 5
initial_angle = 1.8  # Angle in degrees (0 = right, 90 = down)
randomness = 0.00  # Default randomness amount
simulation_started = False

# Create UI elements
# Place UI elements on the white panel
UI_PANEL_X = WIDTH + UI_PADDING
start_button = Button(UI_PANEL_X, UI_PADDING, 
                     BUTTON_WIDTH, BUTTON_HEIGHT, "Start Simulation", GREEN)
                     
reset_button = Button(UI_PANEL_X, UI_PADDING * 2 + BUTTON_HEIGHT, 
                     BUTTON_WIDTH, BUTTON_HEIGHT, "Reset", BLUE)

predict_button = Button(UI_PANEL_X, UI_PADDING * 3 + BUTTON_HEIGHT * 2, 
                     BUTTON_WIDTH, BUTTON_HEIGHT, "Predict", YELLOW)
                     
# ...existing code...
velocity_slider = Slider(
    UI_PANEL_X, UI_PADDING * 4 + BUTTON_HEIGHT * 3,
    SLIDER_WIDTH, SLIDER_HEIGHT, 1, 8, int(initial_velocity), "Velocity",
    discrete_values=list(np.array(range(1, 101)) / 10)
)

angle_slider = Slider(
    UI_PANEL_X, UI_PADDING * 5 + BUTTON_HEIGHT * 3 + SLIDER_HEIGHT,
    SLIDER_WIDTH, SLIDER_HEIGHT, 0, 360, initial_angle, "Angle"
)

randomness_slider = Slider(
    UI_PANEL_X, UI_PADDING * 6 + BUTTON_HEIGHT * 3 + SLIDER_HEIGHT * 2,
    SLIDER_WIDTH, SLIDER_HEIGHT, 0.01, 0.03, 0.01, "Randomness",
    discrete_values=list(np.array(range(1, 51)) / 1000)
)
# ...e

# Create initial balls
balls = create_triangle_formation(WIDTH * 3 // 4, HEIGHT // 2)

clock = pygame.time.Clock()

# Main game loop
count = 0
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                
                if reset_button.is_clicked(event.pos):
                    reset_simulation()

                if predict_button.is_clicked(event.pos):
                    prediction, history = predict()
                
                if start_button.is_clicked(event.pos) and not simulation_started:
                    simulation_started = True
                    # Set velocity for cue ball with randomness
                    for ball in balls:
                        if ball.is_cue_ball:
                            # Apply random increase to velocity based on randomness slider
                            random_factor = initial_velocity + random.uniform(0, randomness)
                            ball.velocity_x = random_factor * math.cos(math.radians(initial_angle))
                            ball.velocity_y = random_factor * math.sin(math.radians(initial_angle))

                # Check sliders
                if velocity_slider.is_over_handle(event.pos):
                    velocity_slider.active = True
                    
                if angle_slider.is_over_handle(event.pos):
                    angle_slider.active = True
                    
                if randomness_slider.is_over_handle(event.pos):
                    randomness_slider.active = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                velocity_slider.active = False
                angle_slider.active = False
                randomness_slider.active = False
                
        elif event.type == pygame.MOUSEMOTION:
            if velocity_slider.active:
                velocity_slider.update(event.pos)
                initial_velocity = velocity_slider.val
                
            if angle_slider.active:
                angle_slider.update(event.pos)
                initial_angle = angle_slider.val
                
            if randomness_slider.active:
                randomness_slider.update(event.pos)
                randomness = randomness_slider.val
    
    for i in range(2):
        if simulation_started:
            simulation_stopped = update_balls(balls)

            #compare with history:
            # if prediction is not None and history is not None:
            #     for i, ball in enumerate(balls):
            #         if ball.alive:
            #             # Compare current position with history
                        
            #             predicted_ball = history[count][i]
            #             if ball.x != predicted_ball.x:
            #                 print(count)
            #                 print(ball.x, predicted_ball.x)
            #                 print(ball.velocity_x, predicted_ball.velocity_x)
            #                 print('--------------------------')
            #             # assert(ball.y == predicted_ball.y)
            #             # assert(ball.velocity_x == predicted_ball.velocity_x)
            #             # assert(ball.velocity_y == predicted_ball.velocity_y)
            if simulation_stopped:
                simulation_started = False

            count += 1
    
    # Draw everything
    screen.fill(TABLE_COLOR)
    # Draw pockets
    draw_pockets(screen)
    
    # Draw balls
    for ball in balls:
        if ball.alive:
            ball.draw(screen)
    # Draw the white panel on the right
    pygame.draw.rect(screen, WHITE, (WIDTH, 0, PANEL_WIDTH, HEIGHT))
    # Draw UI elements
    start_button.draw(screen)
    reset_button.draw(screen)
    predict_button.draw(screen)
    velocity_slider.draw(screen)
    angle_slider.draw(screen)
    randomness_slider.draw(screen)
    if (prediction is not None):
        color = (0, 0, 255, 200)
        for ball in prediction:
            rect = pygame.Rect(
                int(ball.x.low), int(ball.y.low),
                max(5, int(ball.x.high - ball.x.low)),
                max(5, int(ball.y.high - ball.y.low))
            )
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, rect.topleft)
            color = ((color[0] + 50) % 256, color[1], color[2], color[3])

    # Update display
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()