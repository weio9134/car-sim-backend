from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from simulate_mod import get_population, get_new_genomes, save_gen_info, run_simulation_frame, update_sim_info, test
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
CORS(app)

game_states = {}


# find location of starting green tile
def get_start(array):
  for y, row in enumerate(array):
     for x, cell in enumerate(row):
        if cell == 2:
           return [x * 60, y * 60]


# replace pop_size in config
def mod_config_count(count):
    with open('./config.txt', 'r') as file:
        data = file.readlines()

    # overwrite pop_size
    data[3] = f"pop_size              = {count}\n"

    # write everything back
    with open('./config.txt', 'w') as file:
        file.writelines(data)


# 1: call to initialize population and settings to simulate
@app.route("/settings", methods=["POST"])
def get_settings():
    # get data sent from client
    data = request.get_json()
    board = data.get('board')
    gen = data.get('gen')

    # mod config to set car count
    count = data.get('count')
    mod_config_count(count)

    # store all data
    game_states['board'] = board
    game_states['start'] = get_start(board)
    game_states['gen'] = gen
    game_states["population"] = get_population()
    game_states["stop"] = False
    return jsonify({"message": "SETTINGS RECEIVED"})


# 2: call to renew one generation of ai
@app.route("/new_genome", methods=["GET"])
def new_genome():
    # create new set of nets, cars, and genomes
    nets, cars, genomes = get_new_genomes(
                            population=game_states["population"],
                            start=game_states['start'])
    
    # store all data
    game_states["nets"] = nets
    game_states["cars"] = cars
    game_states["genomes"] = genomes
    return jsonify({"message": "UPDATED NEW GENOMES"})


# 3: call to simulate one frame of the ai (at least 1000 frames per gen)
@app.route("/run_frame", methods=["GET"])
def run_frame():
    # run one simulation frame
    nets, cars, genomes = run_simulation_frame(
                                    nets=game_states["nets"], 
                                    cars=game_states["cars"], 
                                    genomes=game_states["genomes"])
    # check if continue
    if cars == None:
        return jsonify({
            "message": "GET NEW POPULTION",
            "gen": game_states['gen'], 
            "cars": [],
            "continue": False
        })

    # store updated data
    game_states["nets"] = nets
    game_states["cars"] = cars
    game_states["genomes"] = genomes
    
    # return car data to display on frontend
    data = [{
        "id": car.id,
        "position": car.position,
        "angle": car.angle % 360,
        "center": car.center,
        "alive": car.alive,
        "radars": car.radar if hasattr(car, 'radar') else [],
        "corners": car.corners if hasattr(car, 'corners') else []
    } if car.alive else None for car in cars] if cars != None else []

    return jsonify({
        "message": "PASSED FRAME", 
        "gen": game_states['gen'], 
        "cars": data,
        "continue": True,
        "stop": game_states["stop"]
    })


# 4: call to update car info, repeat from 3
@app.route("/update_cars", methods=["POST"])
def update_car():
    data = request.get_json()
    new_info = data.get('cars')
    if new_info == []:
        return jsonify({"message": "NOTHING TO UPDATE"})
    
    car_list = game_states["cars"]
    for i, car in enumerate(car_list):
        info = new_info[i]
        if info is None:
            car.alive = False
            continue

        car.alive = info["alive"]
        car.radars = info["radars"]

    return jsonify({"message": "CARS UPDATED"})


# 5: call to save population info so next gen is smarter, repeat from 2
@app.route("/update_population")
def update_pop():
    pop = save_gen_info(population=game_states["population"])
    game_states["population"] = pop
    game_states['gen'] = game_states['gen'] - 1
    return jsonify({
        "message": "POPULATION UPDATED",
        "gen": game_states['gen'],
        "stop": game_states["stop"]
    })


@app.route("/stop")
def stop():
    game_states["stop"] = True
    return jsonify({"message": "STOPPED"})


@app.route("/reset")
def reset():
    game_states["nets"] = None
    game_states["cars"] = None
    game_states["genomes"] = None
    game_states['board'] = None
    game_states['start'] = None
    game_states['gen'] = None
    game_states["population"] = None
    game_states["stop"] = None
    return jsonify({"message": "RESETED"})



@app.route("/test")
def testing():
    test()
    return jsonify({"message": "FINISHED TESTING"})


if __name__ == '__main__':
    app.run(debug=True)