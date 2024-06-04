from flask import Flask, request, jsonify
from flask_cors import CORS
from simulate import simulate

# init flask app
app = Flask(__name__)
# allow cross origins requests
CORS(app)


@app.route("/num", methods=["GET"])
def get_num():
  print("getting 5")
  return jsonify({"num": 5})


@app.route("/calc", methods=["POST"])
def calc():
  print("doing math")
  return jsonify({"num": request.json.get("num") * 10})


@app.route("/run_sim", methods=["POST"])
def run_sim():
  pass
  # map = request.json.get('map')
  
  # Run your simulation with the provided map
  # result = play_sim(map)
  # return jsonify(result)


if __name__ == "__main__":
  app.run(debug=True)