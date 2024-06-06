from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from simulate_mod import get_population, get_new_genomes, save_gen_info, run_simulation_frame, update_sim_info, test
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
CORS(app)

game_states = {}

@app.route("/connect", methods=["GET"])
def connect():
    print("CONNECTED")
    return jsonify({"message": "connected"})


@app.route("/send_message", methods=["POST"])
def get_message():
    data = request.get_json()
    print(data)
    message = data.get('message')
    print("RECEIVED", message)
    return jsonify({"message": f"Message received: {message}"})


@app.route("/start", methods=["POST"])
def start():
   data = request.get_json()
   print(data)
   return jsonify({"message": "started"})


@app.route("/get_state", methods=["GET"])
def get_state():
   data = [i for i in range(10)]
   return jsonify({"data": data})



# 1: call to initialize population to simulate
@app.route("/init_population", methods=["GET"])
def init_pop():
    pop = get_population()
    game_states["population"] = pop
    return jsonify({"message": "INITIALIZED POPULATION"})


# 2: call to renew a generation of ai
@app.route("/new_genome", methods=["GET"])
def new_genome():
    nets, cars, genomes = get_new_genomes(population=game_states["population"])
    game_states["nets"] = nets
    game_states["cars"] = cars
    game_states["genomes"] = genomes
    return jsonify({"message": "UPDATED NEW GENOMES"})


# 3: call to simulate a frame of the ai running (at least 1000 frames per gen)
@app.route("/run_frame", methods=["GET"])
def run_frame():
    # print(game_states, "\n\n")
    nets, cars, genomes = run_simulation_frame(
                                    nets=game_states["nets"], 
                                    cars=game_states["cars"], 
                                    genomes=game_states["genomes"])
    game_states["nets"] = nets
    game_states["cars"] = cars
    game_states["genomes"] = genomes

    data = [{
        "id": car.id,
        "position": car.position,
        "angle": car.angle,
        "center": car.center,
        "alive": car.alive,
        "radars": car.radar if hasattr(car, 'radar') else []
    } for car in cars] if cars != None else []

    # print(data)
    return jsonify({"message": "PASSED FRAME", "cars": data})


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