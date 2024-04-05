from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def welcome():
    name = ""
    food = ""
    if request.method == "POST" and "username" in request.form:
        name = request.form.get('username')
        food = request.form.get('userfood')
    return render_template("index.html", name=name, food=food)

app.run()