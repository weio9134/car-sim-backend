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
        

# 1: call to initialize population and settings to simulate
@app.route("/settings", methods=["POST"])
def get_settings():
    # get data sent from client
    data = request.get_json()
    board = data.get('board')
    gen = data.get('gen')

    # store all data
    game_states['board'] = board
    game_states['start'] = get_start(board)
    game_states['gen'] = gen
    game_states["population"] = get_population()
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
    
    # store updated data
    print(nets, cars, genomes)
    game_states["nets"] = nets
    game_states["cars"] = cars
    game_states["genomes"] = genomes
    
    # return car data to display on frontend
    data = [{
        "id": car.id,
        "position": car.position,
        "angle": car.angle,
        "center": car.center,
        "alive": car.alive,
        "radars": car.radar if hasattr(car, 'radar') else []
    } for car in cars] if cars != None else []

    # print(data)
    return jsonify({
        "message": "PASSED FRAME", 
        "gen": game_states['gen'], 
        "cars": data
    })


# 4: call to save population info so next gen is smarter, repeat from 2
@app.route("/update_population")
def update():
    pop = save_gen_info(population=game_states["population"])
    game_states["population"] = pop
    return jsonify({"message": "POPULATION UPDATED"})


@app.route("/test")
def testing():
    test()
    return jsonify({"message": "FINISHED TESTING"})


if __name__ == '__main__':
    app.run(debug=True)