import math
import neat


# car size
CAR_X = 40
CAR_Y = 18

# map sizes
CELL_SIZE = 60
ARRAY_WIDTH = CELL_SIZE * 10
ARRAY_HEIGHT =  CELL_SIZE * 10


class Car:
  # make car object  
  def __init__(self, id, start):
    self.id = id
    # load startin position, angle, speed
    self.position = start.copy()
    self.angle = 0
    self.speed = 2

    # set car center
    self.center = [self.position[0] + (CELL_SIZE - CAR_X) / 2, self.position[1] + (CELL_SIZE - CAR_Y)/ 2] # Calculate Center

    # set radars to draw, radar: [(x, y), length]
    self.radars = []
    self.drawing_radars = []

    self.alive = True

    # set distance traveled and time passed
    self.distance = 0 
    self.past_positions = []
    self.time = 0

  
  # update all car info
  def update(self):
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

        return total_distance / (len(self.past_positions) - 1) >= 1
    
    return True
     
  
  # reward the NN model
  def get_reward(self):
    reward = self.distance * self.time
    return reward if self.check_progress() else -reward



# get initial population
def get_population():
   # config for population sim
  config_path = "./config.txt"
  config = neat.config.Config(neat.DefaultGenome,
                              neat.DefaultReproduction,
                              neat.DefaultSpeciesSet,
                              neat.DefaultStagnation,
                              config_path)
  population = neat.Population(config)
  return population


# reset genome and cars
def get_new_genomes(population, start):
    nets = []
    cars = []
    genomes = list(population.population.items())
    pc = population.config
    
    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, pc)
        nets.append(net)
        g.fitness = 0
        cars.append(Car(i, start))
    
    return nets, cars, genomes


# save info for next gen to learn
def save_gen_info(population):
  # Gather and report statistics.
  best = None
  for g in population.population.values():
      if g.fitness is None:
          raise RuntimeError("Fitness not assigned to genome {}".format(g.key))

      if best is None or g.fitness > best.fitness:
          best = g

  # Track the best genome ever seen.
  if population.best_genome is None or best.fitness > population.best_genome.fitness:
      population.best_genome = best

  if not population.config.no_fitness_termination:
      # End if the fitness threshold is reached.
      fv = population.fitness_criterion(g.fitness for g in population.population.values())
      if fv >= population.config.fitness_threshold:
          population.reporters.found_solution(population.config, population.generation, best)
          return

  # Create the next generation from the current generation.
  population.population = population.reproduction.reproduce(population.config, population.species,
                                                population.config.pop_size, population.generation)

  # Check for complete extinction.
  if not population.species.species:
      population.reporters.complete_extinction()

      # If requested by the user, create a completely new population,
      # otherwise raise an exception.
      if population.config.reset_on_extinction:
          population.population = population.reproduction.create_new(population.config.genome_type,
                                                          population.config.genome_config,
                                                          population.config.pop_size)
      else:
          return

  # Divide the new population into species.
  population.species.speciate(population.config, population.population, population.generation)
  population.reporters.end_generation(population.config, population.population, population.species)
  population.generation += 1
  
  return population


# run one simulation generation turn and return data from one frame
def run_simulation_frame(nets, cars, genomes):
    # update each car's action
    for i, car in enumerate(cars):
        data = car.get_data()
        output = nets[i].activate(data)
        choice = output.index(max(output))

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
            still_alive += 1
            genomes[i][1].fitness += reward
    
    if still_alive == 0:
        return

    return nets, cars, genomes


# update sim info for each car
def update_sim_info():
    # update car info for alive, radar, and call update
    pass


def test():
   print("TESTING")
   print(START)
   print("FINISHED TESTING")