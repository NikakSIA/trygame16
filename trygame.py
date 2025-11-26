#{"mapID": 0, "pos": [65, 15], "hp": 100, "inv": [], "bag": "", "max_hp": 100, "stren": 1, "agil": 1, "ms": 1, "arm": 0}
import arcade
from random import randrange
import pathlib
import json
import math
from pyglet.graphics import Batch


def eq(s, i, n):
    s[i] = n

def str_to_hash(s):
    d = {}
    for i in s.split("="):
        xd = i.index("&")
        d[i[:xd]] = i[xd+1:]
    return d

def on_range(x1, y1, x2, y2):
    xr = abs(x1 - x2)
    yr = abs(y1 - y2)
    return round((xr**2 + yr**2)**0.5, 2)

def generate_sprite(t, x, y, s):
    a = arcade.Sprite()
    a.texture = t.texture
    a.center_x = x
    a.center_y = y
    a.scale = s
    return a

ASSETS_PATH = pathlib.Path(__file__).resolve().parent.parent / "trygame16"
SCREEN_WIDTH = 700#576
SCREEN_HEIGHT = SCREEN_WIDTH


class GameView(arcade.View):
    """ Главный класс приложения. """

    def __init__(self):
        super().__init__()
        self.scaling = 1
        self.pause = True
        self.a_pressed = False
        self.d_pressed = False
        self.w_pressed = False
        self.s_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.right_pressed = False
        self.left_pressed = False
        self.todo = False
        self.q_pressed = False
        self.e_pressed = False
        self.ctrl_pressed = False
        self.enter_pressed = False
        self.shift_pressed = False
        self.alt_pressed = False
        self.attack = False
        self.Gameover = False
        self.Gameover_text = arcade.Text("", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, anchor_x="center", anchor_y="center", font_size=60)
        self.ms_modifer = 1
        self.stamina = 100
        self.timer = 0
        self.oldtime = 0
        self.oldtime1 = 0        
        self.change_melee_attack_x = 0
        self.change_melee_attack_y = 0
        self.batch = []
        self.info_language = "RU"
        self.price_texts = []
        self.boss_hp = 0
        with open("save.json", encoding="UTF-8") as file_in:
            save = json.load(file_in)
        self.map_ID = save["mapID"]
        self.save_inv = [save["inv"], save["bag"]]
        
        self.textures = arcade.Scene.from_tilemap(arcade.load_tilemap(str(ASSETS_PATH / "textures.tmj"), self.scaling))
        self.enemy_groups = arcade.Scene.from_tilemap(arcade.load_tilemap(str(ASSETS_PATH / "enemy_groups.json"), self.scaling))
        self.player_list = arcade.SpriteList()
        self.player_sprite = generate_sprite(self.textures.get_sprite_list("textures")[0], save["pos"][0], save["pos"][1], self.scaling) # Стартовая позиция
        self.player_sprite.properties["hitpoints"] = save["hp"]
        self.player_sprite.properties["max_hitpoints"] = save["max_hp"]
        self.player_sprite.properties["strength"] = save["stren"]
        self.player_sprite.properties["agility"] = save["agil"]
        self.player_sprite.properties["movespeed"] = save["ms"]
        self.player_sprite.properties["armor"] = save["arm"]
        self.player_sprite.properties["rageat"] = 0
        self.player_list.append(self.player_sprite)
        self.progectiles = arcade.SpriteList()
        self.bonus_stats = {"strength": 0, "agility": 0, "movespeed": 0, "armor": 0, "max_hitpoints": 0, "hp_reg":0}
        
        

        self.icons = arcade.SpriteList()

        self.melee_attack = generate_sprite(self.textures.get_sprite_list("textures")[3], 0, 0, 0.1)
        self.melee_attack.properties["active"] = False
        self.icons.append(self.melee_attack)

        self.in_chest = arcade.SpriteList()
        self.opened_chest = 0
        

        self.inventory = arcade.SpriteList()
        for i in range(6):
            inventory_part = generate_sprite(self.textures.get_sprite_list("textures")[1], SCREEN_WIDTH - 16, ((SCREEN_HEIGHT - 16) - (30 * i)), 1.5)
            inventory_part.properties["content"] = 0
            inventory_part.properties["selected"] = False
            self.inventory.append(inventory_part)
        self.inventory[0].properties["selected"] = True
        

        self.mark = generate_sprite(self.textures.get_sprite_list("textures")[2], [i for i in self.inventory if i.properties["selected"]][0].center_x - 30, [i for i in self.inventory if i.properties["selected"]][0].center_y, 1.5)
        self.icons.append(self.mark)

        self.heart = generate_sprite(self.textures.get_sprite_list("textures")[15], 10, SCREEN_HEIGHT - 10, 1.5)
        self.icons.append(self.heart)
        self.hp_text = arcade.Text(str(self.player_sprite.properties["hitpoints"]), self.heart.center_x + 10, self.heart.center_y - 5)
        self.selected_inv_text = arcade.Text("", SCREEN_WIDTH - 5, SCREEN_HEIGHT - 200, font_size=10, anchor_x="right")
        self.damage_text = arcade.Text("", 0, 0, font_size=int(10*self.scaling))
        self.damage_text_update_time = 0
        self.minus_hp_text = arcade.Text("", self.heart.center_x + 10, self.heart.center_y - 15, font_size=int(10*self.scaling))
        self.minus_hp_update_time = 0

        self.point = self.textures.get_sprite_list("textures")[4]
        self.point.scale = 0.8 * self.scaling
        self.point.visible = False

    def kill_enemy(self, enemy):
        if enemy.properties["content"] != "" and not "reincarnable" in enemy.properties["mods"].split():
            corpse = generate_sprite(self.textures.get_sprite_list("textures")[6], enemy.center_x, enemy.center_y, enemy.scale)
            corpse.properties["locked"] = False
            corpse.properties["content"] = enemy.properties["content"]
            corpse.properties["delete"] = True
            corpse.properties["slots"] = len(enemy.properties["content"].split())
            self.scene.get_sprite_list("chests").append(corpse)
        if "twisted" in enemy.properties["mods"].split():
            for i in range(2):
                minion = generate_sprite(enemy, enemy.center_x + i * 15 / 1.5 * self.scaling, enemy.center_y, 0.8 * self.scaling)
                minion.properties = enemy.properties.copy()
                minion.properties["content"] = ""
                minion.properties["sees_player"] = True
                minion.properties["hitpoints"] = enemy.properties["max_hitpoints"] / 2
                minion.properties["max_hitpoints"] = enemy.properties["max_hitpoints"] / 2
                minion.properties["mods"] = ""
                self.scene.get_sprite_list("enemies").append(minion)
        if "attack" in enemy.properties["mods"].split():
            enemy.properties["attacking"].properties["isattack"] = False
        if "reincarnable" in enemy.properties["mods"].split():
            corpse = generate_sprite(self.textures.get_sprite_list("textures")[6], enemy.center_x, enemy.center_y, self.scaling)
            corpse.properties = enemy.properties.copy()
            corpse.properties["movement"] = "stand"
            corpse.properties["hitpoints"] = 50
            corpse.properties["mods"] = "reincarnating"
            corpse.properties["deathat"] = self.timer
            self.scene.get_sprite_list("enemies").append(corpse)
        if "boss" in enemy.properties["mods"].split():
            while len(self.scene.get_sprite_list("enemies")) != 0:
                self.scene.get_sprite_list("enemies")[0].remove_from_sprite_lists()
            self.Gameover = True

        enemy.remove_from_sprite_lists()

    def spawn_enemy_without_collisions(self, enemy, hash={}):
        self.scene.get_sprite_list("enemies").append(enemy)
        enemy.center_x += randrange(-5, 5, 1)
        enemy.center_y += randrange(-5, 5, 1)
        if hash.get(str(enemy.position), False) or arcade.check_for_collision_with_list(enemy, self.wall_list) or arcade.check_for_collision_with_list(enemy, self.player_list) or arcade.check_for_collision_with_list(enemy, self.scene.get_sprite_list("enemies")):
            hash[str(enemy.position)] = True
            enemy.remove_from_sprite_lists()
            self.spawn_enemy_without_collisions(enemy, hash)
            

    def stat_update(self, reverse=False):
        for i in self.bonus_stats.keys():
            self.bonus_stats[i] = 0
        for slot in self.inventory:
            if slot.properties["content"] != 0 and slot.properties["content"].properties["type"] == "passive":
                buffs = str_to_hash(slot.properties["content"].properties["buffs"])
                for i in buffs.keys():
                    self.bonus_stats[i] += float(buffs[i])
        if self.player_sprite.properties["hitpoints"] > self.player_sprite.properties["max_hitpoints"] + self.bonus_stats["max_hitpoints"]:
            self.player_sprite.properties[i] = self.player_sprite.properties["max_hitpoints"] + self.bonus_stats["max_hitpoints"]        
                
    
    def decode_item(self, item, reverse=False):
        if not reverse:
            name = "".join([f for f in item[:item.index("/")] if f.isalpha()])
            count = int("".join([f for f in item[:item.index("/")] if f.isdigit()]))
            stats = item[item.index("/") + 1:][:-1].split("#")
            
            chest_content = generate_sprite(self.textures.get_sprite_list("textures")[0], 0, 0, 1.5)
            chest_content.properties["count"] = count
            chest_content.properties["type"] = name
            if not name in ["weapon", "bag", "passive", "staff"]:
                chest_content.properties["max_count"] = 100
            else:
                chest_content.properties["max_count"] = 1
            chest_content.properties["in_inventory"] = False
            chest_content.properties["in_chest"] = True
            for i in set(stats) - set(("count", "type")):
                key = i.split(":")[0]
                v = i.split(":")[1]
                if key == "t":
                    chest_content.texture = self.textures.get_sprite_list("textures")[int(v)].texture
                elif key[0] == "i":
                    chest_content.properties[key[1:]] = int(v)
                elif key[0] == "f":
                    chest_content.properties[key[1:]] = float(v)
                elif key[0] == "s":
                    chest_content.properties[key[1:]] = v
                elif key[0] == "b":
                    chest_content.properties[key[1:]] = v=="True"
            return chest_content
        else:
            content = str(item.properties["count"]) + item.properties["type"] + "/t:" + str([i for i in range(len(self.textures.get_sprite_list("textures"))) if self.textures.get_sprite_list("textures")[i].texture == item.texture][0]) + "#"
            for i in set(item.properties.keys()) - set(("count", "type", "max_count", "tile_id", "content")):
                content += str(type(item.properties[i]))[str(type(item.properties[i])).index("'") + 1] + i + ":" + str(item.properties[i]) + "#"
            return content

    def setup(self):
        map_path = ASSETS_PATH / f"map{self.map_ID}.json"
        self.game_map = arcade.load_tilemap(str(map_path))
        self.scaling = SCREEN_HEIGHT / (self.game_map.width * self.game_map.tile_width)
        self.game_map = arcade.load_tilemap(str(map_path), self.scaling)         
        self.scene = arcade.Scene.from_tilemap(self.game_map)
        self.player_sprite.scale = self.scaling
        self.player_sprite.center_x *= self.scaling
        self.player_sprite.center_y *= self.scaling
        for i in ["pickups", "enemies", "chests", "portals", "sp_doors", "doors"]:           
            try:
                self.scene.get_sprite_list(i)
            except KeyError:
                self.scene.add_sprite_list(i)

        self.mark.position = ([i for i in self.inventory if i.properties["selected"]][0].center_x - 30, [i for i in self.inventory if i.properties["selected"]][0].center_y)

        self.wall_list = arcade.SpriteList()
        self.wall_list.extend(self.scene.get_sprite_list("walls"))
        self.wall_list.extend(self.scene.get_sprite_list("doors"))
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.background_color = arcade.color.BLACK

        border = generate_sprite(self.scene.get_sprite_list("walls")[0], -1, 0, 1)
        border.scale_x = 0.1
        border.scale_y = 500
        border.visible = False
        self.wall_list.append(border)

        border = generate_sprite(self.scene.get_sprite_list("walls")[0], self.game_map.width * self.game_map.tile_width * self.scaling + 1, 0, 1)
        border.scale_x = 0.1
        border.scale_y = 500
        border.visible = False
        self.wall_list.append(border)

        border = generate_sprite(self.scene.get_sprite_list("walls")[0], 0, -1, 1)
        border.scale_x = 500
        border.scale_y = 0.1
        border.visible = False
        self.wall_list.append(border)

        border = generate_sprite(self.scene.get_sprite_list("walls")[0], 0, self.game_map.height * self.game_map.tile_height * self.scaling + 1, 1)
        border.scale_x = 500
        border.scale_y = 0.1
        border.visible = False
        self.wall_list.append(border)
        self.wall_list.extend(self.scene.get_sprite_list("sp_doors"))
        if self.save_inv != []:
            for i, b in enumerate(self.save_inv[0]):
                a = self.decode_item(b)
                a.position = self.inventory[i].position
                if a.properties["type"] == "bag":
                    a.properties["content"] = self.save_inv[1]
                self.scene.get_sprite_list("pickups").append(a)
                self.inventory[i].properties["content"] = a
            self.save_inv.clear()
        
        save = {"mapID": self.map_ID, "pos": [self.player_sprite.center_x / self.scaling, self.player_sprite.center_y / self.scaling], "hp": self.player_sprite.properties["hitpoints"], "inv":[], "bag": ""}
        save["max_hp"] = self.player_sprite.properties["max_hitpoints"]
        save["stren"] = self.player_sprite.properties["strength"]
        save["agil"] = self.player_sprite.properties["agility"]
        save["ms"] = self.player_sprite.properties["movespeed"]
        save["arm"] = self.player_sprite.properties["armor"]
        for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0]:
            save["inv"].append(self.decode_item(i, reverse=True))
        if [i for i in self.inventory if i.properties["content"] != 0 and i.properties["content"].properties["type"] == "bag"] != []:
            save["bag"] = [i for i in self.inventory if i.properties["content"] != 0 and i.properties["content"].properties["type"] == "bag"][0].properties["content"].properties["content"]
        with open("save.json", "w") as file_out:
            json.dump(save, file_out)
        self.stat_update()

        self.pause = True
        self.info = {}
        with open("info.json", encoding="UTF-8") as file_in:
            info = json.load(file_in)
        self.info["RU"] = info[self.map_ID]
        with open("info1.json", encoding="UTF-8") as file_in:
            info = json.load(file_in)
        self.info["EN"] = info[self.map_ID]
        self.process_keychange1()

        a = 0
        for i in self.scene.get_sprite_list("enemies"):
            if "patrolling" in i.properties:
                i.position=[int(f) * self.scaling for f in i.properties["patrolling"].split()[i.properties["pointID"]].split(",")]
            if "invisible" in i.properties["mods"].split():
                i.visible = False
            if i.properties["movement"] in ["simple", "jerker"]:
                i.properties["lastreaction"] = 0
            if "rgb" in i.properties.keys():
                i.rgb = tuple(map(int, i.properties["rgb"].split()))
                del i.properties["rgb"]
            i.properties["effects"] = {}
        for i in self.scene.get_sprite_list("pickups"):
            if "price" in i.properties.keys() and not(i.properties["in_chest"] or i.properties["in_inventory"]):
                self.price_texts.append(arcade.Text(f"{i.properties['price']}¢", i.center_x - 5 * self.scaling, i.center_y + 10 * self.scaling))
            if "rgb" in i.properties.keys():
                i.rgb = tuple(map(int, i.properties["rgb"].split()))
                del i.properties["rgb"]

        for i in self.scene.get_sprite_list("chests"):
            if "treasure" in i.properties.keys():
                i.properties["content"] += i.properties["treasure"].split()[randrange(0, len(i.properties["treasure"].split()), 1)]
        
        for i in self.scene.get_sprite_list("sp_doors"):
            if "rgb" in i.properties.keys():
                i.rgb = tuple(map(int, i.properties["rgb"].split()))
                del i.properties["rgb"]
        if self.map_ID == 5:
            self.boss_hp = generate_sprite(self.textures.get_sprite_list("textures")[49], SCREEN_WIDTH/2, 20, self.scaling)
            self.boss_hp.scale_x = 60*self.scaling
            self.boss_hp.rgb = (255, 0, 0)
            self.icons.append(self.boss_hp)

    def on_draw(self):
        self.clear()
        self.scene.draw()
        self.wall_list.draw()
        self.player_list.draw()
        self.inventory.draw()
        self.icons.draw()        
        self.in_chest.draw()
        self.progectiles.draw()
        self.hp_text.draw()
        self.selected_inv_text.draw()
        self.damage_text.draw()
        self.minus_hp_text.draw()
        [i.draw() for i in self.price_texts]
        self.Gameover_text.draw()
        [i.draw() for i in self.batch]
    #def process_keychange(self):


    def process_keychange1(self):
              
        if not (self.Gameover or self.pause):
            #Контроль активного слота в инвентаре  
            index = self.inventory.index([i for i in self.inventory if i.properties["selected"]][0])
            if self.q_pressed and not self.e_pressed:
                if not self.inventory[0].properties["selected"]:                
                    self.inventory[index].properties["selected"] = False
                    self.inventory[index - 1].properties["selected"] = True
                    self.mark.center_y += 30
            elif self.e_pressed and not self.q_pressed:
                if not self.inventory[-1].properties["selected"]:
                    self.inventory[index].properties["selected"] = False
                    self.inventory[index + 1].properties["selected"] = True
                    self.mark.center_y -= 30

            #Контроль активного слота в сундуке
            if len(self.in_chest) > 0:
                chest_index = self.in_chest.index([i for i in self.in_chest if i.properties["selected"]][0])
                if len(self.in_chest) > 1:
                    if self.right_pressed and not self.in_chest[-1].properties["selected"]:
                        self.in_chest[chest_index].properties["selected"] = False
                        self.in_chest[chest_index + 1].properties["selected"] = True
                    if self.left_pressed and not self.in_chest[0].properties["selected"]:
                        self.in_chest[chest_index].properties["selected"] = False
                        self.in_chest[chest_index - 1].properties["selected"] = True
                if len(self.in_chest) > 10:
                    if self.up_pressed and chest_index >= 10:
                        self.in_chest[chest_index].properties["selected"] = False
                        self.in_chest[chest_index - 10].properties["selected"] = True
                    if self.down_pressed and len(self.in_chest) >= 10 + chest_index:
                        self.in_chest[chest_index].properties["selected"] = False
                        self.in_chest[chest_index + 10].properties["selected"] = True
                

                #визуализация выбранного слота в сундуке
                spart = self.in_chest[self.in_chest.index([i for i in self.in_chest if i.properties["selected"]][0])]
                spart.scale = 2
                for i in self.in_chest:
                    if i != spart:
                        i.scale = 1.5

            #копание в сундуке
            if self.todo and len(self.in_chest) > 0:
                selected_chest = [i for i in self.in_chest if i.properties["selected"]][0]
                selected_invevtory = [i for i in self.inventory if i.properties["selected"]][0]
                if selected_invevtory.properties["content"] == 0:
                    selected_invevtory.properties["content"] = selected_chest.properties["content"]
                    selected_chest.properties["content"] = 0
                    selected_invevtory.properties["content"].center_x = selected_invevtory.center_x
                    selected_invevtory.properties["content"].center_y = selected_invevtory.center_y
                    selected_invevtory.properties["content"].properties["in_inventory"] = True
                    selected_invevtory.properties["content"].properties["in_chest"] = False
                    self.stat_update()
                    arcade.load_sound(ASSETS_PATH / "sounds/pickup1.mp3").play()

                elif selected_chest.properties["content"] == 0 and selected_invevtory.properties["content"].properties["type"] != "bag":
                    selected_chest.properties["content"] = selected_invevtory.properties["content"]
                    selected_invevtory.properties["content"] = 0
                    selected_chest.properties["content"].center_x = selected_chest.center_x
                    selected_chest.properties["content"].center_y = selected_chest.center_y
                    selected_chest.properties["content"].properties["in_inventory"] = False
                    selected_chest.properties["content"].properties["in_chest"] = True
                    self.stat_update()
                    arcade.load_sound(ASSETS_PATH / "sounds/pickup1.mp3").play()
                    

                elif selected_chest.properties["content"].properties["type"] == selected_invevtory.properties["content"].properties["type"] and "name" not in selected_chest.properties["content"].properties.keys() and "name" not in selected_invevtory.properties["content"].properties.keys():
                    selected_invevtory.properties["content"].properties["count"] += selected_chest.properties["content"].properties["count"]
                    if selected_invevtory.properties["content"].properties["count"] > selected_invevtory.properties["content"].properties["max_count"]:
                        selected_invevtory.properties["content"].properties["count"] = selected_invevtory.properties["content"].properties["max_count"]
                        selected_chest.properties["content"].properties["count"] = selected_invevtory.properties["content"].properties["count"] + selected_chest.properties["content"].properties["count"] - selected_invevtory.properties["content"].properties["max_count"]
                    else:
                        selected_chest.properties["content"].remove_from_sprite_lists()
                        selected_chest.properties["content"] = 0
                    arcade.load_sound(ASSETS_PATH / "sounds/pickup1.mp3").play()

                elif selected_invevtory.properties["content"].properties["type"] != "bag":
                    rezerv = selected_invevtory.properties["content"]
                    selected_invevtory.properties["content"] = selected_chest.properties["content"]
                    selected_invevtory.properties["content"].center_x = selected_invevtory.center_x
                    selected_invevtory.properties["content"].center_y = selected_invevtory.center_y
                    selected_invevtory.properties["content"].properties["in_inventory"] = True
                    selected_invevtory.properties["content"].properties["in_chest"] = False

                    selected_chest.properties["content"] = rezerv
                    selected_chest.properties["content"].center_x = selected_chest.center_x
                    selected_chest.properties["content"].center_y = selected_chest.center_y
                    selected_chest.properties["content"].properties["in_inventory"] = False
                    selected_chest.properties["content"].properties["in_chest"] = True
                    self.stat_update()
                    arcade.load_sound(ASSETS_PATH / "sounds/pickup1.mp3").play()

            #использование расходников
            if self.todo and len(self.in_chest) == 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "disposable":
                buffs = str_to_hash([i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["buffs"])
                for i in buffs.keys():
                    if float(buffs[i]) < 5:
                        self.player_sprite.properties[i] += float(buffs[i])
                    else:
                        self.player_sprite.properties[i] += int(buffs[i])
                    if i == "hitpoints" and self.player_sprite.properties[i] > self.player_sprite.properties["max_hitpoints"] + self.bonus_stats["max_hitpoints"]:
                        self.player_sprite.properties[i] = self.player_sprite.properties["max_hitpoints"] + self.bonus_stats["max_hitpoints"]
                [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] -= 1
                if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                    [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists()
                    [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0


            #ДВЕРИ
            if self.todo and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "key":
                for door in self.scene.get_sprite_list("doors"):
                    if on_range(self.player_sprite.center_x, self.player_sprite.center_y, door.center_x, door.center_y) < 16 * self.scaling:
                        door.remove_from_sprite_lists()
                        arcade.load_sound(ASSETS_PATH/"sounds/open_door1.mp3").play()
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] += -1
                        if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists() 
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0

            if self.todo and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "spkey":
                for door in self.scene.get_sprite_list("sp_doors"):
                    if on_range(self.player_sprite.center_x, self.player_sprite.center_y, door.center_x, door.center_y) < 16 * self.scaling and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["spid"] == door.properties["spid"]:
                        for i in self.scene.get_sprite_list("sp_doors"):
                            if i.properties["spid"] == [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["spid"]:
                                i.scale = 0
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] += -1
                        if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists() 
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0

            #колдунства
            if self.todo and len(self.in_chest) == 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "staff":
                staff = [i for i in self.inventory if i.properties["selected"]][0].properties["content"]
                if self.timer - staff.properties["lastcast"] > staff.properties["qldown"]:
                    staff.properties["lastcast"] = self.timer
                    if staff.properties["spellid"] == 0:
                        if [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()] != []:
                            [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()][0].properties["hitpoints"] += 100
                            if [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()][0].properties["hitpoints"] > [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()][0].properties["max_hitpoints"]:
                                [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()][0].properties["hitpoints"] = [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()][0].properties["max_hitpoints"]
                        else:
                            boner = generate_sprite(self.textures.get_sprite_list("textures")[20], self.player_sprite.center_x, self.player_sprite.center_y, self.scaling)
                            boner.properties["content"] = ""
                            boner.properties["damage"] = 10
                            boner.properties["hitpoints"] = 25
                            boner.properties["max_hitpoints"] = 25
                            boner.properties["last_attack"] = 0
                            boner.properties["mods"] = "friendly"
                            boner.properties["opponent"] = 0
                            boner.properties["movement"] = "simple"
                            boner.properties["movespeed"] = 1.05
                            boner.properties["vision"] = 50
                            boner.properties["sees_player"] = True
                            boner.properties["lastreaction"] = 0
                            self.scene.get_sprite_list("enemies").append(boner)

                    elif staff.properties["spellid"] == 1:
                        shot = generate_sprite(self.textures.get_sprite_list("textures")[35], self.player_sprite.center_x, self.player_sprite.center_y, self.scaling)
                        shot.properties["damage"] = 0
                        shot.properties["range"] = 150 * self.scaling
                        shot.change_x = self.player_sprite.change_x * 2
                        shot.change_y = self.player_sprite.change_y * 2
                        if shot.change_x == 0 and shot.change_y == 0:
                            shot.change_x = 2*self.scaling 
                        shot.properties["mods"] = {"stun":5}
                        self.progectiles.append(shot)

                    elif staff.properties["spellid"] == 2:    
                        for i in self.scene.get_sprite_list("enemies"):
                            if "effects" in i.properties.keys():
                                i.properties["effects"]["stun"] = 7

                    elif staff.properties["spellid"] == 3:
                        self.player_sprite.properties["rageat"] = self.timer
                        self.player_sprite.rgb = arcade.color.RED
                        self.bonus_stats["strength"] += 0.3
                        self.bonus_stats["movespeed"] += 0.3

                    elif staff.properties["spellid"] == 4:    
                        for i in self.scene.get_sprite_list("pickups"):
                            if i.properties["in_inventory"] and i.properties["type"] == "staff":
                                i.properties["lastcast"] -= min(i.properties["qldown"]/2, 5)
                    
                    elif staff.properties["spellid"] == 5:
                        shot = generate_sprite(self.textures.get_sprite_list("textures")[35], self.player_sprite.center_x, self.player_sprite.center_y, self.scaling)
                        shot.properties["range"] = 150 * self.scaling
                        shot.change_x = self.player_sprite.change_x * 3
                        shot.change_y = self.player_sprite.change_y * 3
                        if shot.change_x == 0 and shot.change_y == 0:
                            shot.change_x = 2*self.scaling 
                        shot.properties["tp"] = True
                        self.progectiles.append(shot)

            #переход на другой уровень
            if self.todo and arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("portals")):
                self.map_ID = arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("portals"))[0].properties["mapID"]
                in_inventory = [i for i in self.scene.get_sprite_list("pickups") if i.properties["in_inventory"] or i.properties["in_chest"]]
                self.player_sprite.position = (arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("portals"))[0].properties["player_x"], arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("portals"))[0].properties["player_y"])
                self.setup()
                self.scene.get_sprite_list("pickups").extend(in_inventory)

        if self.pause:
            for i in self.scene._sprite_lists:
                i.alpha = 120
            self.wall_list.alpha = 120
            self.batch = []
            for i, a in enumerate(self.info[self.info_language]):
                text = arcade.Text(a, 0, SCREEN_HEIGHT-20-i*30, font_size=14)
                self.batch.append(text)
            if self.shift_pressed and self.alt_pressed:
                if self.info_language == "RU":
                    self.info_language = "EN"
                elif self.info_language == "EN":
                    self.info_language = "RU"
        else:
            self.batch = []
            for i in self.scene._sprite_lists:
                i.alpha = 255
            self.wall_list.alpha = 255

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.w_pressed = True
        elif key == arcade.key.S:
            self.s_pressed = True
        elif key == arcade.key.A:
            self.a_pressed = True
        elif key == arcade.key.D:
            self.d_pressed = True
        elif key == arcade.key.SPACE:
            self.todo = True
        elif key == arcade.key.Q:
            self.q_pressed = True
        elif key == arcade.key.E:
            self.e_pressed = True
        elif key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.LCTRL:
            self.ctrl_pressed = True
        elif key == arcade.key.ENTER:
            self.enter_pressed = True
        elif key == 65505:
            self.shift_pressed = True
        elif key == 65513:
            self.alt_pressed = True
        elif key == arcade.key.TAB:
            self.pause = not(self.pause)
        self.process_keychange1()
    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.w_pressed = False
        elif key == arcade.key.S:
            self.s_pressed = False
        elif key == arcade.key.A:
            self.a_pressed = False
        elif key == arcade.key.D:
            self.d_pressed = False
        elif key == arcade.key.SPACE:
            self.todo = False
        elif key == arcade.key.Q:
            self.q_pressed = False
        elif key == arcade.key.E:
            self.e_pressed = False
        elif key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.LCTRL:
            self.ctrl_pressed = False
        elif key == arcade.key.ENTER:
            self.enter_pressed = False
        elif key == 65505:
            self.shift_pressed = False
        elif key == 65513:
            self.alt_pressed = False
        self.process_keychange1()

    def on_update(self, delta_time):       
        if not (self.Gameover or self.pause):
            self.Gameover_text.text = ""
            self.physics_engine.update()
            self.timer = round(self.timer + delta_time, 3)
            inventory = [0 for i in self.inventory]
            [eq(inventory, i, self.inventory[i].properties["content"].properties["type"]) for i in range(len(self.inventory)) if self.inventory[i].properties["content"] != 0]
            weapon_in_hands = [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "weapon"
            self.melee_attack.center_x = self.player_sprite.center_x + self.change_melee_attack_x
            self.melee_attack.center_y = self.player_sprite.center_y + self.change_melee_attack_y
            
            #движение игрока
            if self.w_pressed and not self.s_pressed:
                self.player_sprite.change_y = (self.player_sprite.properties["movespeed"] + self.bonus_stats["movespeed"]) * self.ms_modifer / 1.5 * self.scaling * ((60 * delta_time) % 4)
            elif self.s_pressed and not self.w_pressed:
                self.player_sprite.change_y = -(self.player_sprite.properties["movespeed"] + self.bonus_stats["movespeed"]) * self.ms_modifer / 1.5 * self.scaling * ((60 * delta_time) % 4)
            else:
                self.player_sprite.change_y = 0
            
            if self.d_pressed and not self.a_pressed:
                self.player_sprite.change_x = (self.player_sprite.properties["movespeed"] + self.bonus_stats["movespeed"]) * self.ms_modifer / 1.5 * self.scaling * ((60 * delta_time) % 4)
            elif self.a_pressed and not self.d_pressed:
                self.player_sprite.change_x = -(self.player_sprite.properties["movespeed"] + self.bonus_stats["movespeed"]) * self.ms_modifer / 1.5 * self.scaling * ((60 * delta_time) % 4)
            else:
                self.player_sprite.change_x = 0 
            
            #спринт            
            if self.stamina <= 20:
                self.ms_modifer = 0.7
            if self.ctrl_pressed and self.stamina > 0:
                self.ms_modifer = 1.35
                self.stamina -= 0.4
                if self.stamina < 0: 
                    self.stamina = 0
            elif self.stamina > 20:
                self.ms_modifer = 1
            if self.player_sprite.change_x == 0 and self.player_sprite.change_y == 0 and self.stamina < 100:
                self.stamina += 0.4
                if self.stamina > 100: 
                    self.stamina = 100
            self.mark.scale_x = 0.02 * self.stamina

            if int(self.timer)//30 > int(self.timer-delta_time)//30 and self.player_sprite.properties["hitpoints"] + self.bonus_stats["hp_reg"] <= self.player_sprite.properties["max_hitpoints"]:
                self.player_sprite.properties["hitpoints"] = int(self.player_sprite.properties["hitpoints"] + self.bonus_stats["hp_reg"])

            #боль врагов
            if len(self.scene.get_sprite_list("enemies")) > 0:
                enemy_hit = arcade.check_for_collision_with_list(self.melee_attack, self.scene.get_sprite_list("enemies"))
            else:
                enemy_hit = []
                if weapon_in_hands and self.melee_attack.properties["active"]:
                    pass
                    "searching sound...."
            for enemy in [i for i in enemy_hit if not "untouchable" in i.properties["mods"].split() and not "friendly" in i.properties["mods"].split()]:
                if weapon_in_hands and self.melee_attack.properties["active"]:
                    enemy.properties["hitpoints"] -= [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["damage"] * (self.player_sprite.properties["strength"] + self.bonus_stats["strength"])
                    if "mods" in [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties.keys() and "stun" in [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["mods"].split() and randrange(1, 4) == 3 and "effects" in enemy.properties.keys():
                        enemy.properties["effects"]["stun"] = 1.5
                    self.damage_text.x = enemy.center_x
                    self.damage_text.y = enemy.center_y + 10 * self.scaling
                    self.damage_text.text = "-" + str(round([i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["damage"] * (self.player_sprite.properties["strength"] + self.bonus_stats["strength"]), 1))
                    self.damage_text_update_time = self.timer
                    self.melee_attack.properties["active"] = False
                    for friend in [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()]:
                        if friend.properties["opponent"] == 0:
                            friend.properties["opponent"] = enemy
                    if enemy.properties["hitpoints"] <= 0:
                        self.kill_enemy(enemy)
                        arcade.load_sound(ASSETS_PATH/"sounds/kill1.mp3").play(0.2)
                    else:
                        arcade.load_sound(ASSETS_PATH/"sounds/hit2.wav").play(0.2)

            #боль игрока + смерть            
            player_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("enemies"))  
            if player_hit and self.timer - self.oldtime1 > 0.5 and not "friendly" in player_hit[0].properties["mods"].split() and ((("effects" in player_hit[0].properties.keys()) and ("stun" not in player_hit[0].properties["effects"].keys())) or ("effects" not in player_hit[0].properties.keys())):
                if player_hit[0].properties["damage"] > 0:
                    if randrange(0, 100, 1) > self.player_sprite.properties["armor"] + self.bonus_stats["armor"]:
                        self.player_sprite.properties["hitpoints"] -= player_hit[0].properties["damage"]
                        self.minus_hp_text.text = f'-{player_hit[0].properties["damage"]}'
                        arcade.load_sound(ASSETS_PATH/"sounds/damage1.mp3").play()
                    else:
                        self.minus_hp_text.text = "miss!"
                    self.minus_hp_update_time = self.timer
                if player_hit[0].properties["damage"] > 0 or ("thief" in player_hit[0].properties["mods"].split() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0):    
                    self.oldtime1 = self.timer
                for friend in [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()]:
                    if friend.properties["opponent"] == 0:
                        friend.properties["opponent"] = player_hit[0]
                if "shot" in player_hit[0].properties["mods"].split() or "attack" in player_hit[0].properties["mods"].split():
                    self.kill_enemy(player_hit[0])
    
                if "trader" in player_hit[0].properties["mods"].split() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0:
                    if "name" in [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties.keys() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["name"] in ["diamond", "ruby"]:
                        stuff = self.decode_item(player_hit[0].properties["content"])
                        stuff.center_x = player_hit[0].center_x
                        stuff.center_y = player_hit[0].center_y - 30 * self.scaling
                        self.scene.get_sprite_list("pickups").append(stuff)
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] -= 1
                        if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists()
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0
                if "blood_sacrifice" in player_hit[0].properties["mods"].split() or ("thief" in player_hit[0].properties["mods"].split() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0):
                    coin = generate_sprite(self.textures.get_sprite_list("textures")[7], self.player_sprite.center_x, self.player_sprite.center_y, 1.5)
                    coin.properties["type"] = "coin"
                    coin.properties["count"] = 1
                    coin.properties["max_count"] = 100
                    coin.properties["in_chest"] = False
                    coin.properties["in_inventory"] = False
                    if "thief" in player_hit[0].properties["mods"].split() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0:
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] -= 1
                        if "name" in [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties.keys() and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["name"] == "cheese":
                            self.kill_enemy(player_hit[0])
                        if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] in ["passive", "weapon", "disposable", "staff"]:
                            coin.properties["count"] = 5
                        if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists()
                            [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0 
                    self.scene.get_sprite_list("pickups").append(coin)
                if self.player_sprite.properties["hitpoints"] <= 0:
                    self.player_sprite.remove_from_sprite_lists()
                    self.Gameover = True                

            #атака дружелюбных врагов
            for friend in [i for i in self.scene.get_sprite_list("enemies") if "friendly" in i.properties["mods"].split()]:
                if self.timer - friend.properties["last_attack"] > 0.5:
                    for enemy in arcade.check_for_collision_with_list(friend, self.scene.get_sprite_list("enemies")):
                        if "friendly" not in enemy.properties["mods"].split() and "untouchable" not in enemy.properties["mods"].split():
                            enemy.properties["hitpoints"] -= friend.properties["damage"]
                            friend.properties["hitpoints"] -= enemy.properties["damage"]
                            if enemy.properties["hitpoints"] <= 0:
                                self.kill_enemy(enemy)
                            if friend.properties["hitpoints"] <= 0:
                                self.kill_enemy(friend)
                    friend.properties["last_attack"] = self.timer
                if friend.properties["opponent"] not in self.scene.get_sprite_list("enemies"):
                    friend.properties["opponent"] = 0
                    

            #Управление атаки            
            if weapon_in_hands and len(self.in_chest) == 0:                                 
                if not self.attack:                                                   
                    if self.up_pressed or self.down_pressed or self.right_pressed or self.left_pressed:
                        self.attack = True
                        self.oldtime = self.timer
                        if [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "melee":                           
                            self.melee_attack.properties["active"] = True                           
                        elif [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "range" and "arrow" in [i.properties["content"].properties["type"] for i in self.inventory if i.properties["content"] != 0]:
                            shot = generate_sprite(self.textures.get_sprite_list("textures")[8], self.player_sprite.center_x, self.player_sprite.center_y, self.scaling)
                            shot.properties["damage"] = [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["damage"] + [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["damage"]
                            shot.properties["range"] = [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["range"] / 1.5 * self.scaling
                            a = [i for i in self.inventory if i.properties["content"] != 0 and "shot_buffs" in i.properties["content"].properties.keys()]
                            if a:
                                shot.properties["mods"] = {}
                            for i in a:
                                for mod in str_to_hash(i.properties["content"].properties["shot_buffs"]).keys():
                                    shot.properties["mods"][mod] = float(str_to_hash(i.properties["content"].properties["shot_buffs"])[mod])
                            self.progectiles.append(shot)
                            if self.up_pressed:                   
                                shot.angle = 90
                                shot.change_y = [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["shotspeed"] * self.scaling
                            elif self.down_pressed:
                                shot.angle = 90
                                shot.change_y = -[i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["shotspeed"] * self.scaling
                            elif self.right_pressed:
                                shot.change_x = [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["shotspeed"] * self.scaling
                            elif self.left_pressed:    
                                shot.change_x = -[i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["shotspeed"] * self.scaling
                            if not "quiver" in [i.properties["content"].properties["name"] for i in self.inventory if i.properties["content"] != 0 and "name" in i.properties["content"].properties.keys()]:
                                [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["count"] -= 1
                                if [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "arrow"][0].properties["count"] <= 0:
                                    a = [i for i in [i for i in self.inventory if i.properties["content"] != 0] if i.properties["content"].properties["type"] == "arrow"][0]
                                    a.properties["content"].remove_from_sprite_lists()
                                    [i for i in [i for i in self.inventory if i.properties["content"] != 0] if i.properties["content"].properties["type"] == "arrow"][0].properties["content"] = 0

                    if self.up_pressed:                   
                        if [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "melee":
                            self.change_melee_attack_y = 20 / 1.5 * self.scaling
                            self.melee_attack.scale_x = self.scaling
                            self.melee_attack.scale_y = self.scaling
                    elif self.down_pressed:
                        if [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "melee":
                            self.change_melee_attack_y = -20 / 1.5 * self.scaling
                            self.melee_attack.scale_x = self.scaling
                            self.melee_attack.scale_y = -self.scaling
                    elif self.right_pressed:
                        if [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "melee":
                            self.change_melee_attack_x = 20 / 1.5 * self.scaling
                            self.melee_attack.scale_x = self.scaling
                            self.melee_attack.scale_y = self.scaling
                    elif self.left_pressed:
                        if [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["class"] == "melee":
                            self.change_melee_attack_x = -20 / 1.5 * self.scaling  
                            self.melee_attack.scale_x = -self.scaling
                            self.melee_attack.scale_y = self.scaling    
                
                elif self.attack and self.timer - self.oldtime > [i.properties["content"] for i in self.inventory if i.properties["selected"]][0].properties["qldown"]:
                    self.up_pressed = False
                    self.down_pressed = False
                    self.right_pressed = False
                    self.left_pressed = False
                    self.change_melee_attack_x = 0
                    self.change_melee_attack_y = 0
                    self.melee_attack.scale_x = 0.1
                    self.melee_attack.scale_y = 0.1
                    self.melee_attack.properties["active"] = False
                    self.attack = False
                    

            #движение снарядов
            for shot in self.progectiles:
                shot.center_x += shot.change_x
                shot.center_y += shot.change_y
                shot.properties["range"] -= abs(shot.change_x + shot.change_y)
                shot_hit = [i for i in arcade.check_for_collision_with_list(shot, self.scene.get_sprite_list("enemies")) if not "untouchable" in i.properties["mods"].split() and not "friendly" in i.properties["mods"].split()]
                if shot_hit != [] and "tp" not in shot.properties.keys():
                    shot_hit[0].properties["hitpoints"] -= shot.properties["damage"] * (self.player_sprite.properties["agility"] + self.bonus_stats["agility"])
                    if randrange(0, 100, 1) > 5:
                        shot_hit[0].properties["content"] += " 1arrow/t:11#bin_inventory:False#idamage:1#fshotspeed:1.5#bin_chest:True#"
                    if "mods" in shot.properties.keys():
                        for effect in shot.properties["mods"].keys():
                            shot_hit[0].properties["effects"][effect] = shot.properties["mods"][effect]
                    self.damage_text.x = shot_hit[0].center_x
                    self.damage_text.y = shot_hit[0].center_y + 10 * self.scaling
                    self.damage_text.text = "-" + str(round(shot.properties["damage"] * (self.player_sprite.properties["agility"] + self.bonus_stats["agility"]), 1))
                    self.damage_text_update_time = self.timer
                    if shot_hit[0].properties["hitpoints"] <= 0:
                        self.kill_enemy(shot_hit[0])
                    shot.remove_from_sprite_lists()
                if shot.properties["range"] <= 0 or arcade.check_for_collision_with_list(shot, self.wall_list):
                    if "tp" in shot.properties.keys():
                        self.player_sprite.position = shot.position
                    shot.remove_from_sprite_lists()
            
            #движение врага
            for enemy in self.scene.get_sprite_list("enemies"):
                if enemy.properties["movement"] in ["simple", "jerker"] and (("friendly" in enemy.properties["mods"].split() and enemy.properties["opponent"] == 0) or "friendly" not in enemy.properties["mods"].split()) and not ("melee" in enemy.properties["mods"].split() and enemy.properties["isattack"]):
                    range_to_player = on_range(enemy.center_x, enemy.center_y, self.player_sprite.center_x, self.player_sprite.center_y)
                    if enemy.center_x > self.player_sprite.center_x:
                        left = -1
                    else:
                        left = 1
                    if enemy.center_y > self.player_sprite.center_y:
                        down = -1
                    else:
                        down = 1
                    if range_to_player < enemy.properties["vision"] * self.scaling and not arcade.check_for_collision_with_list(enemy, self.player_list) and not enemy.properties["sees_player"] and self.timer - enemy.properties["lastreaction"] >= 1:   
                        enemy.properties["lastreaction"] = self.timer
                        flag = True
                        self.point.center_x = enemy.center_x
                        self.point.center_y = enemy.center_y
                        while not arcade.check_for_collision_with_list(self.point, self.player_list):
                            self.point.center_x += left * abs(enemy.center_x - self.player_sprite.center_x) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling
                            self.point.center_y += down * abs(enemy.center_y - self.player_sprite.center_y) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling
                            if arcade.check_for_collision_with_list(self.point, self.wall_list):
                                flag = False
                                break
                        if flag:
                            enemy.properties["sees_player"] = True
                            if "invisible" in enemy.properties["mods"].split():
                                enemy.visible = True
                            if enemy.properties["movement"] == "jerker":
                                enemy.properties["range"] = 0
                    
                    if "boss" in enemy.properties["mods"].split() and self.player_sprite.center_y > 20*self.scaling and not enemy.properties["sees_player"]:
                        enemy.properties["sees_player"] = True
                        enemy.visible = True
                        enemy.properties["vision"] = 1000*self.scaling
                        enemy.properties["lastpatternchange"] = self.timer - 10
                    if range_to_player > enemy.properties["vision"] * self.scaling:
                        enemy.properties["sees_player"] = False

                    if enemy.properties["movement"] == "jerker" and enemy.properties["sees_player"] and range_to_player != 0 and ((("effects" in enemy.properties.keys()) and ("stun" not in enemy.properties["effects"].keys())) or ("effects" not in enemy.properties.keys())):
                        if self.timer - enemy.properties["lastjerk"] > 1 and enemy.properties["range"] <= 0:
                            enemy.properties["range"] = 150*self.scaling + ("boss" in enemy.properties["mods"].split()) * 100 * self.scaling
                            enemy.change_x = left * abs(enemy.center_x - self.player_sprite.center_x) / (on_range(enemy.center_x, enemy.center_y, self.player_sprite.center_x, self.player_sprite.center_y) / (3*enemy.properties["movespeed"])) / 1.5 * self.scaling 
                            enemy.change_y = down * abs(enemy.center_y - self.player_sprite.center_y) / (on_range(enemy.center_x, enemy.center_y, self.player_sprite.center_x, self.player_sprite.center_y) / (3*enemy.properties["movespeed"])) / 1.5 * self.scaling
                            
                        
                    elif enemy.properties["movement"] == "simple" and enemy.properties["sees_player"] and range_to_player != 0 and ((("effects" in enemy.properties.keys()) and ("stun" not in enemy.properties["effects"].keys())) or ("effects" not in enemy.properties.keys())):
                        enemy.change_x = left * abs(enemy.center_x - self.player_sprite.center_x) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling 
                        enemy.change_y = down * abs(enemy.center_y - self.player_sprite.center_y) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling
                        if "shooting" in enemy.properties["mods"].split() and self.timer - 3 > enemy.properties["lastshotat"]:
                            enemy.properties["lastshotat"] = self.timer
                            shot = generate_sprite(self.textures.get_sprite_list("textures")[23], enemy.center_x, enemy.center_y, self.scaling)
                            shot.properties = enemy.properties.copy()
                            del shot.properties["effects"]
                            shot.properties["damage"] = enemy.properties["damage"]
                            shot.properties["range"] = 150 * self.scaling
                            shot.properties["mods"] = "untouchable shot"
                            shot.properties["content"] = ""
                            shot.properties["movement"] = "line"
                            shot.change_x = enemy.change_x * 2
                            shot.change_y = enemy.change_y * 2
                            self.scene.get_sprite_list("enemies").append(shot)
                            if "triple" in enemy.properties["mods"].split():
                                for i in range (-1, 2, 2):
                                    shot = generate_sprite(self.textures.get_sprite_list("textures")[23], enemy.center_x, enemy.center_y, self.scaling)
                                    shot.properties = enemy.properties.copy()
                                    del shot.properties["effects"]
                                    shot.properties["damage"] = enemy.properties["damage"]
                                    shot.properties["range"] = 150 * self.scaling
                                    shot.properties["mods"] = "untouchable shot"
                                    shot.properties["content"] = ""
                                    shot.properties["movement"] = "line"
                                    shot.change_x = left * abs(enemy.center_x - self.player_sprite.center_x + 20*self.scaling*i) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling 
                                    shot.change_y = down * abs(enemy.center_y - self.player_sprite.center_y) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling
                                    self.scene.get_sprite_list("enemies").append(shot)
                        if "necromancy" in enemy.properties["mods"].split() and self.timer - 7 > enemy.properties["lastshotat"]:
                            enemy.properties["lastshotat"] = self.timer
                            for i in range((1*"double" in enemy.properties["mods"].split()) + 1):
                                boner = generate_sprite(self.textures.get_sprite_list("textures")[20], enemy.center_x-i*20*self.scaling, enemy.center_y, self.scaling)
                                boner.properties["content"] = ""
                                boner.properties["damage"] = 10
                                boner.properties["hitpoints"] = 25
                                boner.properties["max_hitpoints"] = 25
                                boner.properties["mods"] = ""
                                boner.properties["movement"] = "simple"
                                boner.properties["movespeed"] = 1.05
                                boner.properties["vision"] = 120
                                boner.properties["sees_player"] = False
                                boner.properties["effects"] = {}
                                boner.properties["lastreaction"] = self.timer
                                if "king" in enemy.properties["mods"].split():
                                    boner.properties["hitpoints"] = 90
                                    boner.properties["max_hitpoints"] = 90
                                    boner.properties["damage"] = 20
                                    boner.properties["mods"] = "melee"
                                    boner.properties["isattack"] = False
                                    boner.properties["lastattack"] = 0
                                    boner.texture = self.textures.get_sprite_list("textures")[44].texture
                                self.scene.get_sprite_list("enemies").append(boner)
                        if "melee" in enemy.properties["mods"].split() and self.timer - 3 > enemy.properties["lastattack"]:
                            enemy.properties["lastattack"] = self.timer
                            enemy.properties["isattack"] = True
                            attack = generate_sprite(self.textures.get_sprite_list("textures")[3], enemy.center_x+25*enemy.change_x, enemy.center_y+25*enemy.change_y, self.scaling)
                            if enemy.change_x < 0:
                                attack.scale_x = -self.scaling
                            if enemy.change_y < 0:
                                attack.scale_y = -self.scaling
                            attack.properties["damage"] = enemy.properties["damage"]
                            attack.properties["mods"] = "untouchable attack"
                            attack.properties["content"] = ""
                            attack.properties["movement"] = "stand"
                            attack.properties["attacking"] = enemy
                            attack.properties["attackat"] = self.timer
                            self.scene.get_sprite_list("enemies").append(attack)
                            enemy.change_x = 0
                            enemy.change_y = 0

                    #патрулирование       
                    elif "patrolling" in enemy.properties.keys() and ((("effects" in enemy.properties.keys()) and ("stun" not in enemy.properties["effects"].keys())) or ("effects" not in enemy.properties.keys())):
                        point = [int(i) * self.scaling for i in enemy.properties["patrolling"].split()[enemy.properties["pointID"]].split(",")]
                        
                        if point[0] - 5 < enemy.position[0] < point[0] + 5 and point[1] - 5 < enemy.position[1] < point[1] + 5:
                            enemy.properties["pointID"] += 1
                            if enemy.properties["pointID"] >= len(enemy.properties["patrolling"].split()):
                                enemy.properties["pointID"] = 0
                            point = [int(i) * self.scaling for i in enemy.properties["patrolling"].split()[enemy.properties["pointID"]].split(",")]
                            if enemy.center_x > point[0]:
                                left = -1
                            else:
                                left = 1
                            if enemy.center_y > point[1]:
                                down = -1
                            else:
                                down = 1
                            enemy.change_x = left * abs(enemy.center_x - point[0]) / (on_range(enemy.center_x, enemy.center_y, point[0], point[1]) / (enemy.properties["movespeed"] * 0.8)) / 1.5 * self.scaling 
                            enemy.change_y = down * abs(enemy.center_y - point[1]) / (on_range(enemy.center_x, enemy.center_y, point[0], point[1]) / (enemy.properties["movespeed"] * 0.8)) / 1.5 * self.scaling 
                    else:
                        enemy.change_x = 0
                        enemy.change_y = 0

                #движение союзников к врагам
                elif enemy.properties["movement"] == "simple" and "friendly" in enemy.properties["mods"].split() and enemy.properties["opponent"] != 0:
                    range_to_player = on_range(enemy.center_x, enemy.center_y, enemy.properties["opponent"].center_x, enemy.properties["opponent"].center_y)
                    if enemy.center_x > enemy.properties["opponent"].center_x:
                        left = -1
                    else:
                        left = 1
                    if enemy.center_y > enemy.properties["opponent"].center_y:
                        down = -1
                    else:
                        down = 1
                    if range_to_player != 0:
                        enemy.change_x = left * abs(enemy.center_x - enemy.properties["opponent"].center_x) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling 
                        enemy.change_y = down * abs(enemy.center_y - enemy.properties["opponent"].center_y) / (range_to_player / enemy.properties["movespeed"]) / 1.5 * self.scaling

                #перемещение врагов    
                if "feared" not in enemy.properties["mods"].split():
                    enemy.center_x += enemy.change_x * ((60 * delta_time) % 4)
                    if arcade.check_for_collision_with_list(enemy, self.wall_list):
                        enemy.center_x -= enemy.change_x * ((60 * delta_time) % 4)
                        if enemy.properties["movement"] == "jerker":
                            enemy.properties["range"] = 0
                            enemy.properties["lastjerk"] = self.timer
                            enemy.change_x = 0
                            enemy.change_y = 0
                        if "shot" in enemy.properties["mods"].split():
                            self.kill_enemy(enemy)
                    enemy.center_y += enemy.change_y * ((60 * delta_time) % 4)
                    if arcade.check_for_collision_with_list(enemy, self.wall_list):
                        enemy.center_y -= enemy.change_y * ((60 * delta_time) % 4)
                        if enemy.properties["movement"] == "jerker":
                            enemy.properties["range"] = 0
                            enemy.properties["lastjerk"] = self.timer
                            enemy.change_x = 0
                            enemy.change_y = 0
                        if "shot" in enemy.properties["mods"].split():
                            self.kill_enemy(enemy)
                    if enemy.properties["movement"] == "jerker" and enemy.change_x != 0 and enemy.change_y != 0:
                        enemy.properties["range"] -= abs(enemy.change_x) + abs(enemy.change_y)
                        if enemy.properties["range"] <= 0:
                            enemy.properties["lastjerk"] = self.timer
                            enemy.change_x = 0
                            enemy.change_y = 0
                #...если испуганы
                else:
                    enemy.center_x -= enemy.change_x * ((60 * delta_time) % 4)
                    if arcade.check_for_collision_with_list(enemy, self.wall_list):
                        enemy.center_x += enemy.change_x * ((60 * delta_time) % 4)
                    enemy.center_y -= enemy.change_y * ((60 * delta_time) % 4)
                    if arcade.check_for_collision_with_list(enemy, self.wall_list):
                        enemy.center_y += enemy.change_y * ((60 * delta_time) % 4)

                #обновление вражеских снарядов
                if "shot_2" in enemy.properties["mods"].split():
                    enemy.forward(-2*self.scaling)
                if "shot" in enemy.properties["mods"].split():
                    enemy.properties["range"] -= abs(enemy.change_x + enemy.change_y)
                if "shot" in enemy.properties["mods"].split() and (arcade.check_for_collision_with_list(enemy, self.wall_list) or enemy.properties["range"] <= 0):
                    self.kill_enemy(enemy)
                if "attack" in enemy.properties["mods"].split() and self.timer - enemy.properties["attackat"] > 1:
                    self.kill_enemy(enemy)

                #управление могилой
                if "summoner" in enemy.properties["mods"].split() and self.timer - enemy.properties["summonat"] > 10 and len([i for i in self.scene.get_sprite_list("enemies") if "summoned" in i.properties["mods"].split()]) < 5 and ((("effects" in enemy.properties.keys()) and ("stun" not in enemy.properties["effects"].keys())) or ("effects" not in enemy.properties.keys())):
                    enemy.properties["summonat"] = self.timer
                    enemy.properties["hitpoints"] -= 2
                    boner = generate_sprite(self.textures.get_sprite_list("textures")[20], enemy.center_x + randrange(-45, 45, 1) * self.scaling, enemy.center_y + randrange(-45, 45, 1) * self.scaling, self.scaling)
                    boner.properties["content"] = "1coin/t:7#bin_chest:True#bin_inventory:False#"
                    boner.properties["damage"] = 10
                    boner.properties["hitpoints"] = 25
                    boner.properties["max_hitpoints"] = 25
                    boner.properties["mods"] = "summoned"
                    boner.properties["movement"] = "simple"
                    boner.properties["movespeed"] = 1.05
                    boner.properties["vision"] = 120
                    boner.properties["sees_player"] = False
                    boner.properties["effects"] = {}
                    boner.properties["lastreaction"] = self.timer
                    self.spawn_enemy_without_collisions(boner)

                #перерождение
                if "reincarnating" in enemy.properties["mods"].split() and self.timer - enemy.properties["deathat"] > 5:
                    enemy1 = generate_sprite(self.textures.get_sprite_list("textures")[41], enemy.center_x, enemy.center_y, self.scaling*1.2)
                    enemy1.properties = enemy.properties.copy()
                    enemy1.properties["movement"] = "simple"
                    enemy1.properties["hitpoints"] = 90
                    enemy1.properties["mods"] = "reincarnable"
                    self.scene.get_sprite_list("enemies").append(enemy1)
                    enemy.remove_from_sprite_lists()

                #обновление эффектов
                if "effects" in enemy.properties.keys():
                    for effect in enemy.properties["effects"].keys():
                        enemy.properties["effects"][effect] -= delta_time
                        if effect == "burn":
                            enemy.rgb = (255, 114, 0)
                            if int(enemy.properties["effects"][effect]) != int(enemy.properties["effects"][effect] - delta_time):
                                enemy.properties["hitpoints"] -= 3
                            if enemy.properties["hitpoints"] <= 0:
                                self.kill_enemy(enemy)
                        if enemy.properties["effects"][effect] <= 0:
                            enemy.properties["effects"].pop(effect)
                            enemy.rgb = arcade.color.WHITE
                            break

                #управление боссом     
                if "boss" in enemy.properties["mods"].split() and enemy.properties["sees_player"]:
                    #обновление паттерна
                    if self.timer - enemy.properties["lastpatternchange"] > 15 and enemy.properties["Groups_left"] == 0:
                        enemy.properties["lastpatternchange"] = self.timer
                        a = randrange(0, 5, 1)
                        if a == enemy.properties["pattern"]:
                            a = randrange(0, 5, 1)
                        enemy.properties["pattern"] = a
                        if a in [0, 2, 3, 4]:
                            enemy.properties["movement"] = "simple"
                        elif a == 1:
                            enemy.properties["movement"] = "jerker"
                            enemy.properties["lastjerk"] = self.timer
                        if a in [0, 1]:
                            enemy.properties["movespeed"] = 1.1
                        elif a in [2, 3, 4]:
                            enemy.properties["movespeed"] = 0.2
                        if a in [3, 4] and "feared" not in enemy.properties["mods"].split():
                            enemy.properties["mods"] += " feared"
                        elif "feared" in enemy.properties["mods"].split():
                            w = enemy.properties["mods"].split()
                            w.remove("feared")
                            enemy.properties["mods"] = str(w).replace(", ", " ")[1:-1]
                        if a in [3, 4]:
                            enemy.properties["Groups_left"] = 5
                    #обновление полосы здоровья
                    self.boss_hp.scale_x = 60*self.scaling*enemy.properties["hitpoints"]/enemy.properties["max_hitpoints"]
                    self.boss_hp.left = 64*self.scaling
                    #паттерны поведения
                    #выстрелы
                    if enemy.properties["pattern"] == 2 and self.timer - enemy.properties["lastshotat"] > 1.5:
                        enemy.properties["lastshotat"] = self.timer
                        n = randrange(3, 6, 1)
                        for i in range(n):
                            shot = generate_sprite(self.textures.get_sprite_list("textures")[23], enemy.center_x, enemy.center_y, self.scaling)
                            shot.properties["damage"] = enemy.properties["damage"]
                            shot.properties["range"] = 1
                            shot.properties["mods"] = "untouchable shot shot_2"
                            shot.properties["content"] = ""
                            shot.angle = ((math.atan((self.player_sprite.center_x - enemy.center_x) / (self.player_sprite.center_y - enemy.center_y)) * 180 / 3.14) - 30 + i * 60 / (n-1)) * (self.player_sprite.center_y <= enemy.center_y) 
                            shot.angle += (180 + ((math.atan((self.player_sprite.center_x - enemy.center_x) / (self.player_sprite.center_y - enemy.center_y)) * 180 / 3.14) - 30 + i * 60 / (n-1))) * (self.player_sprite.center_y > enemy.center_y)
                            shot.properties["movement"] = "line"
                            shot.change_x = 0
                            shot.change_y = 0
                            self.scene.get_sprite_list("enemies").append(shot)
                    #призыв
                    if enemy.properties["pattern"] in [3, 4] and [i for i in self.scene.get_sprite_list("enemies") if "summoned" in i.properties["mods"].split()] == []:
                        enemy.properties["Groups_left"] -= 1
                        n = randrange(0, 5, 1)
                        for index, i in enumerate(self.enemy_groups.get_sprite_list(str(n))):
                            summon = arcade.Sprite()
                            summon.properties = i.properties.copy()
                            summon.texture = i.texture
                            summon.properties["effects"] = {}
                            summon.properties["mods"] += " summoned"
                            summon.properties["sees_player"] = True
                            summon.properties["vision"] = enemy.properties["vision"]
                            summon.scale = self.scaling
                            summon.center_x = enemy.center_x + index * 20 * self.scaling
                            summon.center_y = enemy.center_y
                            self.spawn_enemy_without_collisions(summon)
    
            #подбор пикапов
            pickup_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("pickups"))
            if pickup_hit != [] and self.todo and not (pickup_hit[0].properties["in_inventory"] or pickup_hit[0].properties["in_chest"]) and not(arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("enemies"))):
                if not "price" in pickup_hit[0].properties or [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "coin" and i.properties["count"] >= pickup_hit[0].properties["price"]] != []:
                    if pickup_hit[0].properties["type"] in inventory and self.inventory[inventory.index(pickup_hit[0].properties["type"])].properties["content"].properties["count"] < pickup_hit[0].properties["max_count"]:
                        self.inventory[inventory.index(pickup_hit[0].properties["type"])].properties["content"].properties["count"] += pickup_hit[0].properties["count"]
                        if self.inventory[inventory.index(pickup_hit[0].properties["type"])].properties["content"].properties["count"] > pickup_hit[0].properties["max_count"]:
                            self.inventory[inventory.index(pickup_hit[0].properties["type"])].properties["content"].properties["count"] = pickup_hit[0].properties["max_count"]
                        pickup_hit[0].remove_from_sprite_lists()
                    elif 0 in inventory:
                        self.inventory[inventory.index(0)].properties["content"] = pickup_hit[0]
                        pickup_hit[0].position = self.inventory[inventory.index(0)].position
                        pickup_hit[0].scale = 1.5
                        pickup_hit[0].properties["in_inventory"] = True
                    self.stat_update()
                    print(self.decode_item(pickup_hit[0], reverse=True))
                    arcade.load_sound(ASSETS_PATH / "sounds/pickup1.mp3").play()
                    if "price" in pickup_hit[0].properties:
                        arcade.load_sound(ASSETS_PATH / "sounds/pay1.mp3").play()
                        [i for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["type"] == "coin" and i.properties["count"] >= pickup_hit[0].properties["price"]][0].properties["count"] -= pickup_hit[0].properties["price"]
                        [i.remove_from_sprite_lists() for i in [i.properties["content"] for i in self.inventory if i.properties["content"] != 0] if i.properties["count"] <= 0]
                        for i in self.inventory:
                            if i.properties["content"] != 0 and i.properties["content"].properties["count"] <= 0:
                                i.properties["content"] = 0
                        for i in self.price_texts:
                            flag = False
                            for f in [y for y in self.scene.get_sprite_list("pickups") if "price" in y.properties.keys()]:
                                if on_range(i.x, i.y, f.center_x, f.center_y) <= 12 * self.scaling:
                                    flag = True
                            if not flag:
                                i.text = ""

            #открытие сундука
            chest_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene.get_sprite_list("chests"))
            if len(self.in_chest) == 0 and self.todo:
                if chest_hit != [] and "mimic" not in chest_hit[0].properties.keys() and chest_hit[0].properties["locked"] and [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "key":
                    chest_hit[0].properties["locked"] = False
                    [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] += -1
                    if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"] <= 0:
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"].remove_from_sprite_lists() 
                        [i for i in self.inventory if i.properties["selected"]][0].properties["content"] = 0
                elif (chest_hit != [] and "mimic" not in chest_hit[0].properties.keys() and not chest_hit[0].properties["locked"] or ([i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0 and [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "bag")):
                    if chest_hit != []:
                        self.opened_chest = chest_hit[0]            
                    else:
                        self.opened_chest = [i for i in self.inventory if i.properties["selected"]][0].properties["content"]
                    for i in range(self.opened_chest.properties["slots"]):
                        chest_part = generate_sprite(self.textures.get_sprite_list("textures")[1], 50 + i % 10 * 30, (SCREEN_HEIGHT - 30) - i // 10 * 30, 1.5)
                        chest_part.properties["selected"] = False
                        if i + 1 > len(self.opened_chest.properties["content"].split()):
                            chest_part.properties["content"] = 0
                        else:
                            chest_content = self.decode_item(self.opened_chest.properties["content"].split()[i])
                            chest_content.position = chest_part.position
                            self.scene.get_sprite_list("pickups").append(chest_content)
                            chest_part.properties["content"] = chest_content
                        self.in_chest.append(chest_part)
                    self.in_chest[0].properties["selected"] = True
                elif chest_hit != [] and "mimic" in chest_hit[0].properties.keys():
                    mimic = arcade.Sprite()
                    mimic.texture = chest_hit[0].texture
                    mimic.center_x = chest_hit[0].center_x
                    mimic.center_y = chest_hit[0].center_y + 10*self.scaling
                    mimic.properties["content"] = chest_hit[0].properties["content"]
                    mimic.properties["movement"] = "simple"
                    mimic.properties["movespeed"] = 1.1
                    mimic.properties["hitpoints"] = 150
                    mimic.properties["max_hitpoints"] = 150
                    mimic.properties["damage"] = 20
                    mimic.properties["mods"] = ""
                    mimic.properties["sees_player"] = True
                    mimic.properties["vision"] = 100
                    mimic.rgb = (255, 0, 0)
                    mimic.scale = self.scaling * 1.1
                    chest_hit[0].remove_from_sprite_lists()
                    self.scene.get_sprite_list("enemies").append(mimic)
            #закрытие сундука        
            if self.enter_pressed and len(self.in_chest) > 0:
                content = ""
                for i in [i.properties["content"] for i in self.in_chest if i.properties["content"] != 0]:
                    content += self.decode_item(i, reverse=True) + " "
                if "delete" not in self.opened_chest.properties.keys() or len(content.split()) > 0:
                    self.opened_chest.properties["content"] = content
                else:
                    self.opened_chest.remove_from_sprite_lists()
                for i in [i for i in self.scene.get_sprite_list("pickups") if i.properties["in_chest"]]:
                    i.remove_from_sprite_lists()
                self.in_chest.clear() 

            #остывание игрока
            if self.player_sprite.properties["rageat"] + 5 < self.timer and self.player_sprite.rgb == (255, 0, 0):
                self.player_sprite.rgb = arcade.color.WHITE
                self.bonus_stats["strength"] -= 0.3
                self.bonus_stats["movespeed"] -= 0.3
                
            #обновление всех текстов
            self.hp_text.text = str(self.player_sprite.properties["hitpoints"])
            if [i for i in self.inventory if i.properties["selected"]][0].properties["content"] != 0:
                if "name" in [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties.keys():
                    self.selected_inv_text.text = (str([i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"]) + " " + [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["name"]).replace("_", " ")
                else:
                    self.selected_inv_text.text = (str([i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["count"]) + " " + [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"]).replace("_", " ")
                if [i for i in self.inventory if i.properties["selected"]][0].properties["content"].properties["type"] == "staff":
                    q = [i for i in self.inventory if i.properties["selected"]][0].properties["content"]
                    if q.properties["lastcast"] + q.properties["qldown"] > self.timer:
                        self.selected_inv_text.text += " " + str(round(q.properties["qldown"] - self.timer + q.properties["lastcast"], 1))
            else:
                self.selected_inv_text.text = ""
            if self.timer - self.damage_text_update_time > 0.5 and self.damage_text.text != "":
                self.damage_text.text = ""
            if self.timer - self.minus_hp_update_time > 0.5 and self.minus_hp_text.text != "":
                self.minus_hp_text.text = ""
        
        if self.Gameover and len(self.scene.get_sprite_list("enemies")) != 0:
            self.Gameover_text.text = "Game over!"
        elif self.Gameover:
            self.Gameover_text.text = "You win!"
            self.boss_hp.scale = 0    

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)
    game = GameView()
    game.setup()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main() 