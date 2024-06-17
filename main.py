import json
import logging
import numpy as np
from collections import namedtuple
from enum import Enum
import os.path

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Визначення ігрової карти та характеристик
MapCell = namedtuple('MapCell', ['type', 'color'])
MapCellType = Enum('MapCellType', 'EMPTY WALL FIRE START FINISH KEY HEART')
MapCellColor = Enum('MapCellColor', 'ORANGE WHITE')
WallMapCell = MapCell(MapCellType.WALL, MapCellColor.WHITE)
EmptyMapCell = MapCell(MapCellType.EMPTY, MapCellColor.WHITE)
class Hero:
    def __init__(self, name, x, y):
        self.name = name
        self.health = 5
        self.actions = 1
        self.x = x
        self.y = y
        self.heals_left = 3
        self.has_key = False
        self.previous_position = None
        self.ignore_previous_position = False

    def move(self, dx, dy, game_map):
        new_x = self.x + dx
        new_y = self.y + dy
        if new_x < 0 or new_x >= len(game_map) or new_y < 0 or new_y >= len(game_map[0]):
            self.health -= 1
            logging.info(f'{self.name} вдарився об стіну і втратив одне очко життя. залишилось {self.health} очок життя')
            return False
        if game_map[new_x][new_y].type == MapCellType.WALL:
            self.health -= 1
            logging.info(f'{self.name} вдарився об стіну і втратив одне очко життя. залишилось {self.health} очок життя')
            return False
        if (new_x, new_y) == self.previous_position and not self.ignore_previous_position:
            logging.info(f'{self.name} злякався і втік.')
            self.health = 0
            if self.has_key:
                game_map[self.x][self.y].type = MapCellType.KEY
            return False
        self.ignore_previous_position = False
        if not self.ignore_previous_position:
            self.previous_position = (self.x, self.y)
        self.x = new_x
        self.y = new_y
        return self.resolve_cell(game_map)

    def resolve_cell(self, game_map):
        cell = game_map[self.x][self.y]
        if cell.type == MapCellType.FIRE:
            self.health -= 1
            logging.info(f'{self.name} наступив на вогонь і втратив одне очко життя. залишилось {self.health} очок життя')
        elif cell.type == MapCellType.HEART:
            logging.info(f'{self.name} отримав лікування.')
            self.health = 5
            self.ignore_previous_position = True
        elif cell.color == MapCellColor.ORANGE:

            self.ignore_previous_position = True

        elif cell.type == MapCellType.FINISH:
            if self.has_key:
                return True
            else:
                logging.info(f'{self.name} загинув від Голема.')
                self.health = 0
        return False

    def heal(self):
        if self.heals_left > 0:
            self.health = min(5, self.health + 1)
            self.heals_left -= 1
            logging.info(f'{self.name} лікувався, тепер у нього {self.health} очок життя.')
        else:
            logging.info(f'У {self.name} більше немає зарядів для лікування.')

    def attack(self, heroes):
        for hero in heroes:
            if hero != self and hero.x == self.x and hero.y == self.y:
                hero.health -= 1
                logging.info(f'{self.name} атакував {hero.name}, тепер у {hero.name} {hero.health} очок життя.')




#   (   ) (   ) (   ) (   ) (0,4) (0,5) (0,6) (0,7)
#   (   ) (   ) (1,2) (   ) (   ) (1,5) (   ) (   )
#   (   ) (2,1) (2,2) (2,3) (   ) (2,5) (2,6) (   )
#   (3,0) (3,1) (   ) (3,3) (3,4) (3,5) (   ) (   )
def create_game_map():
    game_map = [
        [WallMapCell, WallMapCell, WallMapCell, WallMapCell, MapCell(MapCellType.HEART, MapCellColor.ORANGE), EmptyMapCell, EmptyMapCell, MapCell(MapCellType.FINISH, MapCellColor.WHITE)],
        [WallMapCell, WallMapCell, MapCell(MapCellType.KEY, MapCellColor.ORANGE), WallMapCell, WallMapCell, EmptyMapCell, WallMapCell, WallMapCell],
        [WallMapCell, EmptyMapCell, EmptyMapCell, EmptyMapCell, WallMapCell, EmptyMapCell, MapCell(MapCellType.HEART, MapCellColor.ORANGE), WallMapCell],
        [MapCell(MapCellType.START,MapCellColor.WHITE), EmptyMapCell, WallMapCell, EmptyMapCell, EmptyMapCell, EmptyMapCell, WallMapCell, WallMapCell],
    ]
    return game_map

