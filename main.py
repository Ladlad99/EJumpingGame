# pygbag: umblock=0
import pygame
import random
import asyncio
import json
import os

# --- Constants ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 6
ENEMY_SPEED = 2
MAX_JUMP_GAP = 130 

# --- Colors ---
NIGHT_BLUE = (10, 15, 50)      
SNOW_WHITE = (245, 255, 250)   
SANTA_RED = (220, 20, 60)      
GRINCH_GREEN = (50, 205, 50)   
GOLD = (255, 215, 0)           
BUTTON_COLOR = (200, 50, 50) 

# --- File Storage ---
SAVE_FILE = "ejump_save.json"

# --- Game States ---
STATE_MENU = "menu"
STATE_READY = "ready"
STATE_GAME = "game"

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Optimized: No Alpha channel, using ColorKey for speed
        self.image = pygame.Surface((30, 40)) 
        self.image.fill(NIGHT_BLUE) 
        self.image.set_colorkey(NIGHT_BLUE)
        
        pygame.draw.rect(self.image, SANTA_RED, (0, 10, 30, 30)) 
        pygame.draw.rect(self.image, SNOW_WHITE, (0, 0, 30, 10)) 
        pygame.draw.circle(self.image, SNOW_WHITE, (15, 0), 5)   
        
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT - 150))
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.velocity_y = 0

    def move_left(self): self.pos_x -= PLAYER_SPEED
    def move_right(self): self.pos_x += PLAYER_SPEED

    def update(self):
        self.velocity_y += GRAVITY
        self.pos_y += self.velocity_y
        self.rect.y = round(self.pos_y)
        
        if self.rect.right < 0: 
            self.pos_x = WIDTH
            self.rect.x = WIDTH
        if self.rect.left > WIDTH: 
            self.pos_x = 0
            self.rect.x = 0
            
        self.rect.x = round(self.pos_x)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(SNOW_WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0: self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 15))
        self.image.fill(SNOW_WHITE)
        # Optimized: Simple lines
        pygame.draw.line(self.image, SANTA_RED, (15, 0), (20, 15), 4)
        pygame.draw.line(self.image, SANTA_RED, (30, 0), (35, 15), 4)
        pygame.draw.line(self.image, SANTA_RED, (45, 0), (50, 15), 4)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.exact_y = float(y)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40)) 
        self.image.fill(GRINCH_GREEN)
        pygame.draw.rect(self.image, (0,50,0), (5, 10, 10, 5))
        pygame.draw.rect(self.image, (0,50,0), (25, 10, 10, 5))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.exact_y = float(y)
        self.speed = ENEMY_SPEED
        self.direction = 1 

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right > WIDTH or self.rect.left < 0:
            self.direction *= -1

# --- Helper Functions ---
def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_data(data):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def draw_text_centered(screen, text, font, color, y_pos):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH//2, y_pos))
    screen.blit(surf, rect)

