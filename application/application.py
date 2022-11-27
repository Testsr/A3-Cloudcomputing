from flask import *
import string, random
import boto3
from boto3.dynamodb.conditions import Key, Attr
boto_client = boto3.setup_default_session(region_name='us-east-1')
application = Flask(__name__)
application.secret_key = b'\xfb=\xeb?\x84\x1d\xd6m\xfd\xbc\x9d\x0ff\xe2W\x00'
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table("login")
main_table = dynamodb.Table("stocks")
sub_table = dynamodb.Table("stocks-subs")
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
            if "chat_id" in response["Items"][0]:
                res = make_response(redirect("/main", code=302))
            else:
                res = make_response(redirect("/telegram_vaildiate", code=302))
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
@application.route("/telegram_vaildiate")
def telegram_add():
    username=session["username"]
    response = login_table.query(KeyConditionExpression=Key("username").eq(username))
    return render_template("login.html",login_failed=True)
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
    user_name = response['Items'][0]['user_name']
    sub_stocks = sub_table.query(KeyConditionExpression=Key("username").eq(username))["Items"]
    return render_template("main.html",user_name=user_name,sub_stocks=sub_stocks)

def return_query(stock_code,stock_name,stock_table_url):
    import psycopg
    if stock_code==None and stock_name==None:
        return None
    if stock_code==None:
        stock_code = "*"
    if stock_name==None:
        stock_name = "*"
    with psycopg.connect(stock_table_url) as conn:
        with conn.cursor() as curs:
            query="""
            SELECT * from asx_stocks where stock_code = %s and stock_name = %s
            """
            curs.execute(query, (stock_code, stock_name))
    return results["Items"]
@application.route('/subscribe',methods=["POST"])
def subscribe():
    try:
        username = session["username"]
        stockcode = request.form['stockcode']
        compare = request.form["compare"]
        price = int(request.form["price"])
    except KeyError:
        return redirect("/main", code=302)
    except ValueError:
        return flash("Price is not a number.")
    sub_table.put_item(
        Item={
            'username': username,
            'stockcode': stockcode,
            'compare': compare,
            'price': price
        }
    )
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
