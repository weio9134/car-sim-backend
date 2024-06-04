import math
import sys
import neat
import pygame


CAR_X = 25
CAR_Y = 25

BORDER = (255, 255, 255, 255)

current_generation = 0 

ARRAY = [
   [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
   [0, 2, 0, 0, 0, 0, 0, 0, 1, 0],
   [0, 1, 0, 0, 1, 1, 1, 0, 1, 0],
   [1, 1, 0, 0, 1, 0, 1, 0, 1, 0],
   [1, 0, 1, 1, 1, 0, 1, 0, 1, 0],
   [1, 1, 1, 0, 0, 0, 1, 1, 1, 0],
   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
   [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

CELL_SIZE = 65
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 0)
GREEN = (0, 255, 0, 0)

# get coordinate of green tile
def get_start(array):
  for y, row in enumerate(array):
     for x, cell in enumerate(row):
        if cell == 2:
           return [x * CELL_SIZE, y * CELL_SIZE]


START = get_start(ARRAY)
ARRAY_WIDTH = CELL_SIZE * len(ARRAY[0])
ARRAY_HEIGHT =  CELL_SIZE * len(ARRAY)



class Car:
  # make car object
  def __init__(self):
    # load car sprite and ready rotated version
    self.sprite = pygame.image.load('car.png').convert() # Convert Speeds Up A Lot
    self.sprite = pygame.transform.scale(self.sprite, (CAR_X, CAR_Y))
    self.rotated_sprite = self.sprite 

    # load startin position, angle, speed
    self.position = START.copy()
    self.angle = 0
    self.speed = 2

    # set car center
    self.center = [self.position[0] + CAR_X / 2, self.position[1] + CAR_Y / 2] # Calculate Center

    # set radars to draw, radar: [(x, y), length]
    self.radars = []
    self.drawing_radars = []

    self.alive = True

    # set distance traveled and time passed
    self.distance = 0 
    self.past_positions = []
    self.time = 0

  
  # draw car
  def draw(self, screen):
    screen.blit(self.rotated_sprite, self.position)
    self.draw_radar(screen)

  # draw the radars for probe
  def draw_radar(self, screen):
    # Optionally Draw All Sensors / Radars
    for radar in self.radars:
      position = radar[0]
      pygame.draw.line(screen, (0, 255, 0), self.center, position, 1)
      pygame.draw.circle(screen, (0, 255, 0), position, 5)


  # check if crashed
  def check_collision(self, game_map):
    self.alive = True
    for point in self.corners:
      # if any corner is a border on the map, it crashed
    #   print(point, game_map.get_width(), game_map.get_height())
      if game_map.get_at((int(point[0]), int(point[1]))) == BORDER:
          self.alive = False
          break


  # update radars to draw
  def check_radar(self, degree, game_map):
    length = 0
    x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
    y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

    # while the radars dont touch the border and within 300 length
    while (0 <= x < ARRAY_WIDTH) and (0 <= y < ARRAY_HEIGHT) and (game_map.get_at((x, y)) != BORDER) and (length < 300):
        # print(x, y, game_map.get_width(), game_map.get_height())
        length = length + 1
        x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
        y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

    # calc radar length from center to its end
    dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
    self.radars.append([(x, y), dist])
  

  # update all car info
  def update(self, game_map):
    # rotate the sprite based on angle
    self.rotated_sprite = self.rotate_center(self.sprite, self.angle)
    
    # record past positions
    self.past_positions.append(self.position.copy())
    if len(self.past_positions) > 10:
        self.past_positions.pop(0)

    # update new x y position
    self.position[0] += math.cos(math.radians(360 - self.angle)) * self.speed
    self.position[0] = max(self.position[0], 20)
    self.position[0] = min(self.position[0], ARRAY_WIDTH - 120)

    self.position[1] += math.sin(math.radians(360 - self.angle)) * self.speed
    self.position[1] = max(self.position[1], 20)
    self.position[1] = min(self.position[1], ARRAY_WIDTH - 120)

    # increase time and speed
    self.distance += self.speed
    self.time += 1
    
    # get new center
    self.center = [int(self.position[0]) + CAR_X / 2, int(self.position[1]) + CAR_Y / 2]

    # get car corner to check for collision
    length = 0.5 * CAR_X
    left_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 30))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 30))) * length]
    right_top = [self.center[0] + math.cos(math.radians(360 - (self.angle + 150))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 150))) * length]
    left_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 210))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 210))) * length]
    right_bottom = [self.center[0] + math.cos(math.radians(360 - (self.angle + 330))) * length, self.center[1] + math.sin(math.radians(360 - (self.angle + 330))) * length]
    self.corners = [left_top, right_top, left_bottom, right_bottom]

    # check collision
    self.check_collision(game_map)
    self.radars.clear()

    # get new radar from -90 to 90 with 45 gap
    for d in range(-90, 100, 45):
        self.check_radar(d, game_map)


  # get dist info from radar
  def get_data(self):
    # get dist from radar
    radars = self.radars
    vals = [0, 0, 0, 0, 0]
    for i, radar in enumerate(radars):
        vals[i] = radar[1]
    return vals  


  # check if car has been progressing along the track
  def check_progress(self):
    if len(self.past_positions) >= 5:
        total_distance = 0
        for i in range(len(self.past_positions) - 1):
            distance = math.sqrt((self.past_positions[i+1][0] - self.past_positions[i][0])**2 +
                                    (self.past_positions[i+1][1] - self.past_positions[i][1])**2)
            total_distance += distance

        # print("TOTAL", total_distance / (len(self.past_positions) - 1), self.position, self.speed)
        return total_distance / (len(self.past_positions) - 1) >= 1
    
    return True
     
  
  # reward the NN model
  def get_reward(self):
    reward = self.distance * self.time
    return reward if self.check_progress() else -reward


  # rotate sprite
  def rotate_center(self, image, angle):
    # get rect area of car
    rectangle = image.get_rect()
    # rotate sprite
    rotated_image = pygame.transform.rotate(image, angle)
    # copy it all over
    rotated_rectangle = rectangle.copy()
    rotated_rectangle.center = rotated_image.get_rect().center
    rotated_image = rotated_image.subsurface(rotated_rectangle).copy()
    return rotated_image