# --- Main App ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ejump")
    
    font_lg = pygame.font.Font(None, 50)
    font_md = pygame.font.Font(None, 36)
    
    # Pre-Render Shoot Button
    shoot_btn_surf = pygame.Surface((80, 80))
    shoot_btn_surf.fill(NIGHT_BLUE)
    shoot_btn_surf.set_colorkey(NIGHT_BLUE)
    pygame.draw.circle(shoot_btn_surf, BUTTON_COLOR, (40, 40), 35)
    pygame.draw.circle(shoot_btn_surf, SNOW_WHITE, (40, 40), 35, 3)
    pygame.draw.line(shoot_btn_surf, SNOW_WHITE, (30, 40), (50, 40), 2)
    pygame.draw.line(shoot_btn_surf, SNOW_WHITE, (40, 30), (40, 50), 2)
    
    shoot_btn_rect = pygame.Rect(WIDTH - 90, HEIGHT - 100, 80, 80)
    shoot_btn_draw_pos = (WIDTH - 90, HEIGHT - 100)

    player = Player()
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    
    # STARS ARE GONE. NO MORE STARS.

    user_data = load_data()
    high_scores = user_data.get("scores", []) if user_data else []
    
    current_state = STATE_MENU
    current_score = 0
    game_over = False
    running = True

    def reset_game():
        nonlocal current_score, game_over
        player.rect.center = (WIDTH//2, HEIGHT - 150)
        player.pos_x, player.pos_y = player.rect.x, player.rect.y
        player.velocity_y = 0
        platforms.empty()
        enemies.empty()
        bullets.empty()
        current_score = 0
        game_over = False
        
        platforms.add(Platform(WIDTH//2 - 30, HEIGHT - 80))
        last_y = HEIGHT - 80
        for i in range(5):
            gap = random.randint(60, MAX_JUMP_GAP) 
            new_y = last_y - gap
            platforms.add(Platform(random.randint(0, WIDTH-60), new_y))
            last_y = new_y

    def spawn_new_platform():
        min_y = HEIGHT
        for p in platforms:
            if p.rect.y < min_y: min_y = p.rect.y
        gap = random.randint(60, MAX_JUMP_GAP)
        new_y = min_y - gap
        platforms.add(Platform(random.randint(0, WIDTH-60), new_y))

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if current_state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    reset_game()
                    current_state = STATE_READY

            elif current_state == STATE_READY:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    current_state = STATE_GAME

            elif current_state == STATE_GAME:
                if not game_over:
                    shoot = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: shoot = True
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if shoot_btn_rect.collidepoint(event.pos): shoot = True
                    if shoot:
                        bullets.add(Bullet(player.rect.centerx, player.rect.top))
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        reset_game()
                        current_state = STATE_READY

        # Game Logic
        if current_state == STATE_GAME and not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: player.move_left()
            if keys[pygame.K_RIGHT]: player.move_right()
            
            if pygame.mouse.get_pressed()[0]: 
                mx, my = pygame.mouse.get_pos()
                if not shoot_btn_rect.collidepoint((mx, my)):
                    if mx < WIDTH * 0.5: player.move_left()
                    else: player.move_right()

            player.update()
            enemies.update()
            bullets.update()
            
            pygame.sprite.groupcollide(enemies, bullets, True, True)

            if player.velocity_y > 0:
                hits = pygame.sprite.spritecollide(player, platforms, False)
                if hits:
                    player.pos_y = hits[0].rect.top - player.rect.height
                    player.rect.y = player.pos_y
                    player.velocity_y = JUMP_STRENGTH

            hit_enemy = pygame.sprite.spritecollide(player, enemies, False)
            if hit_enemy:
                if player.velocity_y > 0 and player.rect.bottom < hit_enemy[0].rect.centery:
                    player.velocity_y = JUMP_STRENGTH
                    hit_enemy[0].kill()
                    current_score += 500
                else:
                    game_over = True

            if player.rect.top < HEIGHT / 3:
                scroll = abs(player.velocity_y)
                player.pos_y += scroll
                player.rect.y = round(player.pos_y)
                current_score += int(scroll)
                
                for sprite in platforms:
                    sprite.exact_y += scroll
                    sprite.rect.y = round(sprite.exact_y)
                    if sprite.rect.top >= HEIGHT:
                        sprite.kill()
                        spawn_new_platform()
                
                for sprite in enemies:
                    sprite.exact_y += scroll
                    sprite.rect.y = round(sprite.exact_y)
                    if sprite.rect.top >= HEIGHT: sprite.kill()
                
                for sprite in bullets:
                    sprite.rect.y += int(scroll)
                    
                if random.randint(0, 100) < 2: 
                    enemies.add(Enemy(random.randint(0, WIDTH-40), -50))

            if player.rect.top > HEIGHT:
                game_over = True
                high_scores.append(current_score)
                high_scores.sort(reverse=True)
                high_scores = high_scores[:5]
                save_data({"scores": high_scores})

        # --- DRAWING ---
        screen.fill(NIGHT_BLUE)
        # NO STARS DRAWN HERE.
        
        if current_state == STATE_MENU:
            draw_text_centered(screen, "EJUMP", font_lg, GOLD, 150)
            draw_text_centered(screen, "Tap to Play", font_lg, SNOW_WHITE, 300)
            player.rect.center = (WIDTH//2, 400)
            screen.blit(player.image, player.rect)

        elif current_state == STATE_READY:
            platforms.draw(screen)
            enemies.draw(screen)
            screen.blit(player.image, player.rect)
            draw_text_centered(screen, "Tap to Jump!", font_lg, GOLD, HEIGHT//2)

        elif current_state == STATE_GAME:
            platforms.draw(screen)
            enemies.draw(screen)
            bullets.draw(screen)
            screen.blit(player.image, player.rect)
            
            score_surf = font_md.render(f"{current_score}", True, GOLD)
            screen.blit(score_surf, (10, 10))
            
            # Draw Button
            screen.blit(shoot_btn_surf, shoot_btn_draw_pos)

            if game_over:
                draw_text_centered(screen, "GAME OVER", font_lg, GOLD, 200)
                draw_text_centered(screen, f"Score: {current_score}", font_md, SNOW_WHITE, 260)
                draw_text_centered(screen, "Tap to Try Again", font_md, SNOW_WHITE, 350)
                
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
