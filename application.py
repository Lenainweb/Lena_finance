# from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///finance.db"
db = SQLAlchemy(app)

# create datebase
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    hash = db.Column(db.String(512), nullable=False)
    cash = db.Column(db.Integer, default=10000, nullable=False)
    # users = db.relationship('Users', backref='portfolio', lazy='dynamic')


class Portfolio(db.Model):
    __tablename__ = 'portfolio'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(512))
    shares = db.Column(db.Integer)
    price = db.Column(db.Float, nullable=False)

db.create_all()


@app.route("/")
@login_required
def index():

    # Requests to the database of the user's assets.
    # portfolios = db.execute("SELECT symbol, name, SUM(shares), ROUND(price, 2) FROM portfolio WHERE user_id = :userid GROUP BY symbol HAVING SUM(shares) > 0",
    #     userid = session["user_id"])
    # cash = db.execute("SELECT cash FROM users WHERE id = :userid", userid = session["user_id"])

    # portfolios_all = Portfolio.query.filter_by(user_id=session["user_id"]).first()
    # portfolios = portfolios_all.execute(select())
    # # Calculation of the total amount of assets (money + share price) of the user.
    # summa = 0
    # for portfolio in portfolios:
    #     summa += portfolio["SUM(shares)"] * portfolio["ROUND(price, 2)"]
    # summa += cash[0]["cash"]

    # # Visualization of the user's portfolio.
    # return render_template("index.html",
    #                         portfolios = portfolios,
    #                         cash = usd(cash[0]["cash"]),
    #                         summa = usd(summa))
    return render_template("index1.html")

#############################################
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "POST":

        # ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol")

        elif not request.form.get("shares"):
            return apology("missing shares")

        elif not request.form.get("shares").isdigit() or int(request.form.get("shares")) < 1:
            return apology("invalid shares")

        # look up quote for symbol
        quote = lookup(request.form.get("symbol"))

        # symbol validation
        if not quote:
             return apology("invalid symbol")

        summa = float(quote["price"]) * float(request.form.get("shares"))

        # row = db.execute("SELECT cash FROM users WHERE id = :userid", userid = session["user_id"])
        user_cash = Users.query.filter_by(id=session["user_id"]).first()

        if float(user_cash.cash) < summa:
            return apology("can't afford")

        user_cash.cash = user_cash.cash - summa
        result_buy = Portfolio(user_id=session["user_id"], 
                                symbol=quote["symbol"],
                                name=quote["name"],
                                shares=request.form.get("shares"),
                                price=quote["price"])

        db.session.add(result_buy)
        db.session.commit()

        flash("Purchase was successful!")

        # redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("buy.html")
##############################################
# @app.route("/history")
# @login_required
# def history():
#     """Show history of transactions."""

#     # Requests to the database of the user's assets.
#     portfolios = db.execute("SELECT symbol, name, shares, ROUND(price, 2), transacted FROM portfolio WHERE user_id = :userid",
#         userid = session["user_id"])

#     # Visualization of the user's history.
#     return render_template("history.html", portfolios = portfolios)
###############################################
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        this_user = request.form.get("username")
        rows = Users.query.filter_by(username=this_user).first()

        # ensure username exists and password is correct
        if not pwd_context.verify(request.form.get("password"), rows.hash):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows.id
        session["user_name"] = request.form.get("username")

        # redirect user to home page        
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
###############################################
@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
###############################################
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        # ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol")

        # look up quote for symbol
        quote = lookup(request.form.get("symbol"))
        # flash(quote)

        # symbol validation
        if not quote:
             return apology("invalid symbol")


        # transfer to the user of the share price
        return render_template("quoted.html",
                                name = quote["name"],
                                price = usd(quote["price"]),
                                symbol = quote["symbol"])
    else:
        return render_template("quote.html")