# create map from array
def create_map_surface():
    map_surface = pygame.Surface((ARRAY_WIDTH, ARRAY_HEIGHT))
    map_surface.fill(WHITE)
    for y in range(len(ARRAY)):
        for x in range(len(ARRAY[0])):
            if ARRAY[y][x] == 0:
                color = WHITE
            elif ARRAY[y][x] == 1:
                color = BLACK # road
            elif ARRAY[y][x] == 2:
                color = GREEN # start
            pygame.draw.rect(map_surface, color, pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    return map_surface



# run a simulation turn
def run_simulation(genomes, config):    
    # init game and display
    pygame.init()
    screen = pygame.display.set_mode((ARRAY_WIDTH, ARRAY_HEIGHT))

    # for all genomes passed make a new NN
    nets = []
    cars = []
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0
        cars.append(Car())

    # set up clock and map
    clock = pygame.time.Clock()
    game_map = create_map_surface()

    global current_generation
    current_generation += 1

    # counter to limit time
    counter = 0
    while True: 
        # pygame exit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        # update each car's action
        for i, car in enumerate(cars):
            data = car.get_data()
            output = nets[i].activate(data)
            choice = output.index(max(output))
            # print(output, choice)

            if choice == 0:
                car.angle += 10 # Left
            elif choice == 1:
                car.angle -= 10 # Right
            elif choice == 2:
                if car.speed > 12:
                    car.speed -= 2 # Slow Down
            else:
                car.speed = min(12, car.speed + 2) # Speed Up
                
        # check if any cars are alive
        still_alive = 0
        for i, car in enumerate(cars):
            if car.alive:
                reward = car.get_reward()
                if reward < -15000:
                   car.alive = False
                   continue
                
                reward = min(reward, 100 + reward / 100)
                # print("REWARD", car.id, car.position, reward, car.check_progress())

                still_alive += 1
                car.update(game_map)
                genomes[i][1].fitness += reward

        if still_alive == 0:
            break

        counter += 1
        if counter == 30 * 40:
            break

        # redraw map and cars
        screen.fill(WHITE)
        screen.blit(game_map, (0, 0))

        for car in cars:
          if car.alive:
            car.draw(screen)

        pygame.display.flip()
        clock.tick(60) # 60 FPS
        
        # TESTING
        # x = input()
        # if(x == "q"):
        #    sys.exit(0)



# start simulation
def simulate(array):
  # set up config
  config_path = "./config.txt"
  config = neat.config.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              config_path)

  # create population
  population = neat.Population(config)
  population.add_reporter(neat.StdOutReporter(True))
  stats = neat.StatisticsReporter()
  population.add_reporter(stats)
  
  # rin sim for some gens
  population.run(run_simulation, 10)
