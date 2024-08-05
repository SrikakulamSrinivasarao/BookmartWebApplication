import base64
from pymongo import MongoClient
from flask import Flask,render_template,session,request,redirect,send_file
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import io



database=MongoClient("mongodb://127.0.0.1:27017")
users=database['users']
books=users['books'] 
stock=users['stock']
 
app=Flask(__name__)

app.secret_key='50000'
app.config['uploads']="uploads"
# session['flag']=0

@app.route('/')
def home():
    return render_template('Login.html')

@app.route('/reg')
def loadReg():
    return render_template('Register.html')


@app.route('/register',methods=['post','get'])
def register():
    username=request.form['username']
    phone=request.form['phone']
    mail=request.form['mail']
    password=request.form['password']
    confirmpass=request.form['confirmpass']
    k={}
    k['username']=username
    k['phone']=phone
    k['mail']=mail
    k['password']=password
    k['confirmpass']=confirmpass  
    k['cart']=[]
    res=books.find()
    for data in res:
        x=dict(data)
        if(x['username']==username):
            return render_template('register.html',res='Username already exists')
        if(x['mail']==mail):
         return render_template('register.html',res='Email already exists')
        if(password!=confirmpass):
            return render_template('register.html',res='Passwords do not match')
        if(len(password)<8):
            return render_template('register.html',res='Password should have atlest 8 characters')           
    else:
        books.insert_one(k)
        return render_template('register.html',res='Registration successful')

@app.route("/adminlogin",methods=['post','get'])
def adminlogin():
    user=request.form['name']
    password=request.form['pass']

    data=stock.find()
    if(user=="admin" and password=="nimda"):
        session['name']=user
        return render_template('AdminIndex.html',data=data)
    else:
        return render_template('Admin.html',status='User does not exist or wrong password')



@app.route('/login',methods=['post','get'])
def login():
    user=request.form['name']
    password=request.form['pass']
    session['name']=user
    flag=0
    res=books.find()
    res1=books.find_one({"username":user})
    data=stock.find()
    for x in res:
        i=dict(x)
        if(user==i['username'] and password==i['password']):
            session['name']=user
            flag=1
            break
    if(flag==1):
        count=(len(list(res1['cart'])))
        return render_template('index.html',data=data,count=count)
    else:
        return render_template('login.html',status='User does not exist or wrong password')

@app.route('/cart')
def cart():
    data=books.find_one({"username":session['name']})
    result=data['cart']
    di={}
    total=0
    for i in result:
        if i["_id"] in di:
            di[i["_id"]]['count']+=1
        else:
            x=dict(i)
            x['count']=1
            di[i["_id"]]=x
        total+=int(i['price'])
    return render_template('Cart.html',data=di,total=total)

@app.route('/profile')
def profile():
    return render_template('Profile.html')

@app.route('/sortbyauthor')
def sortbyauthor():
    return render_template('Author.html')

@app.route('/sortbygenere')
def sortbygenere():
    return render_template('Genere.html')

@app.route('/forgot')
def forgot():
    return render_template('Forgot.html')

@app.route('/forget')
def forget():
    email=request.form['email']
    res=books.find_one({'email': email})
    if not res:
        return render_template('Forgot.html',status='Email not found')
    else:
        mail=res['password']
        return render_template('Password.html',pas=mail)

@app.route('/add')
def deff():
    return render_template('Book.html')

@app.route('/addbook',methods=['post'])
def book():
    name=request.form['bookname']
    author=request.form['author']
    genre=request.form['genre']
    price=request.form['price']
    chooseFile=request.files['image']
    doc=secure_filename(chooseFile.filename)
    chooseFile.save(app.config['uploads']+'/'+doc)
    di={}
    di['title']=name
    di['genre']=genre
    di['author']=author 
    di['price']=int(price)
    di['image']=chooseFile.filename
    di['mimetype'] = chooseFile.mimetype.split('/')[-1]
    stock.insert_one(di) 
    return render_template('Book.html',status="book inserted")


@app.route('/admin')
def admin():
    return render_template('Admin.html')

@app.route('/addtocart',methods=['get'])
def addtocart():
    id=request.args.get("id")
    res=stock.find_one({"_id":ObjectId(id)})
    books.update_one({"username":session['name']},{"$push":{"cart":res}})
    return redirect('/cart')
  

@app.route('/filter',methods=['get','post'])
def filter():
    da=[]
    filter=request.form['search']
    data=stock.find()
    res1=books.find_one({"username":session['name']})
    count=(len(list(res1['cart'])))
    z=0
    for i in data:
        x=dict(i)
        
        if x['author']==filter:
            z=1
            da+=list(stock.find({'author':filter}))
            break
        elif x['genre']==filter:
            da+=list(stock.find({"genre":filter}))
            z=1
            break
        elif x['title']==filter:
            z=1
            da+=list(stock.find({"title":filter}))
            break

    if z==0:       
        return render_template('index.html',data=da,status='No results found')
    else:
        return render_template('index.html',data=da,count=count)
    

@app.route('/adminfilter',methods=['get','post'])
def afilter():
    da=[]
    filter=request.form['search']
    data=stock.find()
    z=0
    for i in data:
        x=dict(i)
        
        if x['author']==filter:
            z=1
            da+=list(stock.find({'author':filter}))
            break
        elif x['genre']==filter:
            da+=list(stock.find({"genre":filter}))
            z=1
            break
        elif x['title']==filter:
            z=1
            da+=list(stock.find({"title":filter}))
            break

    if z==0:       
        return render_template('AdminIndex.html',data=da,status='No results found')
    else:
        return render_template('AdminIndex.html',data=da)


@app.route('/carthome')
def carthome():
    data=stock.find()
    return render_template('index.html',data=data)

@app.route("/book")
def booking():
    return render_template("/Book.html")

@app.route('/logout')
def logout():
    session['name']=''
    return redirect('/')

@app.route('/img/<name>/<mimetype>')
def load(name,mimetype):
    with open('./uploads/'+name,'rb') as f:
        x=f.read()
        return send_file(
            io.BytesIO(x),
            mimetype='image/'+mimetype,
            as_attachment=True,
            download_name=name
        )

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/remtocart')
def rem():
    id=request.args.get("id")
    res=stock.find_one({"_id":ObjectId(id)})
    books.update_one({"username":session['name']},{"$pull":{"cart":res}})
    return redirect('/cart')


@app.route('/removebook')
def removebook():
    data=stock.find()
    id=request.args.get("id")
    res=stock.find_one({"_id":ObjectId(id)})
    stock.delete_one(res)
    return render_template('AdminIndex.html',data=data)

@app.route('/adminindex')
def adminind():
    data=stock.find()
    return render_template('AdminIndex.html',data=data)


@app.route('/psuccess',methods=['post'])
def ppsuc():
    request.form['address']
    return render_template('psuccess.html')


if __name__=="__main__":
    app.run(debug=True)