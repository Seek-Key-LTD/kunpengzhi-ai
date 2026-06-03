from flask import Flask, request, jsonify
from spiral.score_engine import BYOKScoreEngine

app = Flask(__name__)
engine = BYOKScoreEngine()

@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    if not data:
        return jsonify({'error':'empty'}),400
    vote = engine.vote(data['voter_key'], data['seat_id'], data['dimension'], data['score'])
    if vote:
        return jsonify({'vote_id':vote.vote_id}),200
    return jsonify({'error':'invalid'}),400

@app.route('/scores')
def scores():
    return jsonify(engine.get_scores())

if __name__ == '__main__':
    app.run(port=5890)
