# pygbag: umblock=0
import pygame
import random
import asyncio

# --- Constants ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 6
ENEMY_SPEED = 2

# --- Christmas Colors ---
NIGHT_BLUE = (10, 15, 50)      # Background
SNOW_WHITE = (245, 255, 250)   # Snow & Platforms
SANTA_RED = (220, 20, 60)      # Player & Candy Stripes
GRINCH_GREEN = (50, 205, 50)   # Enemies
GOLD = (255, 215, 0)           # Stars/Ui

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Create a "Santa" Block
        self.image = pygame.Surface((30, 40), pygame.SRCALPHA)
        # Red Body
        pygame.draw.rect(self.image, SANTA_RED, (0, 10, 30, 30))
        # White Fur Trim (Hat Rim)
        pygame.draw.rect(self.image, SNOW_WHITE, (0, 0, 30, 10))
        # Little Pom-Pom on top
        pygame.draw.circle(self.image, SNOW_WHITE, (15, 0), 5)
        
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT - 150))
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
        self.velocity_y = 0

    def move_left(self):
        self.pos_x -= PLAYER_SPEED
        
    def move_right(self):
        self.pos_x += PLAYER_SPEED

    def update(self):
        self.velocity_y += GRAVITY
        self.pos_y += self.velocity_y
        self.rect.y = round(self.pos_y)
        
        # Screen Wrapping
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
        # Snowball Image
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, SNOW_WHITE, (6, 6), 6)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 15))
        self.image.fill(SNOW_WHITE)
        # Add "Candy Cane" Stripes
        for i in range(0, 60, 15):
            pygame.draw.line(self.image, SANTA_RED, (i, 0), (i+5, 15), 5)
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.exact_y = float(y)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40)) 
        self.image.fill(GRINCH_GREEN)
        # Angry Eyes
        pygame.draw.line(self.image, (0,50,0), (5, 10), (15, 20), 3)
        pygame.draw.line(self.image, (0,50,0), (35, 10), (25, 20), 3)
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.exact_y = float(y)
        self.speed = ENEMY_SPEED
        self.direction = 1 

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right > WIDTH or self.rect.left < 0:
            self.direction *= -1

class Star(pygame.sprite.Sprite):
    """ Background falling snow/stars """
    def __init__(self):
        super().__init__()
        size = random.randint(2, 4)
        self.image = pygame.Surface((size, size))
        self.image.fill(SNOW_WHITE)
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        self.speed = random.uniform(0.5, 1.5)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.bottom = 0
            self.rect.x = random.randint(0, WIDTH)

# --- Main Game Loop ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Create Groups
    player = Player()
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    background_particles = pygame.sprite.Group()

    # Create Background Snow
    for _ in range(50):
        background_particles.add(Star())

    # Create Initial Platforms
    for i in range(6):
        p = Platform(random.randint(0, WIDTH-60), i * 100)
        platforms.add(p)

    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not game_over:
                # SHOOT (Space or Touch Center)
                shoot = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    shoot = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if WIDTH * 0.25 < mx < WIDTH * 0.75:
                        shoot = True
                
                if shoot:
                    bullets.add(Bullet(player.rect.centerx, player.rect.top))

            # RESTART (Touch anywhere on Game Over)
            if game_over and event.type == pygame.MOUSEBUTTONDOWN:
                 player.rect.center = (WIDTH//2, HEIGHT - 100)
                 player.pos_x = player.rect.x
                 player.pos_y = player.rect.y
                 player.velocity_y = 0
                 platforms.empty()
                 enemies.empty()
                 bullets.empty()
                 for i in range(6):
                    platforms.add(Platform(random.randint(0, WIDTH-60), i * 100))
                 game_over = False

        if not game_over:
            # MOVEMENT
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: player.move_left()
            if keys[pygame.K_RIGHT]: player.move_right()

            if pygame.mouse.get_pressed()[0]: 
                mx, my = pygame.mouse.get_pos()
                if mx < WIDTH * 0.25: player.move_left()
                elif mx > WIDTH * 0.75: player.move_right()

            # UPDATES
            player.update()
            enemies.update()
            bullets.update()
            background_particles.update()

            # COLLISIONS
            pygame.sprite.groupcollide(enemies, bullets, True, True) # Kill enemy+snowball

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
                else:
                    game_over = True

            # SCROLLING
            if player.rect.top < HEIGHT / 3:
                scroll = abs(player.velocity_y)
                player.pos_y += scroll
                player.rect.y = round(player.pos_y)
                
                for sprite in platforms:
                    sprite.exact_y += scroll
                    sprite.rect.y = round(sprite.exact_y)
                    if sprite.rect.top >= HEIGHT:
                        sprite.kill()
                        platforms.add(Platform(random.randint(0, WIDTH-60), random.randint(-50, -10)))
                
                for sprite in enemies:
                    sprite.exact_y += scroll
                    sprite.rect.y = round(sprite.exact_y)
                    if sprite.rect.top >= HEIGHT: sprite.kill()
                
                for sprite in bullets:
                    sprite.rect.y += int(scroll)

                # Spawn Grinch (2% chance)
                if random.randint(0, 100) < 2: 
                    enemies.add(Enemy(random.randint(0, WIDTH-40), -50))

            if player.rect.top > HEIGHT:
                game_over = True

        # DRAWING
        screen.fill(NIGHT_BLUE)
        background_particles.draw(screen) # Snow in background
        platforms.draw(screen)
        enemies.draw(screen)
        bullets.draw(screen)
        screen.blit(player.image, player.rect)

        # Touch Controls Overlay
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 10), (0, 0, WIDTH*0.25, HEIGHT))
        pygame.draw.rect(s, (255, 255, 255, 10), (WIDTH*0.75, 0, WIDTH*0.25, HEIGHT))
        screen.blit(s, (0,0))

        if game_over:
            font = pygame.font.Font(None, 40)
            t1 = font.render("MERRY CHRISTMAS!", True, GOLD)
            t2 = font.render("Tap to Try Again", True, SNOW_WHITE)
            screen.blit(t1, (WIDTH//2 - 130, HEIGHT//2 - 20))
            screen.blit(t2, (WIDTH//2 - 110, HEIGHT//2 + 20))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())