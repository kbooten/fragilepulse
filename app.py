from flask import Flask
from flask import render_template,jsonify,request
import os
app = Flask(__name__)

from distractor import Distractor
mind = Distractor()

@app.route('/')
def main_page():
    return render_template('home.html')

# @app.route('/initial_distraction', methods=['GET'])
# def initial_distraction():
# 	startSentence = request.args.get('currentSentence')
# 	print(startSentence)
# 	mind.become_distracted(startSentence)
# 	return jsonify({"focus":mind.get_focus()})

# @app.route('/another_distraction', methods=['GET'])
# def another_distraction():
# 	mind.become_distracted()
# 	return jsonify({"focus":mind.get_focus()})

@app.route('/distraction', methods=['GET'])
def distraction():
	startSentence = request.args.get('currentSentence').strip('"')
	print("Input--->"+startSentence)
	mind.become_distracted(startSentence)
	nextthought = mind.get_focus()
	print("Output--->"+nextthought)
	return jsonify({"focus":nextthought})


@app.route('/cleanMind', methods=['GET'])
def cleanMind():
	mind.used = []
	return jsonify({"focus":[]})##nonce




# @app.route('/reset', methods=['GET'])
# def reset():
# 	mind.used=[]
# 	return jsonify({"ok":"ok"})

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(host='0.0.0.0', port=port)