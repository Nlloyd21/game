import arcade
import random
import math
from pathlib import Path

# --- Tkinter setup for Native Name Popups on macOS ---
import tkinter as tk
from tkinter import simpledialog
root = tk.Tk()
root.withdraw()  

# --- State Definitions ---
STATE_MENU = 0
STATE_INSTRUCTIONS = 1
STATE_INTRO = 2  
STATE_GAMEPLAY = 3
STATE_PAUSE = 4
STATE_SETTINGS = 5
STATE_GAMEOVER = 6

class FruitCatcherGame(arcade.Window):
    def __init__(self):
        super().__init__(title="Fruit Catcher: Ultra Edition", fullscreen=True)
        
        self.screen_w = self.width
        self.screen_h = self.height
        
        self.current_state = STATE_MENU
        self.previous_state = STATE_MENU
        self.control_mode = "KEYBOARD"  
        self.sensitivity = 5.0          
        
        self.score = 0
        self.lives = 3
        self.level = 1
        self.score_needed = 150
        
        self.intro_timer = 0.0
        self.last_intro_second = 4
        self.player_name_input = ""
        self.score_saved = False  
        
        self.stats_tracker = {
            "Apple": 0, "Blueberry": 0, "Orange": 0, "Strawberry": 0, "Banana": 0,
            "Bomb": 0, "IceCube": 0, "BigBasket": 0, "Starfruit": 0,
            "Magnet": 0, "Hourglass": 0, "WindFeather": 0, "RottenFruit": 0
        }
        
        self.freeze_timer = 0.0
        self.big_basket_timer = 0.0
        self.magnet_timer = 0.0
        self.slow_mo_timer = 0.0
        self.wind_timer = 0.0
        self.sluggish_timer = 0.0
        self.wind_dir = 1.0
        
        self.flash_counter = 0
        self.particles = []
        
        self.basket_x = self.screen_w // 2
        self.basket_y = 60
        self.base_basket_width = 120
        self.basket_width = self.base_basket_width
        self.basket_height = 25
        self.basket_change_x = 0
        
        self.falling_objects = []
        self.time_since_last_spawn = 0.0
        
        self.top_scores = []
        self.load_leaderboard()
        
        # --- FIXED: Isolated Audio Asset Pipeline ---
        self.snd_coin = self.safe_load_sound(":resources:sounds/coin1.wav")
        self.snd_bomb = self.safe_load_sound(":resources:sounds/explosion2.wav")
        self.snd_level = self.safe_load_sound(":resources:sounds/upgrade1.wav")
        self.snd_gameover = self.safe_load_sound(":resources:sounds/gameover1.wav")
        self.snd_beep = self.safe_load_sound(":resources:sounds/hit1.wav") 
        
        self.snd_basket = self.safe_load_sound(":resources:sounds/upgrade2.wav")  
        self.snd_star = self.safe_load_sound(":resources:sounds/secret1.wav")    
        self.snd_magnet = self.safe_load_sound(":resources:sounds/coin4.wav")     
        self.snd_slow = self.safe_load_sound(":resources:sounds/upgrade3.wav")    
        
        self.snd_ice = self.safe_load_sound(":resources:sounds/error4.wav")       
        self.snd_wind = self.safe_load_sound(":resources:sounds/jump2.wav")       
        self.snd_rot = self.safe_load_sound(":resources:sounds/lose2.wav")        
        
        self.bg_music = self.safe_load_sound(":resources:music/funkyrobot.mp3")
        self.music_player = None
        if self.bg_music:
            try:
                self.music_player = self.bg_music.play(volume=0.12, loop=True)
            except Exception:
                pass
            
        self.OBJECT_TYPES = [
            {"name": "Apple", "color": arcade.color.RED, "points": 10, "type": "fruit", "alignment": "good", "radius": 16},
            {"name": "Blueberry", "color": arcade.color.ROYAL_BLUE, "points": 15, "type": "fruit", "alignment": "good", "radius": 11},
            {"name": "Orange", "color": arcade.color.ORANGE, "points": 20, "type": "fruit", "alignment": "good", "radius": 18},
            {"name": "Strawberry", "color": arcade.color.CRIMSON, "points": 25, "type": "fruit", "alignment": "good", "radius": 14},
            {"name": "Banana", "color": arcade.color.YELLOW, "points": 35, "type": "fruit", "alignment": "good", "radius": 14},
            {"name": "Bomb", "color": arcade.color.CHARCOAL, "points": -50, "type": "bomb", "alignment": "bad", "radius": 20},
            {"name": "IceCube", "color": arcade.color.FRESH_AIR, "points": 0, "type": "ice", "alignment": "bad", "radius": 16},
            {"name": "BigBasket", "color": arcade.color.APPLE_GREEN, "points": 0, "type": "powerup_big", "alignment": "good", "radius": 16},
            {"name": "Starfruit", "color": arcade.color.GOLD, "points": 50, "type": "powerup_life", "alignment": "good", "radius": 15},
            {"name": "Magnet", "color": arcade.color.RED, "points": 0, "type": "powerup_magnet", "alignment": "good", "radius": 16},
            {"name": "Hourglass", "color": arcade.color.BURNT_ORANGE, "points": 0, "type": "powerup_slow", "alignment": "good", "radius": 15},
            {"name": "WindFeather", "color": arcade.color.LIGHT_GRAY, "points": 0, "type": "hazard_wind", "alignment": "bad", "radius": 14},
            {"name": "RottenFruit", "color": arcade.color.OLIVE, "points": -15, "type": "hazard_sluggish", "alignment": "bad", "radius": 15}
        ]

        self.title_text = arcade.Text("FRUIT CATCHER", self.screen_w//4, self.screen_h//2 + 150, arcade.color.GOLD, 56, anchor_x="center", bold=True)
        self.menu_start_text = arcade.Text("▶ Start Game [SPACE]", self.screen_w//4, self.screen_h//2 + 20, arcade.color.WHITE, 22, anchor_x="center")
        self.menu_settings_text = arcade.Text("⚙ Settings [S]", self.screen_w//4, self.screen_h//2 - 40, arcade.color.CYAN, 22, anchor_x="center")
        self.menu_exit_text = arcade.Text("❌ Exit Game [ESC]", self.screen_w//4, self.screen_h//2 - 100, arcade.color.LIGHT_GRAY, 22, anchor_x="center")
        
        self.instr_title = arcade.Text("GAME INSTRUCTIONS", self.screen_w//2, self.screen_h//2 + 240, arcade.color.GOLD, 38, anchor_x="center", bold=True)
        self.instr_goal = arcade.Text("Control your basket using LEFT/RIGHT arrow keys. Game speed increases dynamically per level tier.", self.screen_w//2, self.screen_h//2 + 180, arcade.color.WHITE, 16, anchor_x="center")
        self.instr_good_title = arcade.Text("✨ HELPFUL ITEMS (LEAVE GOLD SPARKLE TRAILS)", self.screen_w//2, self.screen_h//2 + 110, arcade.color.LIGHT_GREEN, 18, anchor_x="center", bold=True)
        self.instr_good_desc = arcade.Text("🍉 STANDARD FRUITS: Points!  |  🍏 GREEN APPLE: Big Basket!\n🌟 STARFRUIT: +1 Life!  |  🧲 RED MAGNET: Pulls fruit!\n⏳ HOURGLASS: Temporarily slows down falling speeds!", self.screen_w//2, self.screen_h//2 + 40, arcade.color.WHITE, 15, anchor_x="center", align="center", multiline=True, width=1000)
        self.instr_bad_title = arcade.Text("💀 HAZARDOUS ITEMS (LEAVE DARK SMOKE TRAILS)", self.screen_w//2, self.screen_h//2 - 50, arcade.color.LIGHT_CORAL, 18, anchor_x="center", bold=True)
        self.instr_bad_desc = arcade.Text("💣 LIT BOMBS: Deducts points and 1 Life!\n🧊 ICE CUBES: Instantly freezes basket movement mapping mechanics!\n🌪️ TORNADO VORTEX: Adds random slippery wind drift to controls!\n🤢 SLIME SPLAT: Sluggish penalty that drops basket speed to a crawl!", self.screen_w//2, self.screen_h//2 - 120, arcade.color.WHITE, 15, anchor_x="center", align="center", multiline=True, width=1000)
        self.instr_prompt = arcade.Text("Press [ENTER] to Begin the Game!", self.screen_w//2, self.screen_h//2 - 220, arcade.color.GREEN, 24, anchor_x="center", bold=True)
        
        self.hud_score = arcade.Text("", 40, self.screen_h - 40, arcade.color.WHITE, 18, bold=True)
        self.hud_level = arcade.Text("", self.screen_w // 2, self.screen_h - 40, arcade.color.CYAN, 18, anchor_x="center", bold=True)
        self.hud_lives = arcade.Text("", self.screen_w - 200, self.screen_h - 40, arcade.color.RED, 18, bold=True)
        self.status_text = arcade.Text("", self.screen_w // 2, 120, arcade.color.WHITE, 18, anchor_x="center", bold=True)
        
        self.pause_title = arcade.Text("GAME PAUSED", self.screen_w//2, self.screen_h//2 + 120, arcade.color.WHITE, 45, anchor_x="center", bold=True)
        self.pause_resume = arcade.Text("Press [ESC] to Resume Action", self.screen_w//2, self.screen_h//2 + 40, arcade.color.GREEN, 20, anchor_x="center")
        self.pause_settings = arcade.Text("Press [S] to Open Settings Menu", self.screen_w//2, self.screen_h//2 - 10, arcade.color.CYAN, 20, anchor_x="center")
        self.pause_quit = arcade.Text("Press [Q] to Quit to Main Menu", self.screen_w//2, self.screen_h//2 - 60, arcade.color.LIGHT_CORAL, 20, anchor_x="center")
        
        self.settings_title = arcade.Text("SETTINGS MENU", self.screen_w//2, self.screen_h//2 + 160, arcade.color.CYAN, 38, anchor_x="center", bold=True)
        self.settings_control = arcade.Text("", self.screen_w//2, self.screen_h//2 + 40, arcade.color.WHITE, 22, anchor_x="center")
        self.settings_control_sub = arcade.Text("(Press [M] to toggle Mouse / Keyboard Input mapping modes)", self.screen_w//2, self.screen_h//2 + 15, arcade.color.LIGHT_GRAY, 14, anchor_x="center")
        self.settings_sens = arcade.Text("", self.screen_w//2, self.screen_h//2 - 50, arcade.color.WHITE, 22, anchor_x="center")
        self.settings_sens_sub = arcade.Text("(Press [LEFT]/[RIGHT] arrow indices to alter speed scale limits)", self.screen_w//2, self.screen_h//2 - 75, arcade.color.LIGHT_GRAY, 14, anchor_x="center")
        self.settings_back = arcade.Text("Press [BACKSPACE] to Return to Previous Window", self.screen_w//2, self.screen_h//2 - 180, arcade.color.GOLD, 18, anchor_x="center")

    def safe_load_sound(self, file_path):
        """Helper to ensure one missing file doesn't crash the entire audio system."""
        try:
            return arcade.Sound(file_path)
        except Exception:
            return None

    def play_sound_safely(self, sound_object, volume=0.5):
        if sound_object:
            try:
                sound_object.play(volume=volume)
            except Exception:
                pass

    def load_leaderboard(self):
        self.top_scores = []
        file_path = Path("high_scores.txt")
        if file_path.is_file():
            try:
                lines = file_path.read_text().splitlines()
                parsed = []
                for line in lines:
                    if " | " in line and "Score: " in line:
                        parts = line.split(" | ")
                        name = parts[0].replace("[User: ", "").replace("]", "")
                        score = int(parts[1].replace("Score: ", ""))
                        parsed.append((name, score))
                parsed.sort(key=lambda item: item[1], reverse=True)
                self.top_scores = parsed[:5] 
            except Exception as e:
                pass

    def save_score_to_file(self):
        if self.score_saved:
            return
        final_name = self.player_name_input.strip()
        if final_name == "":
            final_name = "Anonymous"
        try:
            with open("high_scores.txt", "a") as file:
                file.write(f"[User: {final_name}] | Score: {self.score}\n")
            self.score_saved = True
            self.load_leaderboard() 
        except Exception as e:
            pass

    def spawn_object(self):
        if self.current_state in [STATE_MENU, STATE_INTRO]:
            weights = [20, 20, 20, 20, 20, 0, 0, 0, 0, 0, 0, 0, 0] 
        else:
            star_weight = max(1, 4 - (self.level // 3)) if (self.level % 3 == 0) else 0
            bomb_weight = min(35, 12 + (self.level * 3))  
            ice_weight = min(15, 6 + self.level)
            rotten_weight = min(15, 5 + self.level)
            fruit_weight = max(10, 25 - self.level * 2)
            powerup_weight = max(2, 6 - (self.level // 2))
            
            weights = [
                fruit_weight, fruit_weight - 2, fruit_weight - 4, fruit_weight - 6, fruit_weight - 8,
                bomb_weight, ice_weight, powerup_weight, star_weight, 
                powerup_weight, powerup_weight, ice_weight, rotten_weight
            ]
            
        config = random.choices(self.OBJECT_TYPES, weights=weights, k=1)[0]
        speed_mult = 1.0 + (self.level - 1) * 0.20 if self.current_state == STATE_GAMEPLAY else 0.5
        if self.current_state == STATE_GAMEPLAY and self.slow_mo_timer > 0:
            speed_mult *= 0.5
            
        speed = random.uniform(3.5, 5.5) * speed_mult
        
        obj = {
            "x": random.randint(30, self.screen_w - 30),
            "y": self.screen_h + 30,
            "speed": speed,
            "name": config["name"],
            "color": config["color"],
            "points": config["points"],
            "type": config["type"],
            "alignment": config["alignment"],
            "radius": config["radius"]
        }
        self.falling_objects.append(obj)

    def draw_picnic_background(self):
        arcade.draw_lrbt_rectangle_filled(0, self.screen_w, self.screen_h - 250, self.screen_h, arcade.color.LIGHT_BLUE)
        arcade.draw_circle_filled(self.screen_w - 100, self.screen_h - 100, 40, arcade.color.SUNGLOW)
        arcade.draw_lrbt_rectangle_filled(0, self.screen_w, 0, self.screen_h - 250, arcade.color.CELADON)
        blanket_left, blanket_right, blanket_bottom, blanket_top = 50, self.screen_w - 50, 0, 110
        arcade.draw_lrbt_rectangle_filled(blanket_left, blanket_right, blanket_bottom, blanket_top, arcade.color.WHITE)
        
        tile_size = 30
        for x in range(blanket_left, blanket_right, tile_size):
            for y in range(blanket_bottom, blanket_top, tile_size):
                if (x // tile_size + y // tile_size) % 2 == 0:
                    r_width = min(tile_size, blanket_right - x)
                    r_height = min(tile_size, blanket_top - y)
                    arcade.draw_rect_filled(arcade.XYWH(x + r_width/2, y + r_height/2, r_width, r_height), arcade.color.LIGHT_CORAL)

    def draw_all_objects(self):
        for p in self.particles:
            arcade.draw_circle_filled(p["x"], p["y"], p["size"], p["color"])

        for obj in self.falling_objects:
            cx, cy, r = obj["x"], obj["y"], obj["radius"]
            
            if obj["alignment"] == "good":
                glow_r = r + (math.sin(self.flash_counter * 0.1) * 4)
                arcade.draw_circle_filled(cx, cy, glow_r + 4, (255, 223, 0, 70))
            elif obj["alignment"] == "bad":
                arcade.draw_circle_outline(cx, cy, r + 4, arcade.color.MAGENTA if self.flash_counter % 20 < 10 else arcade.color.RED, 3)

            if obj["type"] == "fruit":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                if obj["name"] == "Apple":
                    arcade.draw_line(cx, cy + r, cx + 5, cy + r + 6, arcade.color.BROWN, 3)
                elif obj["name"] == "Orange" or obj["name"] == "Strawberry":
                    arcade.draw_circle_filled(cx, cy + r, 4, arcade.color.FOREST_GREEN)
                elif obj["name"] == "Banana":
                    arcade.draw_arc_outline(cx, cy, r*2, r*1.5, obj["color"], 180, 300, 8)
            elif obj["type"] == "bomb":
                arcade.draw_circle_filled(cx, cy, r, obj["color"]) 
                arcade.draw_rect_filled(arcade.XYWH(cx, cy + r - 2, r * 0.5, 6), arcade.color.LIGHT_GRAY)
                arcade.draw_line(cx, cy + r, cx + 8, cy + r + 12, arcade.color.BROWN, 2)
                spark_r = 4 + (math.sin(self.flash_counter * 0.4) * 2)
                arcade.draw_circle_filled(cx + 8, cy + r + 12, spark_r, arcade.color.ORANGE)
                arcade.draw_circle_filled(cx + 8, cy + r + 12, spark_r * 0.6, arcade.color.YELLOW)
            elif obj["type"] == "ice":
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, r*1.8, r*1.8), obj["color"])
                arcade.draw_line(cx - r, cy - r, cx + r, cy + r, arcade.color.WHITE, 1)
                arcade.draw_line(cx - r, cy + r, cx + r, cy - r, arcade.color.WHITE, 1)
            elif obj["type"] == "powerup_big":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                arcade.draw_line(cx, cy + r, cx + 5, cy + r + 6, arcade.color.BROWN, 3)
            elif obj["type"] == "powerup_magnet":
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, r*1.5, r*1.5), arcade.color.RED)
                arcade.draw_rect_filled(arcade.XYWH(cx, cy + r//3, r * 0.7, r), arcade.color.CELADON) 
                arcade.draw_rect_filled(arcade.XYWH(cx - r//2 - 2, cy + r//2, r*0.4, 5), arcade.color.SILVER)
                arcade.draw_rect_filled(arcade.XYWH(cx + r//2 + 2, cy + r//2, r*0.4, 5), arcade.color.SILVER)
            elif obj["type"] == "powerup_slow":
                arcade.draw_rect_filled(arcade.XYWH(cx, cy + r, r*1.5, 5), obj["color"]) 
                arcade.draw_rect_filled(arcade.XYWH(cx, cy - r, r*1.5, 5), obj["color"]) 
                arcade.draw_triangle_filled(cx - r, cy + r, cx + r, cy + r, cx, cy, arcade.color.FRESH_AIR)
                arcade.draw_triangle_filled(cx - r, cy - r, cx + r, cy - r, cx, cy, arcade.color.FRESH_AIR)
                arcade.draw_circle_filled(cx, cy - r + 6, r * 0.6, arcade.color.AZURE) 
                if self.flash_counter % 6 < 3:
                    arcade.draw_line(cx, cy + r - 4, cx, cy - r + 6, arcade.color.AZURE, 2) 
            elif obj["type"] == "hazard_wind":
                w_offset = math.sin(self.flash_counter * 0.2) * 5
                arcade.draw_ellipse_filled(cx + w_offset, cy + 10, r * 2.2, r * 0.6, arcade.color.LIGHT_GRAY)
                arcade.draw_ellipse_filled(cx - w_offset, cy, r * 1.6, r * 0.5, arcade.color.SILVER)
                arcade.draw_ellipse_filled(cx + w_offset * 0.5, cy - 10, r * 1.0, r * 0.4, arcade.color.DARK_GRAY)
            elif obj["type"] == "hazard_sluggish":
                points = [
                    (cx - r, cy), (cx - r//2, cy + r), (cx, cy + r//3), 
                    (cx + r//2, cy + r), (cx + r, cy), (cx + r//2, cy - r), 
                    (cx, cy - r//2), (cx - r//2, cy - r)
                ]
                arcade.draw_polygon_filled(points, obj["color"])
            elif obj["type"] == "powerup_life":
                arcade.draw_circle_filled(cx, cy, r, obj["color"])
                arcade.draw_circle_filled(cx, cy, r - 5, arcade.color.YELLOW_GREEN)

    def draw_leaderboard_ui(self):
        panel_x = self.screen_w - (self.screen_w // 3)
        panel_y = self.screen_h // 2
        panel_w = 460
        panel_h = 450
        
        arcade.draw_rect_filled(arcade.XYWH(panel_x, panel_y, panel_w, panel_h), (15, 23, 42, 200))
        arcade.draw_rect_outline(arcade.XYWH(panel_x, panel_y, panel_w, panel_h), arcade.color.GOLD, 2)
        arcade.draw_text("🏆 TOP 5 SCORES 🏆", panel_x, panel_y + 180, arcade.color.GOLD, 22, anchor_x="center", bold=True)
        
        if not self.top_scores:
            arcade.draw_text("No high scores logged yet!", panel_x, panel_y, arcade.color.LIGHT_GRAY, 16, anchor_x="center", italic=True)
        else:
            start_y = panel_y + 110
            for index, (name, high_score) in enumerate(self.top_scores):
                rank_str = f"{index + 1}. {name[:12].upper():<14} {high_score:>6}"
                arcade.draw_text(rank_str, panel_x - 170, start_y, arcade.color.WHITE, 20, font_name="Courier New", bold=True)
                start_y -= 55

    def draw_endgame_layout(self):
        center_x = self.screen_w // 2
        
        title_y = self.screen_h - (self.screen_h * 0.12)
        arcade.draw_text("GAME OVER", center_x, title_y, arcade.color.RED, 64, anchor_x="center", bold=True)
        
        # --- FIXED LAYOUT: Box is now safely sized to fully encapsulate the text lines ---
        box_w = min(740, int(self.screen_w * 0.60))
        box_h = 380  
        box_y = title_y - (box_h // 2) - 60
        
        arcade.draw_rect_filled(arcade.XYWH(center_x, box_y, box_w, box_h), (30, 41, 59, 230))
        arcade.draw_rect_outline(arcade.XYWH(center_x, box_y, box_w, box_h), arcade.color.CYAN, 1.5)
        arcade.draw_text("📊 ITEM HARVEST BREAKDOWN", center_x, box_y + (box_h // 2) - 40, arcade.color.CYAN, 18, anchor_x="center", bold=True)
        
        col1_text = (
            f"Apples:      {self.stats_tracker['Apple']:<3}   Blueberries: {self.stats_tracker['Blueberry']:<3}\n"
            f"Oranges:     {self.stats_tracker['Orange']:<3}   Strawberries:{self.stats_tracker['Strawberry']:<3}\n"
            f"Bananas:     {self.stats_tracker['Banana']:<3}   Starfruits:  {self.stats_tracker['Starfruit']:<3}"
        )
        col2_text = (
            f"Bombs Hit:   {self.stats_tracker['Bomb']:<3}   Ice Blocks:  {self.stats_tracker['IceCube']:<3}\n"
            f"Green Apples:{self.stats_tracker['BigBasket']:<3}   Magnets:     {self.stats_tracker['Magnet']:<3}\n"
            f"Hourglasses: {self.stats_tracker['Hourglass']:<3}   Rotten Slime:{self.stats_tracker['RottenFruit']:<3}"
        )
        
        text_render_y = box_y + (box_h // 2) - 95
        arcade.draw_text(col1_text, center_x - (box_w // 2) + 40, text_render_y, arcade.color.WHITE, 16, font_name="Courier New", bold=True, multiline=True, width=330)
        arcade.draw_text(col2_text, center_x + 15, text_render_y, arcade.color.WHITE, 16, font_name="Courier New", bold=True, multiline=True, width=330)
        
        # --- FIXED LAYOUT: Prompt sits cleanly at the bottom, directly beneath action buttons ---
        button_y = box_y - (box_h // 2) - 45
        arcade.draw_text("🔄 Play Again [R]", center_x - 220, button_y, arcade.color.WHITE, 22, anchor_x="center")
        arcade.draw_text("🏠 Main Menu [M]", center_x + 220, button_y, arcade.color.GOLD, 22, anchor_x="center")
        
        prompt_y = button_y - 85
        if not self.score_saved:
            cursor = "_" if (self.flash_counter % 30 < 15) else ""
            save_prompt = f"TYPE YOUR NAME TO SAVE SCORE: {self.player_name_input}{cursor}\n(Press [ENTER] to lock it in)"
            arcade.draw_text(save_prompt, center_x, prompt_y, arcade.color.GREEN, 20, anchor_x="center", bold=True, multiline=True, width=700, align="center")
        else:
            arcade.draw_text("✅ SCORE SAVED TO LEADERBOARD!", center_x, prompt_y, arcade.color.LIGHT_GRAY, 20, anchor_x="center", bold=True)

    def on_draw(self):
        self.clear()
        self.draw_picnic_background()
        self.draw_all_objects()
        
        if self.current_state == STATE_MENU:
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2, self.screen_w, self.screen_h), (0,0,0,80))
            self.title_text.draw()
            self.menu_start_text.draw()
            self.menu_settings_text.draw()
            self.menu_exit_text.draw()
            self.draw_leaderboard_ui()
            
        elif self.current_state == STATE_INSTRUCTIONS:
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2, self.screen_w, self.screen_h), (15, 23, 42, 240))
            self.instr_title.draw()
            self.instr_goal.draw()
            self.instr_good_title.draw()
            self.instr_good_desc.draw()
            self.instr_bad_title.draw()
            self.instr_bad_desc.draw()
            self.instr_prompt.draw()

        elif self.current_state == STATE_INTRO:
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2, self.screen_w, self.screen_h), (10, 15, 30, 220))
            arcade.draw_text("GET READY!", self.screen_w//2, self.screen_h//2 + 50, arcade.color.GOLD, 48, anchor_x="center", bold=True)
            
            bar_w = 400
            progress = (4.0 - self.intro_timer) / 4.0
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2 - 40, bar_w, 20), arcade.color.DARK_GRAY)
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2 - (bar_w//2) + (bar_w * progress // 2), self.screen_h//2 - 40, bar_w * progress, 20), arcade.color.GREEN)

        elif self.current_state == STATE_GAMEPLAY:
            b_color = arcade.color.SADDLE_BROWN
            
            if self.freeze_timer > 0:
                b_color = arcade.color.POWDER_BLUE
                self.status_text.text = f"🥶 FROZEN! {math.ceil(self.freeze_timer)}s"
            elif self.wind_timer > 0:
                b_color = arcade.color.LIGHT_SKY_BLUE
                self.status_text.text = f"🌪️ WIND GUST DRIFT ACTIVE! {math.ceil(self.wind_timer)}s"
            elif self.sluggish_timer > 0:
                b_color = arcade.color.PURPLE
                self.status_text.text = f"🤢 SLUGGISH (ROTTEN EFFECT): {math.ceil(self.sluggish_timer)}s"
            elif self.magnet_timer > 0:
                b_color = arcade.color.DEEP_PINK
                self.status_text.text = f"🧲 FRUIT MAGNET ENGAGED: {math.ceil(self.magnet_timer)}s"
            elif self.slow_mo_timer > 0:
                b_color = arcade.color.AQUA
                self.status_text.text = f"⏳ SLOW-MOTION FIELD ACTIVE: {math.ceil(self.slow_mo_timer)}s"
            elif self.big_basket_timer > 0:
                b_color = arcade.color.GOLD
                self.status_text.text = f"💪 GIANT BASKET ACTIVE: {math.ceil(self.big_basket_timer)}s"
            else:
                self.status_text.text = ""
                
            if self.status_text.text != "":
                self.status_text.draw()
                
            arcade.draw_rect_filled(arcade.XYWH(self.basket_x, self.basket_y, self.basket_width, self.basket_height), b_color)
            
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h - 25, self.screen_w, 50), (0, 0, 0, 130))
            self.hud_score.text = f"SCORE: {self.score}"
            self.hud_level.text = f"LEVEL: {self.level}"
            self.hud_lives.text = f"LIVES: {'❤️' * max(0, self.lives)}"
            self.hud_score.draw()
            self.hud_level.draw()
            self.hud_lives.draw()

        elif self.current_state == STATE_PAUSE:
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2, self.screen_w, self.screen_h), (0, 0, 0, 150))
            self.pause_title.draw()
            self.pause_resume.draw()
            self.pause_settings.draw()
            self.pause_quit.draw()

        elif self.current_state == STATE_SETTINGS:
            arcade.draw_rect_filled(arcade.XYWH(self.screen_w//2, self.screen_h//2, self.screen_w, self.screen_h), (20, 24, 33, 230))
            self.settings_title.draw()
            self.settings_control.text = f"1. CONTROL MODE: < {self.control_mode} >"
            self.settings_sens.text = f"2. CONTROLLER SENSITIVITY: [ {self.sensitivity:.1f} ]"
            self.settings_control.draw()
            self.settings_control_sub.draw()
            self.settings_sens.draw()
            self.settings_sens_sub.draw()
            self.settings_back.draw()

        elif self.current_state == STATE_GAMEOVER:
            self.draw_endgame_layout()

    def trigger_game_restart(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.freeze_timer = self.big_basket_timer = self.magnet_timer = 0.0
        self.slow_mo_timer = self.wind_timer = self.sluggish_timer = 0.0
        self.basket_width = self.base_basket_width
        self.player_name_input = ""
        self.falling_objects.clear()
        self.particles.clear()
        self.score_saved = False
        
        for key in self.stats_tracker:
            self.stats_tracker[key] = 0
            
        self.intro_timer = 4.0
        self.last_intro_second = 4
        self.current_state = STATE_INTRO

    def on_key_press(self, key, modifiers):
        if self.current_state == STATE_GAMEOVER and not self.score_saved:
            if key == arcade.key.ENTER:
                self.save_score_to_file()
                return
            elif key == arcade.key.BACKSPACE:
                self.player_name_input = self.player_name_input[:-1]
                return
            elif len(self.player_name_input) < 12:
                char = chr(key) if key < 256 else ""
                if char.isalnum() or char == " ":
                    self.player_name_input += char.upper()
                    return

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
                self.trigger_game_restart()

        elif self.current_state == STATE_GAMEPLAY:
            if key == arcade.key.ESCAPE:
                self.basket_change_x = 0
                self.current_state = STATE_PAUSE
            elif self.control_mode == "KEYBOARD" and self.freeze_timer <= 0:
                base_speed = 4.0 if self.sluggish_timer <= 0 else 1.5
                adjusted_speed = base_speed + (self.sensitivity * 1.5)
                
                if key == arcade.key.LEFT or key == arcade.key.A:
                    self.basket_change_x = -adjusted_speed
                elif key == arcade.key.RIGHT or key == arcade.key.D:
                    self.basket_change_x = adjusted_speed

        elif self.current_state == STATE_PAUSE:
            if key == arcade.key.ESCAPE:
                self.current_state = STATE_GAMEPLAY
            elif key == arcade.key.S:
                self.previous_state = arcade.key.S
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
                self.trigger_game_restart()
            elif key == arcade.key.M:
                self.current_state = STATE_MENU

    def on_key_release(self, key, modifiers):
        if self.current_state == STATE_GAMEPLAY and self.control_mode == "KEYBOARD":
            if (key == arcade.key.LEFT or key == arcade.key.A) and self.basket_change_x < 0:
                self.basket_change_x = 0
            elif (key == arcade.key.RIGHT or key == arcade.key.D) and self.basket_change_x > 0:
                self.basket_change_x = 0

    def on_update(self, delta_time):
        self.flash_counter += 1 
        
        if self.current_state == STATE_INTRO:
            self.intro_timer -= delta_time
            current_sec = int(self.intro_timer)
            
            if current_sec != self.last_intro_second:
                if current_sec > 0:
                    self.play_sound_safely(self.snd_beep, volume=0.2)
                elif current_sec == 0:
                    self.play_sound_safely(self.snd_level, volume=0.4)
                self.last_intro_second = current_sec
                
            if self.intro_timer <= 0:
                self.current_state = STATE_GAMEPLAY
            return

        if self.current_state == STATE_GAMEPLAY:
            if self.freeze_timer > 0:
                self.freeze_timer -= delta_time
                self.basket_change_x = 0 
            if self.big_basket_timer > 0:
                self.big_basket_timer -= delta_time
                if self.big_basket_timer <= 0: self.basket_width = self.base_basket_width
            if self.magnet_timer > 0:
                self.magnet_timer -= delta_time
            if self.slow_mo_timer > 0:
                self.slow_mo_timer -= delta_time
            if self.sluggish_timer > 0:
                self.sluggish_timer -= delta_time
                
            if self.wind_timer > 0:
                self.wind_timer -= delta_time
                if random.random() < 0.02: self.wind_dir *= -1.0
                self.basket_x += self.wind_dir * random.uniform(1.5, 3.5)

        for p in self.particles[:]:
            p["y"] -= p["speed"]
            p["size"] -= 0.1
            if p["size"] <= 0 or p["y"] < 0:
                self.particles.remove(p)

        if self.current_state not in [STATE_GAMEPLAY, STATE_MENU]:
            return

        self.time_since_last_spawn += delta_time
        spawn_interval = max(0.24, 0.9 - (self.level - 1) * 0.15)
        if self.time_since_last_spawn >= spawn_interval:
            self.spawn_object()
            self.time_since_last_spawn = 0.0

        for obj in self.falling_objects[:]:
            obj["y"] -= obj["speed"]
            
            if self.flash_counter % 4 == 0:
                if obj["alignment"] == "good" and obj["type"] != "fruit":
                    self.particles.append({
                        "x": obj["x"] + random.randint(-10, 10), "y": obj["y"],
                        "size": random.uniform(3.0, 5.0), "speed": random.uniform(1.0, 2.5),
                        "color": arcade.color.GOLD
                    })
                elif obj["alignment"] == "bad" and obj["type"] != "bomb":
                    self.particles.append({
                        "x": obj["x"] + random.randint(-8, 8), "y": obj["y"],
                        "size": random.uniform(4.0, 7.0), "speed": random.uniform(0.5, 1.5),
                        "color": (40, 40, 40, 180) 
                    })
            
            if self.current_state == STATE_GAMEPLAY:
                if self.magnet_timer > 0 and obj["type"] == "fruit" and obj["y"] < 400:
                    if obj["x"] < self.basket_x:
                        obj["x"] += 3.5
                    elif obj["x"] > self.basket_x:
                        obj["x"] -= 3.5
                
                if (self.basket_x - self.basket_width//2 <= obj["x"] <= self.basket_x + self.basket_width//2) and \
                   (self.basket_y <= obj["y"] - obj["radius"] <= self.basket_y + self.basket_height):
                    
                    self.stats_tracker[obj["name"]] += 1
                    
                    if obj["type"] == "fruit":
                        self.play_sound_safely(self.snd_coin, volume=0.4)
                        self.score += obj["points"]
                    elif obj["type"] == "bomb":
                        self.play_sound_safely(self.snd_bomb, volume=0.5)
                        self.score = max(0, self.score + obj["points"])
                        self.lives -= 1
                        if self.lives <= 0:
                            if self.bg_music and self.music_player:
                                self.bg_music.stop(self.music_player) 
                                self.music_player = None
                            self.play_sound_safely(self.snd_gameover, volume=0.6) 
                            self.current_state = STATE_GAMEOVER
                    elif obj["type"] == "ice":
                        self.play_sound_safely(self.snd_ice, volume=0.6)
                        self.freeze_timer = 3.0  
                    elif obj["type"] == "powerup_big":
                        self.play_sound_safely(self.snd_basket, volume=0.5)
                        self.basket_width = int(self.base_basket_width * 1.6) 
                        self.big_basket_timer = 5.0  
                    elif obj["type"] == "powerup_life":
                        self.play_sound_safely(self.snd_star, volume=0.6)
                        self.score += obj["points"]
                        self.lives = min(5, self.lives + 1) 
                    elif obj["type"] == "powerup_magnet":
                        self.play_sound_safely(self.snd_magnet, volume=0.5)
                        self.magnet_timer = 5.0 
                    elif obj["type"] == "powerup_slow":
                        self.play_sound_safely(self.snd_slow, volume=0.5)
                        self.slow_mo_timer = 4.0
                    elif obj["type"] == "hazard_wind":
                        self.play_sound_safely(self.snd_wind, volume=0.5)
                        self.wind_timer = 4.0
                    elif obj["type"] == "hazard_sluggish":
                        self.play_sound_safely(self.snd_rot, volume=0.5)
                        self.score = max(0, self.score + obj["points"])
                        self.sluggish_timer = 3.0
                            
                    self.falling_objects.remove(obj)
                    
                    if self.score >= self.score_needed:
                        self.play_sound_safely(self.snd_level, volume=0.4)
                        self.level += 1
                        self.score_needed += 150 + (self.level * 50)
                    continue

            if obj["y"] + obj["radius"] < 0:
                self.falling_objects.remove(obj)

        if self.current_state == STATE_GAMEPLAY and self.control_mode == "KEYBOARD":
            self.basket_x += self.basket_change_x
            
        self.basket_x = max(self.basket_width // 2, min(self.screen_w - self.basket_width // 2, self.basket_x))

if __name__ == "__main__":
    game = FruitCatcherGame()
    arcade.run()