def add_fire_cells(game_map):
    clear_fire_cells(game_map)
    empty_cells = [(i, j) for i in range(len(game_map)) for j in range(len(game_map[0])) if game_map[i][j].type == MapCellType.EMPTY]
    num_fire_cells = min(4, len(empty_cells))
    fire_indices = np.random.choice(len(empty_cells), num_fire_cells, replace=False)
    fire_cells = [empty_cells[idx] for idx in fire_indices]
    for (i, j) in fire_cells:
        game_map[i][j] = MapCell(MapCellType.FIRE, MapCellColor.WHITE)
    logging.info(f'Вогонь на клітинах: {fire_cells}')
    return fire_cells

def clear_fire_cells(game_map):
    fire_cells = [(i, j) for i in range(len(game_map)) for j in range(len(game_map[0])) if
                   game_map[i][j].type == MapCellType.FIRE]
    for (i, j) in fire_cells:
        game_map[i][j] = MapCell(MapCellType.EMPTY, MapCellColor.WHITE)
    return


def load_game(filename="savegame.json"):
    with open(filename, 'r') as f:
        state = json.load(f)

    heroes = [Hero(h['name'], h['x'], h['y']) for h in state['heroes']]

    game_map = []
    for row in state['game_map']:
        map_row = []
        for cell_data in row:
            cell_type = MapCellType[cell_data['type']]
            cell_color = MapCellColor[cell_data['color']]
            cell = MapCell(cell_type, cell_color)
            map_row.append(cell)
        game_map.append(map_row)

    return heroes, game_map


def save_game(heroes, game_map, filename="savegame.json"):
    state = {
        'heroes': [{'name': hero.name, 'x': hero.x, 'y': hero.y} for hero in heroes],
        'game_map': [[{'type': cell.type.name,
                       'color': cell.color.name} for cell in row] for row in game_map]
    }
    with open(filename, 'w') as f:
        json.dump(state, f)

    logging.info('Гру збережено.')
def game():

    # Перевірка наявності збереженої гри
    try:
        with open('savegame.json', 'r') as f:
            pass
        load_existing = input('Є збережена гра. Завантажити її? (так/ні): ').strip().lower()
        if load_existing == 'так':
            if os.path.isfile('savegame.json'):
                heroes, game_map = load_game()
        else:
            raise FileNotFoundError
    except (FileNotFoundError, json.JSONDecodeError):
        num_heroes = int(input('Введіть кількість героїв: '))
        heroes = [Hero(input(f'Введіть ім\'я героя {i + 1}: '), 3, 0) for i in range(num_heroes)]
        game_map = create_game_map()
    available_movement = ['вгору', 'вниз', 'вліво', 'вправо', 'лікуватися', 'вдарити мечем', 'підібрати ключ']
    while True:
        fire_cells = add_fire_cells(game_map)
        for hero in heroes[:]:
            if hero.health <= 0:
                logging.info(f'{hero.name} загинув.')
                if hero.has_key == True:
                    color = game_map[hero.x][hero.y].color
                    game_map[hero.x][hero.y] = MapCell(MapCellType.KEY, color)
                    logging.info(f'ключ на клітині {hero.x, hero.y}')
                heroes.remove(hero)
                continue
            while True:
                action = input(f'{hero.name}, ваш хід (вгору, вниз, вліво, вправо, лікуватися, вдарити мечем, підібрати ключ): ').strip().lower()
                if action in available_movement:
                    break
                logging.info('Невідома дія, спробуйте знову.')

            if action == 'вгору':
                if not hero.move(-1, 0, game_map):
                    continue
            elif action == 'вниз':
                if not hero.move(1, 0, game_map):
                    continue
            elif action == 'вліво':
                if not hero.move(0, -1, game_map):
                    continue
            elif action == 'вправо':
                if not hero.move(0, 1, game_map):
                    continue
            elif action == 'лікуватися':
                hero.heal()
                continue
            elif action == 'вдарити мечем':
                hero.attack(heroes)
                continue
            elif action == 'підібрати ключ':
                if game_map[hero.x][hero.y].type == MapCellType.KEY:
                    logging.info(f'{hero.name} підібрав ключ.')
                    hero.has_key = True
                    game_map[hero.x][hero.y] = MapCell(MapCellType.EMPTY, MapCellColor.ORANGE)
                else:
                    logging.info(f'На цій клітині немає ключа.')
                continue


            if hero.resolve_cell(game_map):
                logging.info(f'Гра закінчена, {hero.name} переміг!')
                return


        if not heroes:
            logging.info('Всі герої загинули. Гра закінчена.')
            break

        save_game(heroes, game_map)

if __name__ == "__main__":
    game()