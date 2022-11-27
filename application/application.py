import os

from flask import *
import string, random
import boto3
from boto3.dynamodb.conditions import Key, Attr
import psycopg
application = Flask(__name__)
application.secret_key = b'\xfb=\xeb?\x84\x1d\xd6m\xfd\xbc\x9d\x0ff\xe2W\x00'
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table("login")
main_table = dynamodb.Table("stocks")
sub_table = dynamodb.Table("stocks-subs")
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.
stock_table_url=os.environ["stocks_rds"]
@application.route('/')
def index():
    if 'username' in session:
        return redirect("/login", code=302)
    return redirect("/main", code=302)

@application.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return do_login_validiate()
    else:
        return render_template("login.html")
def do_login_validiate():
    try:
        username=request.form["username"]
        password=request.form["password"]
        if validiate(username,password):
            response = login_table.query(KeyConditionExpression=Key("username").eq(username))
            if "chatid" in response["Items"][0]:
                res = make_response(redirect("/main", code=302))
            else:
                res = make_response(redirect("/telegram", code=302))
            session["username"] = username
            return res
    except KeyError:
        pass #Fallthrough to failed template

    return render_template("login.html",login_failed=True)

def validiate(username:str,password:str):
    response = login_table.query(KeyConditionExpression=Key("username").eq(username),
                                 FilterExpression=Attr("password").eq(password),Select="COUNT")
    if response ["Count"] > 0:
        return True
    return False
@application.route("/telegram")
def telegram_add():
    username=session["username"]
    response=login_table.query(KeyConditionExpression=Key("username").eq(username))

    return render_template("telegram.html",key=response["Items"][0]["ident_str"])
@application.route("/logout")
def logout():
    session.pop('username', None)
    return redirect("/login", code=302)

@application.route('/register',methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return add_user()
    else:
        return render_template("register.html")

def add_user():
    username = request.form["username"]
    password=request.form["pass"]
    response = login_table.query(KeyConditionExpression=Key("username").eq(username),Select="COUNT")
    if response["Count"] > 0:
        return render_template("register.html",email_existed=True)
    length=10
    letters = string.ascii_lowercase
    ident=''.join(random.choice(letters) for i in range(length))
    login_table.put_item(Item={
        'username': username,
        'password': password,
        "ident_str":ident
    })
    flash("Sucessful registration")
    return redirect("/login",code=302)


@application.route('/main')
def display_main():
    if 'username' not in session:
        return redirect("/login", code=302)
    username=session["username"]
    response = login_table.query(KeyConditionExpression=Key("username").eq(username))
    return render_template("main.html",username=username)
@application.route('/query')
def display_query():
    if 'username' not in session:
        return redirect("/login", code=302)
    username=session["username"]
    subscriptions = []
    stock_code = request.args.get('stockcode','')
    stock_name = request.args.get('stockname','')
    response=return_query(stock_code,stock_name,"postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres")
    if response is None:
        return render_template("main.html",user_name=username,subscriptions=subscriptions)

    return render_template("main.html",user_name=username,subscriptions=subscriptions,response=response)

def return_query(stock_code,stock_name,stock_table_url):
    if stock_code=='' and stock_name=='':
        return None
    elif stock_code=='':
        params=(stock_name,)
        query = "SELECT * from asx_stocks where stock_name=%s;"
    elif stock_name=='':
        params=(stock_code,)
        query = "SELECT * from asx_stocks where stock_code=%s;"
    else:
        params=(stock_code,stock_name)
        query = "SELECT * from asx_stocks where stock_code=%s and stock_name=%s;"
    with psycopg.connect(stock_table_url) as conn:
        results=conn.execute(query,params).fetchall()
        print(query)
        print(params)
        print(results)
    return results
@application.route('/main')

@application.route('/subscribe',methods=["POST"])
def subscribe():
    try:
        username = session["username"]
        stock_code = request.form['stock_code']
        compare = request.form["compare"]
        trigger = float(request.form["trigger"])
    except KeyError:
        return redirect("/main", code=302)
    except ValueError:
        return flash("Price is not a number.")
    print(stock_table_url)

    with psycopg.connect(stock_table_url) as conn:
        params=(username,stock_code,compare,trigger)
        print(params)
        conn.execute('INSERT INTO asx_cond (username,stock_code,compare,trigger) VALUES(%s,%s,%s,%s)',params)
        print("OK")
    flash("Subscribed.")
    return redirect("/main", code=302)
def remove_subscription(username,stockcode):
    sub_table.delete_item(
        Key={
            'username':username,
            'stockcode':stockcode
        }
    )

if __name__ == '__main__':
    # run app in debug mode on port 8000
    application.run(debug=True, port=8000)
