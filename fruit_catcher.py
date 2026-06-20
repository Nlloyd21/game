from ursina import *
import random

# 1. Boot up the app explicitly disabling complex shader modules
app = Ursina(shader=None)

# Game Windows Setup
window.title = "3D Catch Catcher"
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Game Progression States
score = 0
lives = 3
game_over = False

# 2. Re-establish flat solid background (avoids Skybox rendering failure)
window.color = color.light_gray

# 3. Simplify Entities to use basic flat geometry configurations without complex lighting mapping
ground = Entity(model='cube', scale=(20, 1, 5), y=-4, color=color.olive)
basket = Entity(model='cube', scale=(3, 0.5, 1.5), y=-3, color=color.brown)

# UI Layer text strings
score_text = Text(text=f'Score: {score}', position=(-0.8, 0.45), scale=2, color=color.black)
lives_text = Text(text=f'Lives: {lives}', position=(0.6, 0.45), scale=2, color=color.red)
game_over_text = Text(text='', position=(-0.2, 0), scale=4, color=color.red)

falling_items = []

def spawn_item():
    if game_over:
        return
        
    is_obstacle = random.random() < 0.2
    
    # Removed lighting/texture processing attachments to force universal rendering pipeline stability
    if is_obstacle:
        item = Entity(
            model='cube', 
            color=color.red, 
            scale=0.8, 
            position=(random.uniform(-7, 7), 6, 0)
        )
        item.is_obstacle = True
    else:
        item = Entity(
            model='sphere', 
            color=color.yellow, 
            scale=0.8, 
            position=(random.uniform(-7, 7), 6, 0)
        )
        item.is_obstacle = False
        
    item.speed = random.uniform(3, 6)
    falling_items.append(item)
    
    invoke(spawn_item, delay=1.0)

# Fire up spawning threads
spawn_item()

def update():
    global score, lives, game_over
    
    if game_over:
        if held_keys['r']:
            score = 0
            lives = 3
            game_over = False
            game_over_text.text = ''
            score_text.text = f'Score: {score}'
            lives_text.text = f'Lives: {lives}'
            for item in falling_items:
                destroy(item)
            falling_items.clear()
        return

    # User inputs vectors
    if held_keys['left arrow'] or held_keys['a']:
        basket.x -= 8 * time.dt
    if held_keys['right arrow'] or held_keys['d']:
        basket.x += 8 * time.dt
        
    basket.x = clamp(basket.x, -8.5, 8.5)

    for item in falling_items[:]:
        item.y -= item.speed * time.dt
        
        # Core distance validation formula
        if abs(item.x - basket.x) < 1.8 and abs(item.y - basket.y) < 0.5:
            if item.is_obstacle:
                lives -= 1
                lives_text.text = f'Lives: {lives}'
                if lives <= 0:
                    game_over = True
                    game_over_text.text = 'GAME OVER\nPress R'
            else:
                score += 10
                score_text.text = f'Score: {score}'
                
            falling_items.remove(item)
            destroy(item)
            
        elif item.y < -5:
            falling_items.remove(item)
            destroy(item)

# Move camera back slightly and angle it downward to lock 3D depth perception tracking
camera.position = (0, 0, -15)
camera.rotation_x = 10

# Execute execution pipeline loop
app.run()