################################################
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("missing password")

        elif not request.form.get("passwordagain") or request.form.get("password") != request.form.get("passwordagain"):
            return apology("passwords don't match")

        # query database for username
        new_user = request.form.get("username")
        rows = Users.query.filter_by(username=new_user).first()

        # ensure that the user name is not already in the database
        if rows:
            return apology("username taken")

        # getting a password hash
        hashpass = pwd_context.hash(request.form.get("password"))

        # placing a new user in the database
        # result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashpass)",
        #     username = request.form.get("username"),
        #     hashpass = hashpass)

        result = Users(username = request.form.get("username"),hash = hashpass)
        db.session.add(result)
        db.session.commit()

        # remember which user has logged in
        session["user_id"] = result
        session["user_name"] = request.form.get("username")

        flash("Register!")

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
################################################
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "POST":

        # ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol")

        elif not request.form.get("shares"):
            return apology("missing shares")

        elif not request.form.get("shares").isdigit() or int(request.form.get("shares")) < 1:
            return apology("invalid shares")

        # having = db.execute("SELECT SUM(shares) FROM portfolio WHERE user_id = :userid AND symbol LIKE :symbol",
        #     symbol = request.form.get("symbol"),
        #     userid = session["user_id"])

        having_s = Portfolio.query.filter_by(user_id=session["user_id"], symbol = request.form.get("symbol").upper()).all()
        having = 0
        for i in having_s:
            having = having + i.shares
            print("!!!!!!!!!!!!!!!!", having)

        if  not having or having <= 0:
            return apology("You do not have such shares")

        if float(request.form.get("shares")) > having:
            return apology("You do not have many shares")

        # look up quote for symbol
        quote = lookup(request.form.get("symbol"))

        summa = float(quote["price"]) * int(request.form.get("shares"))

        # rou_up = db.execute("UPDATE users SET cash = cash + :summa WHERE id = :userid",
        #     summa = summa,
        #     userid = session["user_id"])

        rou_up = Users.query.filter_by(id=session["user_id"]).first()
        rou_up.cash = rou_up.cash + summa
        db.session.add(rou_up)
        db.session.commit()

        print("@@@@@@@@@@@@@@@@@@@@")
        
        result_buy = Portfolio(user_id=session["user_id"], 
                                symbol=quote["symbol"],
                                name=quote["name"],
                                shares=(int(request.form.get("shares")) * -1),
                                price=quote["price"])

        print("66666666") 
        db.session.add(result_buy)
        print("33333333333333333")
        db.session.commit()        

        # result_sell = db.execute("INSERT INTO portfolio (user_id, symbol, name, shares,price) VALUES (:user_id, :symbol, :name, :shares,:price)",
        #     user_id = session["user_id"],
        #     symbol = quote["symbol"],
        #     name = quote["name"],
        #     shares = (int(request.form.get("shares")) * -1),
        #     price = quote["price"])

        flash("Sale was successful!")

        #redirect user to home page
        return redirect(url_for("index"))
    else:
        return render_template("sell.html")
################################################
@app.route("/user", methods=["GET", "POST"])
@login_required
def user():
    """Account management."""

    if request.method == "POST":

        if request.form.get("contribute"):
            return render_template("contribute.html")

        if request.form.get("change_passw"):
            return render_template("change_passw.html")

    else:
        return render_template("user.html")
###############################################
@app.route("/change_passw", methods=["GET", "POST"])
@login_required
def change_passw():
    """Account management."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("old_password"):
            return apology("not password")

        # check = db.execute("SELECT hash FROM users WHERE id = :user_id", user_id = session["user_id"])
        check = Users.query.filter_by(id=session["user_id"]).first()

        if not pwd_context.verify(request.form.get("old_password"), check.hash):
            return apology("invalid password")

        # ensure password was submitted
        elif not request.form.get("new_password"):
            return apology("not new password")

        elif not request.form.get("new_passwordagain") or request.form.get("new_password") != request.form.get("new_passwordagain"):
            return apology("new passwords don't match")

        new_hashpass = pwd_context.hash(request.form.get("new_password"))
        
        check.hash = new_hashpass
        db.session.add(check)
        db.session.commit()

        flash("Your password has been changed!")

        return render_template("user.html")

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_passw.html")
#########################
@app.route("/contribute", methods=["GET", "POST"])
@login_required
def contribute():
    """Account management."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("required_amount") or float(request.form.get("required_amount")) <= 0:
            return apology("enter amount")

        
        cash_up_user = Users.query.filter_by(id=session["user_id"]).first()
        cash_up_user.cash = cash_up_user.cash + float(request.form.get("required_amount"))
        db.session.add(cash_up_user)
        db.session.commit()


        flash("The amount was credited to your account!")

        return render_template("user.html")

    else:
        return render_template("contribute.html")
