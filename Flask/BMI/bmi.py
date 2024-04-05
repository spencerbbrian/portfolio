from flask import Flask, request, render_template
from flask_caching import Cache

cache = Cache()

app = Flask(__name__)


@app.route("/bmi", methods=["GET","POST"])
def bmi():
    bmi = ""
    name = ""
    weight = ""
    height = ""
    if request.method == "POST" and "weight" and "name" in request.form:
        name = request.form.get('name')
        weight = float(request.form.get('weight'))
        height = float(request.form.get('height'))
        bmi = calculate_bmi(weight,height)
    return render_template("index.html", name=name, bmi=bmi)

def calculate_bmi(weight,height):
    return round(weight/(height**2),2)


app.run(debug=True)