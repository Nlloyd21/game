import arcade
import random
import math
from pathlib import Path

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Fruit Catcher: Master Edition"

# Object Configurations
OBJECT_TYPES = [
    {"name": "Apple", "color": arcade.color.RED, "points": 10, "is_obstacle": False, "radius": 16},
    {"name": "Orange", "color": arcade.color.ORANGE, "points": 20, "is_obstacle": False, "radius": 18},
    {"name": "Banana", "color": arcade.color.YELLOW, "points": 35, "is_obstacle": False, "radius": 14},
    {"name": "Bomb", "color": arcade.color.CHARCOAL, "points": -50, "is_obstacle": True, "radius": 20}
]

# --- State Definitions ---
STATE_MENU = 0
STATE_INSTRUCTIONS = 1
STATE_GAMEPLAY = 2
STATE_PAUSE = 3
STATE_SETTINGS = 4
STATE_GAMEOVER = 5

class FruitCatcherGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # Core Engine States
        self.current_state = STATE_MENU
        self.previous_state = STATE_MENU
        
        # Settings Variables
        self.control_mode = "KEYBOARD"  # "KEYBOARD" or "MOUSE"
        self.sensitivity = 5.0          
        
        # Gameplay State
        self.score = 0
        self.lives = 3
        self.level = 1
        self.score_needed = 150
        
        # Entities
        self.basket_x = SCREEN_WIDTH // 2
        self.basket_y = 60
        self.basket_width = 120
        self.basket_height = 25
        self.basket_change_x = 0
        
        self.falling_objects = []
        
        # --- Audio Setup (Fixed for Arcade 3.0+ using safe alternative paths) ---
        # Arcade has updated game engine presets that are guaranteed to resolve locally
        try:
            self.sound_collect = arcade.Sound(":resources:sounds/coin1.wav")
            self.sound_explosion = arcade.Sound(":resources:sounds/explosion1.wav")
            self.sound_level_up = arcade.Sound(":resources:sounds/upgrade1.wav")
        except Exception:
            # Absolute fallback to prevent crashes if something is wrong with installation resources
            self.sound_collect = None
            self.sound_explosion = None
            self.sound_level_up = None
        
        # Background Music Pipeline
        self.music_player = None
        self.bg_music_file = "background_music.mp3"  
        self.play_music()
        
        # --- Initialize Text Objects ---
        # Main Menu
        self.title_text = arcade.Text("FRUIT CATCHER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100, arcade.color.GOLD, 48, anchor_x="center", bold=True)
        self.menu_start_text = arcade.Text("Press [SPACE] to Start Game", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, arcade.color.WHITE, 18, anchor_x="center")
        self.menu_settings_text = arcade.Text("Press [S] for Settings Menu", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40, arcade.color.CYAN, 18, anchor_x="center")
        self.menu_exit_text = arcade.Text("Press [ESC] to Exit Application", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80, arcade.color.LIGHT_GRAY, 16, anchor_x="center")
        
        # Instructions Screen
        self.instr_title = arcade.Text("HOW TO PLAY", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 180, arcade.color.GOLD, 36, anchor_x="center", bold=True)
        self.instr_goal = arcade.Text("Catch the falling fruits in your basket. Avoid the bombs!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120, arcade.color.WHITE, 16, anchor_x="center")
        self.instr_points_title = arcade.Text("POINT VALUES:", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60, arcade.color.CYAN, 16, anchor_x="center", bold=True)
        self.instr_apple = arcade.Text("🔴 Apple: +10 Points", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, arcade.color.WHITE, 16, anchor_x="center")
        self.instr_orange = arcade.Text("🟠 Orange: +20 Points", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 15, arcade.color.WHITE, 16, anchor_x="center")
        self.instr_banana = arcade.Text("🟡 Banana: +35 Points", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, arcade.color.WHITE, 16, anchor_x="center")
        self.instr_bomb = arcade.Text("⚫ Bomb: -50 Points & Lose 1 Life", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 85, arcade.color.LIGHT_CORAL, 16, anchor_x="center", bold=True)
        self.instr_prompt = arcade.Text("Press [ENTER] to Begin Catching!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 160, arcade.color.GREEN, 20, anchor_x="center", bold=True)
        
        # Gameplay HUD
        self.hud_score = arcade.Text("", 20, SCREEN_HEIGHT - 35, arcade.color.WHITE, 16, bold=True)
        self.hud_level = arcade.Text("", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35, arcade.color.CYAN, 16, anchor_x="center", bold=True)
        self.hud_lives = arcade.Text("", SCREEN_WIDTH - 150, SCREEN_HEIGHT - 35, arcade.color.RED, 16, bold=True)
        
        # Pause Screen
        self.pause_title = arcade.Text("GAME PAUSED", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120, arcade.color.WHITE, 40, anchor_x="center", bold=True)
        self.pause_resume = arcade.Text("Press [ESC] to Resume Action", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40, arcade.color.GREEN, 18, anchor_x="center")
        self.pause_settings = arcade.Text("Press [S] to Open Settings Menu", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10, arcade.color.CYAN, 18, anchor_x="center")
        self.pause_quit = arcade.Text("Press [Q] to Quit to Main Menu", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60, arcade.color.LIGHT_CORAL, 18, anchor_x="center")
        
        # Settings Screen
        self.settings_title = arcade.Text("SETTINGS MENU", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 160, arcade.color.CYAN, 36, anchor_x="center", bold=True)
        self.settings_control = arcade.Text("", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40, arcade.color.WHITE, 20, anchor_x="center")
        self.settings_control_sub = arcade.Text("(Press [M] to toggle Mouse / Keyboard Input mapping modes)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 15, arcade.color.LIGHT_GRAY, 12, anchor_x="center")
        self.settings_sens = arcade.Text("", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, arcade.color.WHITE, 20, anchor_x="center")
        self.settings_sens_sub = arcade.Text("(Press [LEFT]/[RIGHT] arrow indices to alter speed scale limits)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 75, arcade.color.LIGHT_GRAY, 12, anchor_x="center")
        self.settings_back = arcade.Text("Press [BACKSPACE] to Return to Previous Window", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 180, arcade.color.GOLD, 16, anchor_x="center")
        
        # Game Over Screen
        self.game_over_title = arcade.Text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, arcade.color.RED, 45, anchor_x="center", bold=True)
        self.game_over_restart = arcade.Text("Press [R] to Restart Challenge Loop", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30, arcade.color.WHITE, 18, anchor_x="center")

        arcade.schedule(self.spawn_object, 0.9)

    def play_music(self):
        if Path(self.bg_music_file).is_file():
            try:
                music = arcade.Sound(self.bg_music_file)
                self.music_player = music.play(volume=0.3, loop=True)
            except Exception:
                pass  

    def spawn_object(self, delta_time):
        if self.current_state not in [STATE_GAMEPLAY, STATE_MENU]:
            return
            
        config = random.choices(OBJECT_TYPES, weights=[40, 30, 15, 15], k=1)[0]
        speed_mult = 1.0 + (self.level - 1) * 0.25 if self.current_state == STATE_GAMEPLAY else 0.6
        speed = random.uniform(3.0, 5.0) * speed_mult
        
        obj = {
            "x": random.randint(30, SCREEN_WIDTH - 30),
            "y": SCREEN_HEIGHT + 30,
            "speed": speed,
            "name": config["name"],
            "color": config["color"],
            "points": config["points"],
            "is_obstacle": config["is_obstacle"],
            "radius": config["radius"]
        }
        self.falling_objects.append(obj)

    def draw_picnic_background(self):
        # Sky
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 350, SCREEN_HEIGHT, arcade.color.LIGHT_BLUE)
        # Sun
        arcade.draw_circle_filled(700, 520, 40, arcade.color.SUNGLOW)
        # Grass
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, 350, arcade.color.CELADON)
        
        # Picnic Blanket
        blanket_left, blanket_right, blanket_bottom, blanket_top = 50, SCREEN_WIDTH - 50, 0, 110
        arcade.draw_lrbt_rectangle_filled(blanket_left, blanket_right, blanket_bottom, blanket_top, arcade.color.WHITE)
        
        tile_size = 30
        for x in range(blanket_left, blanket_right, tile_size):
            for y in range(blanket_bottom, blanket_top, tile_size):
                if (x // tile_size + y // tile_size) % 2 == 0:
                    r_width = min(tile_size, blanket_right - x)
                    r_height = min(tile_size, blanket_top - y)
                    arcade.draw_rect_filled(arcade.XYWH(x + r_width/2, y + r_height/2, r_width, r_height), arcade.color.LIGHT_CORAL)

    def draw_all_fruits(self):
        for obj in self.falling_objects:
            cx, cy, r = obj["x"], obj["y"], obj["radius"]
            if obj["name"] == "Apple":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                arcade.draw_line(cx, cy + r, cx + 5, cy + r + 6, arcade.color.BROWN, 3)
            elif obj["name"] == "Orange":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                arcade.draw_circle_filled(cx, cy + r, 4, arcade.color.FOREST_GREEN)
            elif obj["name"] == "Banana":
                arcade.draw_arc_outline(cx, cy, r*2, r*1.5, obj["color"], 180, 300, 8)
            elif obj["name"] == "Bomb":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                arcade.draw_line(cx, cy + r, cx + 8, cy + r + 10, arcade.color.LIGHT_GRAY, 2)

    def on_draw(self):
        self.clear()
        
        self.draw_picnic_background()
        self.draw_all_fruits()
        
        if self.current_state == STATE_MENU:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT), (0,0,0,80))
            self.title_text.draw()
            self.menu_start_text.draw()
            self.menu_settings_text.draw()
            self.menu_exit_text.draw()
            
        elif self.current_state == STATE_INSTRUCTIONS:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT), (15, 23, 42, 235))
            self.instr_title.draw()
            self.instr_goal.draw()
            self.instr_points_title.draw()
            self.instr_apple.draw()
            self.instr_orange.draw()
            self.instr_banana.draw()
            self.instr_bomb.draw()
            self.instr_prompt.draw()

        elif self.current_state == STATE_GAMEPLAY:
            arcade.draw_rect_filled(arcade.XYWH(self.basket_x, self.basket_y, self.basket_width, self.basket_height), arcade.color.SADDLE_BROWN)
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT - 25, SCREEN_WIDTH, 50), (0, 0, 0, 130))
            
            self.hud_score.text = f"SCORE: {self.score}"
            self.hud_level.text = f"LEVEL: {self.level}"
            self.hud_lives.text = f"LIVES: {'❤️' * max(0, self.lives)}"
            
            self.hud_score.draw()
            self.hud_level.draw()
            self.hud_lives.draw()

        elif self.current_state == STATE_PAUSE:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 150))
            self.pause_title.draw()
            self.pause_resume.draw()
            self.pause_settings.draw()
            self.pause_quit.draw()

        elif self.current_state == STATE_SETTINGS:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT), (20, 24, 33, 230))
            self.settings_title.draw()
            
            self.settings_control.text = f"1. CONTROL MODE: < {self.control_mode} >"
            self.settings_sens.text = f"2. CONTROLLER SENSITIVITY: [ {self.sensitivity:.1f} ]"
            
            self.settings_control.draw()
            self.settings_control_sub.draw()
            self.settings_sens.draw()
            self.settings_sens_sub.draw()
            self.settings_back.draw()

        elif self.current_state == STATE_GAMEOVER:
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 200))
            self.game_over_title.draw()
            self.game_over_restart.draw()

    def on_key_press(self, key, modifiers):
        if self.current_state == STATE_MENU:
            if key == arcade.key.SPACE:
                self.current_state = STATE_INSTRUCTIONS
            elif key == arcade.key.S:
                self.previous_state = STATE_MENU
                self.current_state = STATE_SETTINGS
            elif key == arcade.key.ESCAPE:
                arcade.exit()
                
        elif self.current_state == STATE_INSTRUCTIONS:
            if key == arcade.key.ENTER:
                self.score, self.lives, self.level = 0, 3, 1
                self.falling_objects.clear()
                self.current_state = STATE_GAMEPLAY

        elif self.current_state == STATE_GAMEPLAY:
            if key == arcade.key.ESCAPE:
                self.basket_change_x = 0
                self.current_state = STATE_PAUSE
            elif self.control_mode == "KEYBOARD":
                adjusted_speed = 3.0 + (self.sensitivity * 1.2)
                if key == arcade.key.LEFT or key == arcade.key.A:
                    self.basket_change_x = -adjusted_speed
                elif key == arcade.key.RIGHT or key == arcade.key.D:
                    self.basket_change_x = adjusted_speed

        elif self.current_state == STATE_PAUSE:
            if key == arcade.key.ESCAPE:
                self.current_state = STATE_GAMEPLAY
            elif key == arcade.key.S:
                self.previous_state = STATE_PAUSE
                self.current_state = STATE_SETTINGS
            elif key == arcade.key.Q:
                self.current_state = STATE_MENU

        elif self.current_state == STATE_SETTINGS:
            if key == arcade.key.BACKSPACE:
                self.current_state = self.previous_state
            elif key == arcade.key.M:
                self.control_mode = "MOUSE" if self.control_mode == "KEYBOARD" else "KEYBOARD"
                self.basket_change_x = 0
            elif key == arcade.key.RIGHT:
                self.sensitivity = min(10.0, self.sensitivity + 0.5)
            elif key == arcade.key.LEFT:
                self.sensitivity = max(1.0, self.sensitivity - 0.5)

        elif self.current_state == STATE_GAMEOVER:
            if key == arcade.key.R:
                self.score, self.lives, self.level = 0, 3, 1
                self.falling_objects.clear()
                self.current_state = STATE_GAMEPLAY

    def on_key_release(self, key, modifiers):
        if self.current_state == STATE_GAMEPLAY and self.control_mode == "KEYBOARD":
            if (key == arcade.key.LEFT or key == arcade.key.A) and self.basket_change_x < 0:
                self.basket_change_x = 0
            elif (key == arcade.key.RIGHT or key == arcade.key.D) and self.basket_change_x > 0:
                self.basket_change_x = 0

    def on_mouse_motion(self, x, y, dx, dy):
        if self.current_state == STATE_GAMEPLAY and self.control_mode == "MOUSE":
            sens_weight = self.sensitivity / 5.0  
            target_x = self.basket_x + (dx * sens_weight)
            self.basket_x = max(self.basket_width // 2, min(SCREEN_WIDTH - self.basket_width // 2, target_x))

    def on_update(self, delta_time):
        if self.current_state not in [STATE_GAMEPLAY, STATE_MENU]:
            return

        for obj in self.falling_objects[:]:
            obj["y"] -= obj["speed"]
            
            if self.current_state == STATE_GAMEPLAY:
                if (self.basket_x - self.basket_width//2 <= obj["x"] <= self.basket_x + self.basket_width//2) and \
                   (self.basket_y <= obj["y"] - obj["radius"] <= self.basket_y + self.basket_height):
                    
                    self.score += obj["points"]
                    if self.score < 0: self.score = 0
                    
                    if obj["is_obstacle"]:
                        if self.sound_explosion:
                            self.sound_explosion.play(volume=0.5)
                        self.lives -= 1
                        if self.lives <= 0:
                            self.current_state = STATE_GAMEOVER
                    else:
                        if self.sound_collect:
                            self.sound_collect.play(volume=0.4)
                            
                    self.falling_objects.remove(obj)
                    
                    if self.score >= self.score_needed:
                        if self.sound_level_up:
                            self.sound_level_up.play(volume=0.4)
                        self.level += 1
                        self.score_needed += 150 + (self.level * 50)
                    continue

            if obj["y"] + obj["radius"] < 0:
                self.falling_objects.remove(obj)

        if self.current_state == STATE_GAMEPLAY and self.control_mode == "KEYBOARD":
            self.basket_x += self.basket_change_x
            self.basket_x = max(self.basket_width // 2, min(SCREEN_WIDTH - self.basket_width // 2, self.basket_x))

if __name__ == "__main__":
    game = FruitCatcherGame()
    arcade.run()