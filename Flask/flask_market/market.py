from flask import Flask,render_template,request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = "False"
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False,unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False,unique=True)
    description = db.Column(db.String(length=1024), nullable=False,unique=True)

    def __repr__(self) -> str:
        return f"Item {self.name}"

with app.app_context():
        db.create_all()

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


# @app.route("/",methods=["POST","GET"])
# def index():
#     #Add a Task
#     if request.method == "POST":
#         current_task = request.form['content']
#         new_task = MyTask(content=current_task)
#         try:
#             db.session.add(new_task)
#             db.session.commit()
#             return  redirect("/")
#         except Exception as e:
#             print(f"ERROR:{e}")
#             return f"ERROR:{e}"
#     #See all current tasks
#     else:
#         tasks = MyTask.query.order_by(MyTask.created).all()
#         return render_template('index.html', tasks=tasks)


@app.route('/add',methods=["GET","POST"])
def add_page():
    # Add an Item
    if request.method == "POST":
        current_item_name = request.form['item-name']
        current_item_price = request.form['item-price']
        current_item_barcode = request.form['item-barcode']
        current_item_description = request.form['item-description']
        new_item = Item(name=current_item_name,
                        price=current_item_price,
                        barcode=current_item_barcode,
                        description=current_item_description)
        try:
             db.session.add(new_item)
             db.session.commit()
             return redirect("/")
        except Exception as e:
             print(f"ERROR:{e}")
             return f"ERROR:{e}"
    return render_template('additem.html')

@app.route('/market')
def market_page():
    items = Item.query.all()
    return render_template('market.html',items=items)

app.run(debug=True)