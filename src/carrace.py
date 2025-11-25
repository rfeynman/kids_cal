import pygame
import time
import random
import math

# --- Initialization ---
pygame.init()

# --- Constants & Configuration ---
SCREEN_WIDTH = 1000 # Widened slightly for 8 cars/6 lanes
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)
RED = (220, 20, 60)
BLUE = (0, 100, 255)
GREEN = (50, 205, 50)
YELLOW = (255, 215, 0)
CYAN = (0, 255, 255)
PURPLE = (147, 112, 219)
ORANGE = (255, 140, 0)
PINK = (255, 105, 180)
SILVER = (192, 192, 192)

# Road Config
NUM_LANES = 6
LANE_WIDTH = 100
ROAD_WIDTH = NUM_LANES * LANE_WIDTH
ROAD_X_OFFSET = (SCREEN_WIDTH - ROAD_WIDTH) // 2

# Physics Config
CAR_MASS = 100
STONE_MASS = 20
FRICTION = 0.05
MAX_SPEED = 220
MIN_SPEED = 0
INITIAL_AMMO = 200
AMMO_PICKUP_AMOUNT = 5

# Game Config
LAPS_TO_WIN = 3
TRACK_LENGTH = 6000 

# --- Classes ---

class StonePickup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Draw a diamond shape
        pygame.draw.polygon(self.image, CYAN, [(10, 0), (20, 10), (10, 20), (0, 10)])
        pygame.draw.polygon(self.image, WHITE, [(10, 5), (15, 10), (10, 15), (5, 10)]) # Shine
        self.rect = self.image.get_rect(center=(x, y))
        self.real_y = float(y) # Track absolute world position

    def update(self, player_distance_delta, road_scroll_speed):
        # Move relative to screen based on player speed (pseudo-3D effect)
        # Objects on road move down if player moves forward
        self.rect.y += road_scroll_speed 
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Stone(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, owner_id):
        super().__init__()
        self.image = pygame.Surface((12, 12))
        self.image.fill(SILVER)
        pygame.draw.rect(self.image, BLACK, (0,0,12,12), 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        self.owner_id = owner_id

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()

class Car(pygame.sprite.Sprite):
    def __init__(self, lane_index, color, is_player=False, car_id=0, skill_level=0.5):
        super().__init__()
        self.color = color
        self.width = 50
        self.height = 90
        self.image = self.draw_car_surface()
        
        self.rect = self.image.get_rect()
        self.lane = lane_index
        self.target_x = ROAD_X_OFFSET + (self.lane * LANE_WIDTH) + (LANE_WIDTH // 2)
        self.rect.centerx = self.target_x
        self.rect.centery = SCREEN_HEIGHT - 150 if is_player else SCREEN_HEIGHT + 100
        
        self.is_player = is_player
        self.id = car_id
        self.skill_level = skill_level # 0.0 to 1.0 (1.0 is best)
        
        # Physics State
        self.speed = 0 
        self.distance = 0
        self.ammo = INITIAL_AMMO
        
        # Charging Mechanics (Player)
        self.charge_start_time = 0
        self.charging_key = None
        
        # AI Logic
        self.next_action_time = time.time() + random.uniform(0.5, 2.0)
        self.cooldown = 0
        self.collision_timer = 0 # Cooldown to prevent rapid-fire collision draining

    def draw_car_surface(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Main Body with rounded corners
        rect_body = (0, 5, self.width, self.height - 10)
        pygame.draw.rect(surf, self.color, rect_body, border_radius=10)
        
        # "Shine" / Highlight (Lighter strip on the left)
        shine_color = (min(self.color[0]+50, 255), min(self.color[1]+50, 255), min(self.color[2]+50, 255))
        pygame.draw.rect(surf, shine_color, (5, 10, 10, self.height - 20), border_radius=5)
        
        # Windshield
        pygame.draw.rect(surf, (20, 20, 40), (5, 15, self.width-10, 15), border_radius=3)
        # Rear window
        pygame.draw.rect(surf, (20, 20, 40), (5, self.height-25, self.width-10, 10), border_radius=3)
        
        # Wheels
        wheel_color = (10, 10, 10)
        wheel_h = 18
        wheel_w = 8
        # FL
        pygame.draw.rect(surf, wheel_color, (0, 10, wheel_w, wheel_h))
        # FR
        pygame.draw.rect(surf, wheel_color, (self.width - wheel_w, 10, wheel_w, wheel_h))
        # RL
        pygame.draw.rect(surf, wheel_color, (0, self.height - 28, wheel_w, wheel_h))
        # RR
        pygame.draw.rect(surf, wheel_color, (self.width - wheel_w, self.height - 28, wheel_w, wheel_h))
        
        # Stripe
        pygame.draw.rect(surf, BLACK, (self.width//2 - 2, 0, 4, self.height))
        
        return surf

    def start_charge(self, key):
        if self.charging_key is None and self.ammo > 0:
            self.charging_key = key
            self.charge_start_time = time.time()

    def release_charge(self, key, all_stones_group):
        if self.charging_key == key:
            duration = time.time() - self.charge_start_time
            self.charging_key = None
            if self.ammo > 0:
                self.throw_stone(key, duration, all_stones_group)

    def throw_stone(self, key, duration, all_stones_group):
        if self.ammo <= 0: return
        
        self.ammo -= 1
        duration = min(duration, 2.0)
        velocity_magnitude = duration * 20 
        if velocity_magnitude < 5: velocity_magnitude = 5
        
        stone_vx = 0
        stone_vy = 0
        dv_car = (STONE_MASS * velocity_magnitude) / CAR_MASS
        
        # Logic for Throwing
        if key == pygame.K_UP: # Accelerate -> Throw Back
            stone_vy = 10 + velocity_magnitude
            self.speed += dv_car * 5
        elif key == pygame.K_DOWN: # Brake -> Throw Forward
            stone_vy = -(10 + velocity_magnitude)
            self.speed -= dv_car * 5
            if self.speed < 0: self.speed = 0
        elif key == pygame.K_LEFT: # Push Left -> Throw Right
            stone_vx = 10 + velocity_magnitude
            lanes = 2 if duration > 0.4 else 1
            self.change_lane(-lanes)
        elif key == pygame.K_RIGHT: # Push Right -> Throw Left
            stone_vx = -(10 + velocity_magnitude)
            lanes = 2 if duration > 0.4 else 1
            self.change_lane(lanes)

        # Spawn Stone
        spawn_x, spawn_y = self.rect.center
        if stone_vx > 0: spawn_x = self.rect.right
        elif stone_vx < 0: spawn_x = self.rect.left
        if stone_vy > 0: spawn_y = self.rect.bottom
        elif stone_vy < 0: spawn_y = self.rect.top
        
        stone = Stone(spawn_x, spawn_y, stone_vx, stone_vy, self.id)
        all_stones_group.add(stone)

    def change_lane(self, direction):
        new_lane = self.lane + direction
        if new_lane < 0: new_lane = 0
        if new_lane >= NUM_LANES: new_lane = NUM_LANES - 1
        self.lane = new_lane
        self.target_x = ROAD_X_OFFSET + (self.lane * LANE_WIDTH) + (LANE_WIDTH // 2)

    def hit_by_stone(self, stone):
        # Impact Logic
        if abs(stone.vx) > abs(stone.vy):
            # Horizontal Hit
            if stone.vx > 0: # From left
                if self.lane < NUM_LANES - 1: self.change_lane(1)
                else: self.speed = 10 # Wall hit penalty
            else: # From right
                if self.lane > 0: self.change_lane(-1)
                else: self.speed = 10
        else:
            # Vertical Hit
            if stone.vy > 0: # From behind
                self.speed += 5
            else: # From front
                self.speed -= 10
                if self.speed < 10: self.speed = 10

    def update_ai(self, stones_group, all_cars):
        if self.ammo <= 0: return # AI out of ammo

        curr_time = time.time()
        if curr_time < self.next_action_time: return
        
        # AI Strategy based on skill
        # Higher skill = faster reaction
        reaction_speed = max(0.5, 2.0 - self.skill_level * 1.5) 
        aggression = self.skill_level # Chance to attack
        
        # 1. Analyze surroundings
        car_ahead = None
        car_behind = None
        car_left = None
        car_right = None
        
        for car in all_cars:
            if car.id == self.id: continue
            
            # Check lane
            lane_diff = car.lane - self.lane
            dist_diff = car.distance - self.distance
            
            # Only care about cars nearby
            if abs(dist_diff) > 400: continue

            if lane_diff == 0:
                if 0 < dist_diff < 400: car_ahead = car
                if -400 < dist_diff < 0: car_behind = car
            elif lane_diff == -1 and abs(dist_diff) < 150:
                car_left = car
            elif lane_diff == 1 and abs(dist_diff) < 150:
                car_right = car

        action_taken = False
        
        # Decision Matrix - AGGRESSIVE MODE
        
        # 1. Attack Car Behind (Priority: High)
        # Strategy: Accelerate (Up Key). This throws stone BACKWARDS (down screen), hitting the car trailing us.
        # Benefit: We go faster, they get hit/slowed.
        if car_behind and random.random() < aggression + 0.3:
            self.throw_stone(pygame.K_UP, 0.6, stones_group)
            action_taken = True

        # 2. Attack/Push Car to the Side
        # Strategy: If car is on Left, we want to hit them. To hit LEFT, we must throw LEFT.
        # To throw LEFT, we must press RIGHT (Newton's 3rd Law: Move Right -> Throw Left).
        elif car_left and random.random() < aggression + 0.2:
            # Enemy on Left. Throw Left (Press Right).
            self.throw_stone(pygame.K_RIGHT, 0.5, stones_group)
            action_taken = True
            
        elif car_right and random.random() < aggression + 0.2:
            # Enemy on Right. Throw Right (Press Left).
            self.throw_stone(pygame.K_LEFT, 0.5, stones_group)
            action_taken = True

        # 3. Attack Car Ahead (Desperation/Spite)
        # Strategy: Brake (Down Key). This throws stone FORWARDS, hitting car ahead.
        # Cost: We slow down. Only do this if we are fast enough or very aggressive.
        elif car_ahead and random.random() < aggression and self.speed > 100:
            self.throw_stone(pygame.K_DOWN, 0.4, stones_group)
            action_taken = True
            
        # 4. Normal Racing (Accelerate if clear)
        elif not action_taken and self.speed < MAX_SPEED * (0.8 + 0.2*self.skill_level):
            # Random lane changes to keep it dynamic
            if random.random() < 0.05:
                move = random.choice([-1, 1])
                key = pygame.K_LEFT if move == -1 else pygame.K_RIGHT
                self.throw_stone(key, 0.2, stones_group)
            else:
                self.throw_stone(pygame.K_UP, 0.5, stones_group)
            action_taken = True
             
        # Reset timer
        self.next_action_time = curr_time + random.uniform(reaction_speed * 0.5, reaction_speed)

    def update(self, dt, player_speed):
        # Cooldown timer
        if self.collision_timer > 0:
            self.collision_timer -= dt

        # Smooth Lane Animation
        if self.rect.centerx != self.target_x:
            diff = self.target_x - self.rect.centerx
            move = diff * 0.1
            if abs(move) < 1: self.rect.centerx = self.target_x
            else: self.rect.centerx += move

        # Physics update
        if self.is_player:
            if self.speed > 0: self.speed -= FRICTION
            self.distance += self.speed * dt
        else:
            self.distance += self.speed * dt
            # Render relative to player
            relative_dist = self.distance - player_car.distance
            self.rect.centery = (SCREEN_HEIGHT - 150) - relative_dist

# --- Functions ---

def check_car_collisions(cars):
    # Convert sprite group to list for indexing
    car_list = list(cars)
    for i in range(len(car_list)):
        for j in range(i + 1, len(car_list)):
            c1 = car_list[i]
            c2 = car_list[j]
            
            # Simple rectangle overlap for collision
            if c1.rect.colliderect(c2.rect):
                
                # Prevent continuous collision draining speed every frame
                if c1.collision_timer > 0 or c2.collision_timer > 0:
                    continue

                # Determine Collision Type
                
                # 1. Side-by-side (roughly same Y)
                # Overlap width > Overlap height implies vertical collision usually, 
                # but since lanes lock X, we check Y distance.
                y_dist = abs(c1.rect.centery - c2.rect.centery)
                
                if y_dist < 50: # Side Hit
                    # Calculate average speed
                    avg_speed = (c1.speed + c2.speed) / 2
                    # Drops to half of average speed
                    new_speed = avg_speed * 0.5
                    
                    c1.speed = new_speed
                    c2.speed = new_speed
                    
                    # Add cooldown so they don't collide again immediately
                    c1.collision_timer = 1.0
                    c2.collision_timer = 1.0
                    
                    # Push them apart visually if possible (animation only)
                    if c1.rect.centerx < c2.rect.centerx:
                        c1.rect.x -= 5; c2.rect.x += 5
                    else:
                        c1.rect.x += 5; c2.rect.x -= 5
                        
                else: # Front/Back Hit
                    # Identify Front and Back car
                    if c1.rect.centery < c2.rect.centery:
                        front, back = c1, c2
                    else:
                        front, back = c2, c1
                        
                    # Momentum Conservation Idea:
                    # Front car gains speed, Back car loses speed.
                    # Total momentum P = m*v1 + m*v2
                    # Let's transfer 30% of back car's speed to front car
                    
                    transfer_amount = back.speed * 0.4
                    front.speed += transfer_amount
                    back.speed -= transfer_amount
                    
                    if back.speed < 0: back.speed = 0
                    
                    # Cooldown
                    c1.collision_timer = 0.5
                    c2.collision_timer = 0.5

                    # Separate them to prevent sticking
                    if back.rect.top < front.rect.bottom:
                        back.rect.top = front.rect.bottom + 5

# --- Main Game Setup ---

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Momentum Racer - 8 Car Rumble")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Verdana", 18, bold=True)
big_font = pygame.font.SysFont("Verdana", 48, bold=True)

all_sprites = pygame.sprite.Group()
stones_group = pygame.sprite.Group()
cars_group = pygame.sprite.Group()
pickups_group = pygame.sprite.Group()

player_car = None

def reset_game():
    global player_car, game_over, winner_text
    
    all_sprites.empty()
    stones_group.empty()
    cars_group.empty()
    pickups_group.empty()

    # 1. Player
    player_car = Car(2, RED, is_player=True, car_id=1, skill_level=1.0)
    all_sprites.add(player_car)
    cars_group.add(player_car)

    # 2. AI Cars (7 opponents)
    ai_configs = [
        (BLUE, 0.3), (GREEN, 0.4), (YELLOW, 0.5), 
        (PURPLE, 0.7), (ORANGE, 0.6), (PINK, 0.4), (CYAN, 0.8)
    ]

    for i, (color, skill) in enumerate(ai_configs):
        lane = (i % NUM_LANES)
        ai = Car(lane, color, is_player=False, car_id=i+2, skill_level=skill)
        ai.speed = 100 + (i * 5)
        # Start them slightly staggered distance-wise
        ai.distance = i * 50 
        all_sprites.add(ai)
        cars_group.add(ai)
    
    game_over = False
    winner_text = ""

# Initial Start
reset_game()

running = True

def draw_road(surface, offset_y):
    pygame.draw.rect(surface, DARK_GRAY, (ROAD_X_OFFSET, 0, ROAD_WIDTH, SCREEN_HEIGHT))
    
    for i in range(NUM_LANES + 1):
        x = ROAD_X_OFFSET + (i * LANE_WIDTH)
        color = WHITE if i == 0 or i == NUM_LANES else (150, 150, 150)
        width = 6 if i == 0 or i == NUM_LANES else 2
        
        if width == 2: # Dashed lines
            for y in range(-100, SCREEN_HEIGHT + 100, 60):
                draw_y = (y + int(offset_y)) % (SCREEN_HEIGHT + 100) - 50
                pygame.draw.line(surface, color, (x, draw_y), (x, draw_y + 30), width)
        else: # Solid borders
            pygame.draw.line(surface, color, (x, 0), (x, SCREEN_HEIGHT), width)

def draw_ui(surface, player):
    # Info Box
    pygame.draw.rect(surface, BLACK, (0, 0, 180, 130))
    pygame.draw.rect(surface, WHITE, (0, 0, 180, 130), 2)
    
    spd = font.render(f"SPEED: {int(player.speed)}", True, CYAN if player.speed > 150 else WHITE)
    surface.blit(spd, (10, 10))
    
    lap = int(player.distance // TRACK_LENGTH) + 1
    lp_txt = font.render(f"LAP: {lap}/{LAPS_TO_WIN}", True, WHITE)
    surface.blit(lp_txt, (10, 40))
    
    ammo_color = GREEN if player.ammo > 50 else RED
    am_txt = font.render(f"STONES: {player.ammo}", True, ammo_color)
    surface.blit(am_txt, (10, 70))
    
    # Rank
    rank = 1
    for c in cars_group:
        if c.id != player.id and c.distance > player.distance:
            rank += 1
    rnk_txt = font.render(f"POS: {rank}/8", True, YELLOW)
    surface.blit(rnk_txt, (10, 100))

    # Charge Bar
    if player.charging_key is not None:
        duration = time.time() - player.charge_start_time
        charge_pct = min(duration / 2.0, 1.0)
        
        bar_w = 100
        bar_h = 10
        bx = player.rect.centerx - bar_w//2
        by = player.rect.bottom + 10
        
        color = YELLOW if duration < 0.4 else RED
        pygame.draw.rect(surface, WHITE, (bx, by, bar_w, bar_h), 1)
        pygame.draw.rect(surface, color, (bx+1, by+1, (bar_w-2)*charge_pct, bar_h-2))

# --- Main Loop ---
while running:
    dt = clock.tick(FPS) / 1000.0

    # 1. Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Restart Handler
        if game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()

        if not game_over:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    player_car.start_charge(event.key)
            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                    player_car.release_charge(event.key, stones_group)

    # 2. Logic
    if not game_over:
        # Spawn Pickups randomly
        if random.random() < 0.02: # 2% chance per frame
            lane = random.randint(0, NUM_LANES-1)
            px = ROAD_X_OFFSET + lane*LANE_WIDTH + LANE_WIDTH//2
            # Spawn ahead of player
            py = -50 
            pickup = StonePickup(px, py)
            all_sprites.add(pickup)
            pickups_group.add(pickup)

        # Update Cars & AI
        for car in cars_group:
            if not car.is_player:
                car.update_ai(stones_group, cars_group)
        
        player_car.update(dt, player_car.speed)
        for car in cars_group:
            if not car.is_player:
                car.update(dt, player_car.speed)
        
        stones_group.update()
        
        # Pickups Movement (move down screen as player drives forward)
        # Speed of pickup relative to camera = Player Speed (pixels/sec) converted to frame movement
        # If player stops, pickups stay (relative to road). 
        # Actually pickups are fixed on road. Screen moves at player speed.
        # So pickups move DOWN at player.speed * dt
        
        # Note: In this engine, objects have screen coordinates. 
        # We simulate road scrolling by moving non-player objects.
        pickup_scroll = player_car.speed * dt * 10 # Scaling factor for visual speed
        # Actually, let's just say pickups move down at speed proportional to player speed
        for p in pickups_group:
            p.rect.y += player_car.speed * dt
            if p.rect.y > SCREEN_HEIGHT: p.kill()

        # Collisions: Cars vs Pickups
        hits = pygame.sprite.groupcollide(cars_group, pickups_group, False, True)
        for car, p_list in hits.items():
            car.ammo += AMMO_PICKUP_AMOUNT * len(p_list)

        # Collisions: Stones vs Cars
        hits = pygame.sprite.groupcollide(cars_group, stones_group, False, True)
        for car, stones in hits.items():
            for stone in stones:
                if stone.owner_id != car.id:
                    car.hit_by_stone(stone)
        
        # Collisions: Cars vs Cars
        check_car_collisions(cars_group)

        # Win Check
        if player_car.distance >= TRACK_LENGTH * LAPS_TO_WIN:
            game_over = True
            winner_text = "FINISH!"
        
        # Check if AI won
        for car in cars_group:
             if car.distance >= TRACK_LENGTH * LAPS_TO_WIN:
                 # If AI crosses line, race continues until player finishes or gives up?
                 # Usually race ends when player finishes, but we can just mark them finished.
                 pass

    # 3. Drawing
    screen.fill(BLACK)
    draw_road(screen, player_car.distance)
    
    # Draw pickups underneath cars
    pickups_group.draw(screen)
    
    # Draw Shadows
    for car in cars_group:
        pygame.draw.ellipse(screen, (10,10,10), (car.rect.x+5, car.rect.bottom-5, 40, 10))

    all_sprites.draw(screen)
    stones_group.draw(screen)
    
    draw_ui(screen, player_car)
    
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0,0))
        txt = big_font.render(winner_text, True, WHITE)
        screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        
        restart_txt = font.render("Press 'R' to Restart", True, WHITE)
        screen.blit(restart_txt, restart_txt.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60)))

    pygame.display.flip()

pygame.quit()