from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def show_home():
    return render_template("index.html")

@app.route("/request_reply", methods=['POST'])
def request_reply():
    try :
        message = request.json["message"]
    except:
        return jsonify("Something didn't work")
    return jsonify(f'Hi, you just sent me the message "{message}"')


if __name__ == '__main__' :
    app.run(debug=True)