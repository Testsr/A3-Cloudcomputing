from flask import *
import string, random
import boto3
from boto3.dynamodb.conditions import Key, Attr
import psycopg
import os
boto_client = boto3.setup_default_session(region_name='us-east-1')

application = Flask(__name__)
application.secret_key = b'\xfb=\xeb?\x84\x1d\xd6m\xfd\xbc\x9d\x0ff\xe2W\x00'
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table("login")
main_table = dynamodb.Table("stocks")
sub_table = dynamodb.Table("stocks-subs")
stock_table_url= os.environ["stocks_rds"] if "stocks_rds" in os.environ else "postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"\
                                                                           ".us-east-1.rds.amazonaws.com:5432/postgres"
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
@application.route('/main')
def display_main():
    if 'username' not in session:
        return redirect("/login", code=302)
    username=session["username"]
    response = login_table.query(KeyConditionExpression=Key("username").eq(username))
    with psycopg.connect(stock_table_url) as conn:
        params=username,
        print(params)
        result=conn.execute('SELECT stock_code,compare,trigger FROM asx_cond where username = %s',params).fetchall()
        print(result)


    return render_template("main.html",username=username,stocks=result)
@application.route('/add_stock')
def add_stock_menu():
    if 'username' not in session:
        return redirect("/login", code=302)
    username=session["username"]
    response = login_table.query(KeyConditionExpression=Key("username").eq(username))

    return render_template("add_stock.html",username=username,subscriptions=[])

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



@application.route('/query')
def display_query():
    if 'username' not in session:
        return redirect("/login", code=302)
    username=session["username"]
    with psycopg.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres") as conn:
        conditions = conn.execute("SELECT stock_code,compare,trigger from asx_cond where username=%s",
                                  (username,)).fetchall()
    subscriptions = []
    stock_code = request.args.get('stockcode','')
    response=return_query(stock_code,"postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres")
    if response is None:
        return render_template("add_stock.html",user_name=username,subscriptions=subscriptions)

    return render_template("add_stock.html",user_name=username,subscriptions=subscriptions,response=response)

def return_query(stock_item,stock_table_url):
    if stock_item=='':
        return None
    params = (stock_item,)
    query1 = "SELECT * from asx_stocks where stock_name=%s;"
    query2 = "SELECT * from asx_stocks where stock_code=%s;"

    with psycopg.connect(stock_table_url) as conn:
        results1=conn.execute(query1,params).fetchall()
        results2=conn.execute(query2,params).fetchall()
        if len(results1)>0:
            return results1
        elif len(results2)>0:
            return results2
        else:
            return []

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
    pass
if __name__ == '__main__':
    # run app in debug mode on port 8000
    application.run(debug=True, port=8000)
