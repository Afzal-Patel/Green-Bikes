#modules
import sys
from flask import Flask, render_template, request, redirect, g, session, flash, send_from_directory,url_for
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os
import sqlite3
from sqlite3 import Error
import random

#secret key
app = Flask(__name__)
app.secret_key = "fruit_music_&"
app.config["TEMPLATES_AUTO_RELOAD"] = True
#app.config['TESTING'] = True
#app.config['ENV'] = 'development'
#app.config['DEBUG'] = True

#@app.after_request
#def after_request(reponse):
    # response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    # response.headers["Expires"] = 0
    # response.headers["Pragma"] = "no-cache"
    # return response

#link to db
#figure out relative path
DATABASE = 'gb.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            session["user"] = "Guest"
            return redirect("/loginHome")
        return f(*args, **kwargs)
    return decorated_function

#staff only access
def special_requirement(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        try:
            if "XXXXXX47" == session['user']:
                return f(*args,**kwargs)
            else:
                return redirect(url_for('logout'))
    
        except:
            return redirect(url_for('logout'))
    return wrap

#restrict renting to only students
def special_requirement2(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        try:
            if session['type'] == 'Student':
                return f(*args,**kwargs)
            else:
                return redirect(url_for('logout'))
    
        except:
            return redirect(url_for('logout'))
    return wrap


@app.route("/mainTool",methods=["GET"])
#@login_required
@special_requirement
def staffDBaccess():
    if request.method == "GET":
        try:
            user = session['user']
            con = get_db()
            cur = con.cursor()
            cur.execute("SELECT * from Staff")
            staff_data = cur.fetchall()
            cur.execute("SELECT * from Students")
            student_data = cur.fetchall()
            cur.execute("SELECT * from Community")
            community_data = cur.fetchall()
            return render_template("mainTool.html", data1=staff_data,data2=student_data,data3=community_data,user=user)
        except Exception as e:
            print(e, file=sys.stdout)
            return redirect(url_for('staffDBaccess'))
 

@app.route("/bikeTool",methods=["GET","POST"])
#@login_required
@special_requirement
def staffBikeDBaccess():
    if request.method == "GET":
        try:
            con = get_db()
            cur = con.cursor()
            cur.execute("SELECT BikeNo,History FROM GB")
            bike_data = cur.fetchall()

            cur.execute("SELECT LockNo,Code,Pair FROM Locks")
            lock_data = cur.fetchall()

            cur.execute("SELECT * FROM RaffleLimit")
            raffleNum = cur.fetchall()

            return render_template("bikeTool.html", data=bike_data,data2=lock_data,data3=raffleNum)
        except Exception as e:
        #print(e, file=sys.stdout)
            return redirect(url_for('logout'))
    if request.method == "POST":
        try:
            conn = get_db()
            cur = conn.cursor()

            bikeNo = int(request.form.get('BikeNo'))
            model = request.form.get('model')
            year = int(request.form.get('year'))
            size = int(request.form.get('size'))
            fee = int(request.form.get('fee'))
            #available by default
            available = 1
            history = ''

            if not (1990 <= year <= 2020):
                flash("error: check year!")
                return redirect(url_for('staffBikeDBaccess'))

            if not (42 <= size <= 62):
                flash("error: check size!")
                return redirect(url_for('staffBikeDBaccess'))

            if(fee<0):
                flash("error: negative fee!")
                return redirect(url_for('staffBikeDBaccess'))
        
            cur.execute("""INSERT INTO GB VALUES(?,?,?,?,?,?,?)""",(bikeNo,model,year,size,available,history,fee))
            conn.commit()
  
            flash("GB Added Successfully!")
            return redirect(url_for('staffBikeDBaccess'))
        except Exception as e:
            print(e, file=sys.stdout)
            flash("Unsuccessful bike add!")
            return redirect(url_for('staffBikeDBaccess'))
 

@app.route("/editLock",methods=["POST"])
#@login_required
@special_requirement
def editLock():
    if request.method == "POST":
        try:
            conn = get_db()
            cur = conn.cursor()

            lockNo = int(request.form.get('lock'))
    
            #delete lock
            if(request.form.get('deleteLock')==str(lockNo)):
                cur.execute("""DELETE FROM Locks where LockNo=:x """,{"x":lockNo})
                conn.commit()
                flash("Lock deletion successful!")
                return redirect(url_for('staffBikeDBaccess'))

            #update both pair and combo
            elif(request.form.get('pair') and request.form.get('combo')):
                newPair = int(request.form.get('pair'))
                cur.execute("""SELECT EXISTS(SELECT 1 FROM GB WHERE BikeNo=:x)""",{"x":newPair})
                checkBikeExists = cur.fetchone()[0]

                if not checkBikeExists:
                    flash("No existing GB to pair with Lock!")
                    return redirect(url_for('staffBikeDBaccess'))

                if(len(request.form.get('combo'))!=4):
                    flash("Unsuccessful lock update! Check lock combination length")
                    return redirect(url_for('staffBikeDBaccess'))

                try:
                    newCode = int(request.form.get('combo'))
                except:
                    flash("Unsuccessful lock update! Check code type")
                    return redirect(url_for('staffBikeDBaccess'))


                cur.execute("""UPDATE Locks SET Code=:x, Pair=:y WHERE LockNo=:z""",{"x":newCode,"y":newPair,"z":lockNo})
                conn.commit()
                flash("Lock code and pair update successful!")
                return redirect(url_for('staffBikeDBaccess'))

            # #update pair
            elif(request.form.get('pair')):
                newPair = int(request.form.get('pair'))
                cur.execute("""SELECT EXISTS(SELECT 1 FROM GB WHERE BikeNo=:x)""",{"x":newPair})
                checkBikeExists = cur.fetchone()[0]

                if not checkBikeExists:
                    flash("No existing GB to pair with Lock!")
                    return redirect(url_for('staffBikeDBaccess'))

                newPair = int(request.form.get('pair'))
                cur.execute("""UPDATE Locks SET Pair=:x WHERE LockNo=:y""",{"x":newPair,"y":lockNo})
                conn.commit()
                flash("Lock pair update successful!")
                return redirect(url_for('staffBikeDBaccess'))
            
            #update combo
            elif(request.form.get('combo')):
                if(len(request.form.get('combo'))!=4):
                    flash("Unsuccessful lock update! Check lock type/length combination")
                    return redirect(url_for('staffBikeDBaccess'))
                try:
                    newCode = int(request.form.get('combo'))
                except:
                    flash("Unsuccessful lock update! Check code type")
                    return redirect(url_for('staffBikeDBaccess'))

                cur.execute("""UPDATE Locks SET Code=:x WHERE LockNo=:y""",{"x":newCode,"y":lockNo})
                conn.commit()
                flash("Lock code update successful!")
                return redirect(url_for('staffBikeDBaccess'))

            else:
                flash("Unsuccessful lock update!")
                return redirect(url_for('staffBikeDBaccess'))

        except Exception as e:
            print(e, file=sys.stdout)
            flash("Unsuccessful lock update! Check for missing fields and types")
            return redirect(url_for('staffBikeDBaccess'))
 
@app.route("/addLock",methods=["POST"])
#@login_required
@special_requirement
def addLock():
    if request.method == "POST":
        try:
            
            if(len(request.form.get('Code'))!=4):
                flash("Unsuccessful lock update! Check code length")
                return redirect(url_for('staffBikeDBaccess'))

            conn = get_db()
            cur = conn.cursor()

            LockNo = int(request.form.get('LockNo'))
            Code = int(request.form.get('Code'))

            #pair is -1 for unborrowed locks
            cur.execute("""INSERT INTO Locks VALUES(?,?,-1)""",(LockNo,Code))
            conn.commit()
  
            flash("Lock Added Successfully!")
            return redirect(url_for('staffBikeDBaccess'))
        except Exception as e:
            flash("Unsuccessful lock add! Check Missing Fields, Types, and Combo length")
            return redirect(url_for('staffBikeDBaccess'))

@app.route("/setRaffle",methods=["POST"])
#@login_required
@special_requirement
def setRaffle():
    if request.method == "POST":
        try:
            conn = get_db()
            cur = conn.cursor()

            maxRaffleNo = int(request.form.get('maxNum'))

            if(maxRaffleNo > 10 or maxRaffleNo < 0):
                    flash("Unsuccessful limit set add!")
                    return redirect(url_for('staffBikeDBaccess'))
            

            cur.execute("""UPDATE RaffleLimit SET MaxRaffleNo=:x""",{'x':maxRaffleNo})
            conn.commit()
  
            flash("Limit Set Successfully!")
            return redirect(url_for('staffBikeDBaccess'))
        except Exception as e:
            print(e, file=sys.stdout)
            flash("Unsuccessful limit set add!")
            return redirect(url_for('staffBikeDBaccess'))
 

#begin add balance
@app.route("/addStuBal",methods=["POST"])
@login_required
#@special_requirement
def addStuBal():
    if request.method == "POST":
        try:
            con = get_db()
            cur = con.cursor()

            bal = int(request.form.get('balance'))
            user = request.form.get('user1')

            if(bal<0):
                flash("Error: Negative Balance")
                return redirect(url_for('staffDBaccess'))
    
            cur.execute("""UPDATE Students SET bal=:x WHERE userID=:y""",{'x':bal,'y':user})
            con.commit()
            flash("Balance Updated")
            return redirect(url_for('staffDBaccess'))
        except Exception as e:
            #print(e, file=sys.stdout)
            flash("Balance Update Unsuccessful")
            return redirect(url_for('staffDBaccess'))
 

@app.route("/addCommBal",methods=["POST"])
@login_required
#@special_requirement
def addCommBal():
    if request.method == "POST":
        try:
            con = get_db()
            cur = con.cursor()

            bal = int(request.form.get('balance'))
            user = request.form.get('user1')

            if(bal<0):
                flash("Error: Negative Balance")
                return redirect(url_for('staffDBaccess'))
    
            cur.execute("""UPDATE Community SET bal=:x WHERE userID=:y""",{'x':bal,'y':user})
            con.commit()
            flash("Balance Updated")
            return redirect(url_for('staffDBaccess'))
        except Exception as e:
            #print(e, file=sys.stdout)
            flash("Balance Update Unsuccessful")
            return redirect(url_for('staffDBaccess'))

#end add balance

#begin repair and rent requests
@app.route("/repairRequests",methods=["GET","POST"])
#@login_required
@special_requirement
def repairStuReq():
    if request.method == "GET":
        try:
         
            con = get_db()
            cur = con.cursor()
            cur.execute("SELECT * from studentRepairRequest")
            repairData = cur.fetchall()
            cur.execute("SELECT * from commRepairRequest")
            repairCommData = cur.fetchall()
           
            return render_template("repairTool.html", data=repairData,data2=repairCommData)
        except Exception as e:
            print(e, file=sys.stdout)
    if request.method == "POST":
        #staff posts this data 
        
        try:
            conn = get_db()
            cur = conn.cursor()

            bikeNo = int(request.form.get('bikeNo'))
            progress = int(request.form.get('progress'))
            repairID = request.form.get('repairID')
            status = ''
            #ready to service
            if (progress == 1):
                status = 'You may drop-into the shop during working hours'
            #in progress
            elif (progress == 2):
                status = 'Your Bike is being repaired..'
            #mark as finished
            elif (progress == 3):
                #update bike history with notes from finished request, new notes higher that older ones
                cur.execute("SELECT History from GB WHERE BikeNo=:x",{"x":bikeNo})
                oldNotes = cur.fetchone()[0]
                notes = request.form.get('notes') + ' ; ' +'\n'
                newNotes = notes + oldNotes
                cur.execute("""UPDATE GB SET History=:x WHERE BikeNo=:y""",{"x":newNotes,"y":bikeNo})
                conn.commit()
                status = 'Finished'
            if (progress == -1):
                cur.execute("""DELETE FROM studentRepairRequest WHERE BikeNo=:x AND repairID=:y""",{"x":bikeNo,"y":repairID})
                conn.commit()
                flash("Update Successful!")
                return redirect(url_for('repairStuReq'))

                #staff side
            cur.execute("""UPDATE studentRepairRequest SET progress=:x WHERE BikeNo=:y AND repairID=:z""",{"x":progress,"y":bikeNo,"z":repairID})
            conn.commit()
                #student side
            cur.execute("""UPDATE studentRepairRequest SET status=:x WHERE BikeNo=:y AND repairID=:z""",{"x":status,"y":bikeNo,"z":repairID})
            conn.commit()

            flash("Update Successful!")
            return redirect(url_for('repairStuReq'))

        except Exception as e:
            print(e, file=sys.stdout)
            flash("Update Unsuccessful!")
            return redirect(url_for('repairStuReq'))
 

@app.route("/repairCommRequests",methods=["POST"])
#@login_required
@special_requirement
def repairCommReq():
    if request.method == "POST":
        #staff posts this data 
        try:
            conn = get_db()
            cur = conn.cursor()

            user = request.form.get('user')
            progress = int(request.form.get('progress'))
            repairID = int(request.form.get('repairID'))

            if (progress == -1):
                cur.execute("""DELETE FROM commRepairRequest WHERE userID=:y and repairID=:z""",{"y":user,"z":repairID})
                conn.commit()
                flash("Deletion Successful!")
                return redirect(url_for('repairStuReq'))
            
            status = ''
   
            
            if (progress == 1):
                status = 'You may drop-into the shop during working hours'
            if (progress == 2):
                status = 'Your Bike is being repaired..'
            if (progress == 3):

                status = 'Finished'
        

             #staff side
            cur.execute("""UPDATE commRepairRequest SET progress=:a WHERE userID=:b AND repairID=:c""",{"a":progress,"b":user,"c":repairID})
            conn.commit()
            #comm side
            cur.execute("""UPDATE commRepairRequest SET status=:x WHERE userID=:y AND repairID=:z""",{"x":status,"y":user,"z":repairID})
            conn.commit()
            
            flash("Update Successful!")

            return redirect(url_for('repairStuReq'))


        except Exception as e:
            print(e, file=sys.stdout)
            flash("Update Unsuccessful!")
            return redirect(url_for('repairStuReq'))


@app.route("/rentRequests",methods=["GET","POST"])
#@login_required
@special_requirement
def rentReq():
    if request.method == "GET":
        try:
         
            con = get_db()
            cur = con.cursor()
            cur.execute("SELECT * from Reserve")
            reserveData = cur.fetchall()

            return render_template("rentTool.html", data=reserveData)
        except Exception as e:
            print(e, file=sys.stdout)
    if request.method == "POST":
        #staff posts this data 
        conn = get_db()
        cur = conn.cursor()
        try:
            status = int(request.form.get('status'))
            bikeNo = int(request.form.get('bikeNo'))
 
            if (status == -1):
                cur.execute("""DELETE FROM Reserve WHERE BikeNo=:y""",{"y":bikeNo})
                conn.commit()
                cur.execute("""UPDATE GB SET available=:z WHERE BikeNo=:y""",{"z":True,"y":bikeNo})
                conn.commit()

                flash("Update Successful!")
                return redirect(url_for('rentReq'))
            if (status == 1):
                try:
                    cur.execute("""UPDATE Reserve SET status=:z WHERE BikeNo=:y""",{"z":1,"y":bikeNo})
                    conn.commit()
                    flash("Update Successful!")
                    return redirect(url_for('rentReq'))
                except:
                    flash("reservation cancelled!")
                    return redirect(url_for('rentReq'))



        except Exception as e:
            flash("Update unsuccessful!")
            #print(e, file=sys.stdout)
            return redirect(url_for('rentReq'))

#end requests


#home page
@app.route("/",methods=["GET","POST"])
def homePage():
    if request.method == "GET":
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Reserve WHERE userID=:un)""",{"un":session['user']})
            checkRentAccess = cur.fetchone()[0]
            return render_template("homePage.html", user=session['user'],check=checkRentAccess)
        except Exception as e:
            #print(e, file=sys.stdout)
            return render_template("homePage.html", user="Guest")

#begin login 
@app.route("/loginHome", methods=["GET"])
def loginHome():
    if request.method == "GET":
        try:
            user=session["user"]
        except:
            user="Guest"
        return render_template("loginHome.html")

@app.route("/staffLogin", methods=["GET","POST"])
def stafflogin():
    if request.method == "GET":
        return render_template("staffLogin.html")
    elif request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        un = request.form.get("loginID")
        pw = request.form.get("password")

        if not un:
            flash("Please enter your username")
            return render_template("staffLogin.html")
        if not pw:
            flash("Please enter your password")
            return render_template("staffLogin.html")

        #userID must be registered
        cur.execute("""SELECT EXISTS(SELECT 1 FROM Staff WHERE userID=:un)""",{"un":un})
        checkUser1 = cur.fetchone()[0]
  
        if(checkUser1):
            #entered password must = hashed password for entered userID
            cur.execute("""SELECT hash FROM Staff WHERE userID=:un""",{"un":un})
            checkHash1=cur.fetchone()[0]
            if(check_password_hash(checkHash1, pw)):
                session['logged'] = True 
                session['user'] = un
                return redirect(url_for('homePage'))
            else:
                flash("invalid credentials. Please try again.")
                return render_template("staffLogin.html")
        else:
            flash("invalid credentials. Please try again.")
            return render_template("staffLogin.html")
    else:
        flash("invalid credentials. Please try again.")
        return render_template("staffLogin.html")

@app.route("/stuLogin", methods=["GET","POST"])
def stulogin():
    if request.method == "GET":
        return render_template("stuLogin.html")
    elif request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        un = request.form.get("loginID")
        pw = request.form.get("password")

        if not un:
            flash("Please enter your username")
            return render_template("stuLogin.html")
        if not pw:
            flash("Please enter your password")
            return render_template("stuLogin.html")

        #userID must be registered
        cur.execute("""SELECT EXISTS(SELECT 1 FROM Students WHERE userID=:un)""",{"un":un})
        checkUser1 = cur.fetchone()[0]
  
        if(checkUser1):
            #entered password must = hashed password for entered userID
            cur.execute("""SELECT hash FROM Students WHERE userID=:un""",{"un":un})
            checkHash1=cur.fetchone()[0]
            if(check_password_hash(checkHash1, pw)):
                session['logged'] = True 
                session['user'] = un
                session['type'] = 'Student'
                return redirect(url_for('homePage'))
            else:
                flash("invalid credentials. Please try again.")
                return render_template("stuLogin.html")
        else:
            flash("invalid credentials. Please try again.")
            return render_template("stuLogin.html")
    else:
        flash("invalid credentials. Please try again.")
        return render_template("stuLogin.html")

@app.route("/commLogin", methods=["GET","POST"])
def commLogin():
    if request.method == "GET":
        return render_template("commLogin.html")
    elif request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        un = request.form.get("loginID")
        pw = request.form.get("password")

        if not un:
            flash("Please enter your username")
            return render_template("commLogin.html")
        if not pw:
            flash("Please enter your password")
            return render_template("commLogin.html")

        #userID must be registered
        cur.execute("""SELECT EXISTS(SELECT 1 FROM Community WHERE userID=:un)""",{"un":un})
        checkUser1 = cur.fetchone()[0]
  
        if(checkUser1):
            #entered password must = hashed password for entered userID
            cur.execute("""SELECT hash FROM Community WHERE userID=:un""",{"un":un})
            checkHash1=cur.fetchone()[0]
            if(check_password_hash(checkHash1, pw)):
                session['logged'] = True 
                session['user'] = un
                return redirect(url_for('homePage'))
            else:
                flash("invalid credentials. Please try again.")
                return render_template("commLogin.html")
        else:
            flash("invalid credentials. Please try again.")
            return render_template("commLogin.html")
    else:
        flash("invalid credentials. Please try again.")
        return render_template("commLogin.html")
#end login 

#begin registration 
@app.route("/registerHome", methods=["GET"])
def registerHome():
    if request.method == "GET":
        return render_template("registerHome.html")

@app.route("/staffReg", methods=["GET","POST"])
def staffReg():
    if request.method == "GET":
        return render_template("staffReg.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:
            idNum = int(request.form['idNum'])
            i2 = int(request.form['id_two'])
            year = int(request.form["year"])
            school = request.form["school"]
            firstName = request.form["firstName"]
            lastName = request.form["lastName"]
            email = request.form["email"]
            user = request.form["user"]
            password = str(request.form["password"])
            p2 = str(request.form["p_two"])
            word = str(request.form["word"])
            hashWord = generate_password_hash(word)
            hashPSW = generate_password_hash(password)

            try:
                tele = request.form["tele"]
            except:
                tele = -1

            if not word:
                flash("Please choose a secret word")
                return redirect(url_for('staffReg'))

        #check phone #
            if(tele == -1):
                flash("enter a phone #")
                return redirect(url_for('staffReg'))
    
        #for staff user accounts / add 'or' for more admin accounts
            if (user == "green47"):
                accType = 1

        #all users must agree to terms / (todo: create terms in html)
            if not request.form.get("agreement"):
                flash("Please read through and agree to terms")
                return redirect(url_for('staffReg'))

        #check phone #
            if(len(tele) < 9):
                flash("enter a valid phone #")
                return redirect(url_for('staffReg'))

        #check email format
            if('@' not in email):
                flash("invalid email address")
                return redirect(url_for('staffReg'))
        #password matching check
            if(password != p2):
                flash("passwords must match")
                return redirect(url_for('staffReg'))
        #verify id check
            if(idNum != i2):
                flash("id number could not be verified")
                return redirect(url_for('staffReg'))
            if(type(idNum) != int):
                flash("invalid ID")
                return redirect(url_for('staffReg'))
       
        #name, email, username, and password are required
            if not firstName:
                flash("Please enter your first name")
                return redirect(url_for('staffReg'))
            if not lastName:
                flash("Please enter your last name")
                return redirect(url_for('staffReg'))
            if not email:
                flash("Please enter your email")
                return redirect(url_for('staffReg'))
            if not user:
                flash("Please select a unique username")
                return redirect(url_for('staffReg'))
            if not year:
                flash("Please select a year")
                return redirect(url_for('staffReg'))
            if not password:
                flash("Please select a password")
                return redirect(url_for('staffReg'))
        #arbitrary length on password limit
            if len(password) > 16:
                flash("Please select a password fewer than sixteen characters")
                return redirect(url_for('staffReg'))

        #code to check tables for existing usernames, emails, and ID num since these should be unique per account
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Staff WHERE userID=:un)""",{"un":user})
            checkUser1=cur.fetchone()[0]
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Staff WHERE email=:em)""",{"em":email})
            checkEmail1=cur.fetchone()[0]
            
            if (checkUser1):
                flash("username is taken")
                return redirect(url_for('staffReg'))
            if (checkEmail1):
                flash("email address is already registered")
                return redirect(url_for('staffReg'))

        #check id only for student and staff users
   
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Staff WHERE sID=:in)""",{"in":idNum})
            checkIDnum1=cur.fetchone()[0]
            if(checkIDnum1):
                flash("id number is already registered")
                return redirect(url_for('staffReg'))

        #staff user
            if(accType==1):
                try:
                    cur.execute("""INSERT INTO Staff VALUES (?,?,?,?,?,?,?,?,?)""",(user,hashPSW,idNum,firstName,lastName,email,tele, year,hashWord))
                    conn.commit()
                    flash("Registration Successful for Staff User! Please login.")
                    return redirect(url_for('staffLogin'))
                except:
                    return redirect(url_for('staffReg'))
        
        except Exception as e:
            #print(e, file=sys.stdout)
            redirect(url_for('staffReg'))
    return redirect(url_for('staffReg'))

@app.route("/stuReg", methods=["GET","POST"])
def stuReg():
    if request.method == "GET":
        return render_template("stuReg.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:
            accType = 2
            idNum = int(request.form['idNum'])
            i2 = int(request.form['id_two'])
            year = int(request.form["year"])
            school = request.form["school"]
  
            try:
                tele = request.form["tele"]
            except:
                tele = -1

            firstName = request.form["firstName"]
            lastName = request.form["lastName"]
            email = request.form["email"]
            user = request.form["user"]
            password = str(request.form["password"])
            p2 = str(request.form["p_two"])
            word = str(request.form["word"])
            hashWord = generate_password_hash(word)
            hashPSW = generate_password_hash(password)
        #default raffleNum: not participating
            raffleNum = -1
        #default account balance
            balance = float(0)

        #check if user wants to participate in raffle and assign rand int 0-255, only added for student users
            if request.form.get("raffleTerms"):
                raffleNum = random.randint(1,10)

            if not word:
                flash("Please choose a secret word")
                redirect(url_for('stuReg'))
        #all users must agree to terms / (todo: create terms in html)
            if not request.form.get("agreement"):
                flash("Please read through and agree to the terms")
                return redirect(url_for('stuReg'))

        #check phone #
            if(tele == -1):
                flash("enter a phone #")
                return redirect(url_for('stuReg'))

        #check email format
            if('@' not in email):
                flash("invalid email address")
                return redirect(url_for('stuReg'))
        #password matching check
            if(password != p2):
                flash("passwords must match")
                return redirect(url_for('stuReg'))
        #verify id check
            if(idNum != i2 and accType==2):
                flash("id number's could not be verified")
                return redirect(url_for('stuReg'))
            if(type(idNum) != int and accType==2):
                flash("invalid ID")
                return redirect(url_for('stuReg'))
       
        #name, email, username, and password are required
            if not firstName:
                flash("Please enter your first name")
                return redirect(url_for('stuReg'))
            if not lastName:
                flash("Please enter your last name")
                return redirect(url_for('stuReg'))
            if not email:
                flash("Please enter your email")
                return redirect(url_for('stuReg'))
            if not user:
                flash("Please select a unique username")
                return redirect(url_for('stuReg'))
            if not password:
                flash("Please select a password")
                return redirect(url_for('stuReg'))
            if not year:
                flash("Please select a year")
                return redirect(url_for('stuReg'))
        #arbitrary length on password limit
            if len(password) > 16:
                flash("Please select a password fewer than sixteen characters")
                return redirect(url_for('stuReg'))

        #code to check tables for existing usernames, emails, and ID num since these should be unique per account
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Students WHERE userID=:un)""",{"un":user})
            checkUser2=cur.fetchone()[0]
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Students WHERE email=:em)""",{"em":email})
            checkEmail2=cur.fetchone()[0]
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Students WHERE sID=:in)""",{"in":idNum})
            checkIDnum2=cur.fetchone()[0]
    
            if (checkUser2 or checkEmail2 or checkIDnum2):
                flash("username, email, or id is already taken")
                return redirect(url_for('stuReg'))

        #student users
            if(accType==2):
                try:
                    cur.execute("""INSERT INTO Students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",(user,hashPSW,idNum,firstName,lastName,email,tele,year,school,raffleNum, balance, hashWord))
                    conn.commit()
                    flash("Registration Successful for Student User! Please login.")
                    return redirect(url_for('stuLogin'))
                except:
                    return redirect(url_for('stuReg'))
        except Exception as e:
            #print(e, file=sys.stdout)
            redirect(url_for('stuReg'))
    return redirect(url_for('stuReg'))

@app.route("/commReg", methods=["GET","POST"])
def commReg():
    if request.method == "GET":
        return render_template("commReg.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:
            accType = 3

            try:
                tele = request.form["tele"]
            except:
                tele = -1

            firstName = request.form["firstName"]
            lastName = request.form["lastName"]
            email = request.form["email"]
            user = request.form["user"]
            password = str(request.form["password"])
            p2 = str(request.form["p_two"])
            word = str(request.form["word"])
            hashWord = generate_password_hash(word)
            hashPSW = generate_password_hash(password)
      
        #default account balance
            balance = float(0)
    
            if not word:
                flash("Please choose a secret word")
                return redirect(url_for('commReg'))
        #all users must agree to terms / (todo: create terms in html)
            if not request.form.get("agreement"):
                flash("Please read through and agree to the terms")
                return redirect(url_for('commReg'))

        #check phone #
            if(tele == -1):
                flash("enter a phone #")
                return redirect(url_for('commReg'))

        #check email format
            if('@' not in email):
                flash("invalid email address")
                return redirect(url_for('commReg'))
        #password matching check
            if(password != p2):
                flash("passwords must match")
                return redirect(url_for('commReg'))

       
        #name, email, username, and password are required
            if not firstName:
                flash("Please enter your first name")
                return redirect(url_for('commReg'))
            if not lastName:
                flash("Please enter your last name")
                return redirect(url_for('commReg'))
            if not email:
                flash("Please enter your email")
                return redirect(url_for('commReg'))
            if not user:
                flash("Please select a unique username")
                return redirect(url_for('commReg'))
            if not password:
                flash("Please select a password")
                return redirect(url_for('commReg'))
        #arbitrary length on password limit
            if len(password) > 16:
                flash("Please select a password fewer than sixteen characters")
                return redirect(url_for('commReg'))

        #code to check tables for existing usernames, emails, and ID num since these should be unique per account
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Community WHERE userID=:un)""",{"un":user})
            checkUser3=cur.fetchone()[0]
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Community WHERE email=:em)""",{"em":email})
            checkEmail3=cur.fetchone()[0]
            
            if (checkUser3 or checkEmail3):
                flash("username or email already taken")
                return redirect(url_for('commReg'))
    
        #community users        
            if(accType==3):
                try:
                    cur.execute("""INSERT INTO Community VALUES (?,?,?,?,?,?,?,?)""",(user,hashPSW,firstName,lastName,email,tele,balance,hashWord))
                    conn.commit()
                    flash("Registration Successful for Community User! Please login.")
                    return redirect(url_for('commLogin'))
                except:
                    return redirect(url_for('commReg'))
                
        except Exception as e:
            #print(e, file=sys.stdout)
            redirect(url_for('commReg'))
    return redirect(url_for('commReg'))
#end registration 

#begin pw reset
@app.route("/passwordHelpHome", methods=["GET","POST"])
def passwordHelpHome():
    if request.method == "GET":
        return render_template("passwordHelpHome.html")

@app.route("/staffHelp", methods=["GET","POST"])
def staffHelp():
    if request.method == "GET":
        return render_template("staffPasswordHelp.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:  
            un = request.form.get("user")  
            w = request.form.get("word")
            p1 = request.form.get("p1")
            p2 = request.form.get("p2")
        except:
            w=-1
            p1=-1
            p2=-2

        if ((w or p1) == -1):
            flash(" invalid. Try Again.")
            return render_template("staffPasswordHelp.html")
        if not un:
            flash(" invalid user. Try Again.")
            return render_template("staffPasswordHelp.html")

        if (p1 != p2):
            flash(" passwords do not match")
            return render_template("staffPasswordHelp.html")

        cur.execute("""SELECT wordHash FROM Staff WHERE userID=:un""",{"un":un})
        checkHash1=cur.fetchone()[0]
        if(check_password_hash(checkHash1, w)):
            newHashPSW = generate_password_hash(p1)
            try:
                cur.execute("""UPDATE Staff SET hash=:x WHERE userID=:un""",{"x":newHashPSW,"un":un})
                conn.commit()
                flash("Update Successful for Staff User! Please login.")
                return redirect(url_for('staffLogin'))
            except:
                return render_template("staffPasswordHelp.html")
                
        else:
            flash("invalid credentials. Please try again.")
            return render_template("staffPasswordHelp.html")
   
@app.route("/stuHelp", methods=["GET","POST"])
def stuHelp():
    if request.method == "GET":
        return render_template("stuPasswordHelp.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:  
            un = request.form.get("user")  
            w = request.form.get("word")
            p1 = request.form.get("p1")
            p2 = request.form.get("p2")
        except:
            w=-1
            p1=-1
            p2=-2

        if ((w or p1) == -1):
            flash(" invalid. Try Again.")
            return render_template("stuPasswordHelp.html")
        if not un:
            flash(" invalid user. Try Again.")
            return render_template("stuPasswordHelp.html")

        if (p1 != p2):
            flash(" passwords do not match")
            return render_template("stuPasswordHelp.html")

        cur.execute("""SELECT wordHash FROM Students WHERE userID=:un""",{"un":un})
        checkHash1=cur.fetchone()[0]
        if(check_password_hash(checkHash1, w)):
            newHashPSW = generate_password_hash(p1)
            try:
                cur.execute("""UPDATE Students SET hash=:x WHERE userID=:un""",{"x":newHashPSW,"un":un})
                conn.commit()
                flash("Update Successful for Student User! Please login.")
                return redirect(url_for('stuLogin'))
            except:
                return render_template("stuPasswordHelp.html")
    
        else:
            flash("invalid credentials. Please try again.")
            return render_template("stuPasswordHelp.html")
 
@app.route("/commHelp", methods=["GET","POST"])
def commHelp():
    if request.method == "GET":
        return render_template("commPasswordHelp.html")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:  
            un = request.form.get("user")  
            w = request.form.get("word")
            p1 = request.form.get("p1")
            p2 = request.form.get("p2")
        except:
            w=-1
            p1=-1
            p2=-2

        if ((w or p1) == -1):
            flash(" invalid. Try Again.")
            return render_template("commPasswordHelp.html")
        if not un:
            flash(" invalid user. Try Again.")
            return render_template("commPasswordHelp.html")

        if (p1 != p2):
            flash(" passwords do not match")
            return render_template("commPasswordHelp.html")

        cur.execute("""SELECT wordHash FROM Community WHERE userID=:un""",{"un":un})
        checkHash1=cur.fetchone()[0]
        if(check_password_hash(checkHash1, w)):
            newHashPSW = generate_password_hash(p1)
            try:
                cur.execute("""UPDATE Community SET hash=:x WHERE userID=:un""",{"x":newHashPSW,"un":un})
                conn.commit()
                flash("Update Successful for Staff User! Please login.")
                return redirect(url_for('commLogin'))
            except:
                return render_template("commPasswordHelp.html")

        else:
            flash("invalid credentials. Please try again.")
            return render_template("commPasswordHelp.html")
#end pw reset


#begin rent
@app.route("/rent",methods=["GET","POST"])
@login_required
@special_requirement2
def rent():
    if request.method == "GET":
        #only students see this data
        try:
            conn = get_db()
            cur = conn.cursor()
            user = session['user']

        
            #students with one reservation cannot reserve again
            cur.execute("""SELECT EXISTS(SELECT 1 FROM Reserve WHERE userID=:un)""",{"un":user})
            checkUser1 = cur.fetchone()[0]
            if(checkUser1):
                flash("You have already reserved a bike. Please unreserve in 'My Bike' ")
                return redirect(url_for('homePage'))

            cur.execute("""SELECT raffleNo FROM Students WHERE userID=:un""",{"un":user})
            stuRaffleNo = cur.fetchone()[0]

            cur.execute("""SELECT MaxRaffleNo FROM RaffleLimit""")
            maxRaffleNo = cur.fetchone()[0]

            #check student raffle # against max
            if(stuRaffleNo > maxRaffleNo):
                flash("Invalid raffle number, try again later")
                return redirect(url_for('homePage'))


            cur.execute("""SELECT * FROM GB WHERE available=1""")
            bike_data = cur.fetchall()

            return render_template("rent.html", data=bike_data)
        except Exception as e:
            print(e, file=sys.stdout)
            flash("Error")
            return redirect(url_for('homePage'))
    if request.method == "POST":
        #students post this data to rent
        conn = get_db()
        cur = conn.cursor()
        try:
            size = int(request.form.get("size"))
      
            cur.execute("""SELECT EXISTS(SELECT 1 FROM GB WHERE size=:x)""",{"x":size})
            checkSize = cur.fetchone()[0]
            if not checkSize:
                flash("no matches returned from search")
                cur.execute("""SELECT * FROM GB WHERE available=1""")
                bike_data = cur.fetchall()
                return render_template("rent.html", data=bike_data)
            

            cur.execute("""SELECT * FROM GB WHERE size=:x AND available=1""",{"x":size})
            filteredData = cur.fetchall()

            return render_template("rent.html", data=filteredData)
        except:
            try:
                
                bikeNo = int(request.form.get('bikeNo'))
                user = session["user"]

            #check available again incase another user already added
                cur.execute("""SELECT available FROM GB WHERE BikeNo=:m""",{"m":bikeNo})
                checkAvail = cur.fetchone()[0]

            #available may have been changed by another user so we recheck here
                if(checkAvail):

            #print(bikeNo, file=sys.stdout)
                    cur.execute("""INSERT INTO Reserve VALUES (?,?,?)""",(user,bikeNo,0))
                    conn.commit()
                    
                    cur.execute("""UPDATE GB SET available=:x WHERE BikeNo=:y""",{"x":False,"y":bikeNo})
                    conn.commit()

                    flash("Resevation Successful! See My Bike for your reservation.")
                    return redirect(url_for('homePage'))
                else:
                    flash("Resevation Unuccessful! Bike already reserved")
                    return redirect(url_for('rent'))

            except Exception as e:
                #print(e, file=sys.stdout)
                return redirect(url_for('homePage'))



@app.route("/manageRent",methods=["GET","POST"])
@login_required
@special_requirement2
def manageRent():
    if request.method == "GET":
        try:
            user = session['user']
            conn = get_db()
            cur = conn.cursor()

            cur.execute("""SELECT BikeNo FROM Reserve WHERE userID=:x""",{"x":user})
            bike = cur.fetchone()[0]
            
            cur.execute("""SELECT * FROM GB WHERE BikeNo=:y""",{"y":bike})
            bike_data2 = cur.fetchall()

            cur.execute("""SELECT date,notes,status FROM studentRepairRequest WHERE BikeNo=:y""",{"y":bike})
            data3 = cur.fetchall()

            cur.execute("""SELECT status FROM Reserve WHERE BikeNo=:y""",{"y":bike})
            condition1 = cur.fetchone()[0]

            return render_template("manageRent.html",data=bike_data2, reqData=data3,check=condition1)
        except Exception as e:
            #print(e, file=sys.stdout)
            flash("Error. No bike reservation. First reserve a bike under 'Rent'.")
            return redirect(url_for('homePage'))
    if request.method == "POST":
        #students post this data 
        conn = get_db()
        cur = conn.cursor()
        try:
            bikeNo = int(request.form.get('bikeNo'))
            user = session["user"]

            cur.execute("""SELECT status FROM Reserve WHERE userID=:x""",{"x":user})
            status = cur.fetchone()[0]

            if(status!=1):
                cur.execute("""DELETE FROM Reserve WHERE userID=:x""",{"x":user})
                conn.commit()
                cur.execute("""UPDATE GB SET available=:z WHERE BikeNo=:y""",{"z":True,"y":bikeNo})
                conn.commit()
                flash("Unreserve Successful! You may reserve another bike")
                return redirect(url_for('homePage'))
            else:
                flash("Unreserve unuccessful! You must first return your bike first")
                return redirect(url_for('manageRent'))
    
               

        except Exception as e:
            #print(e, file=sys.stdout)
            flash("bike already returned")
            return redirect(url_for('homePage'))
#end rent
   
#begin repair
@app.route("/stuRepair",methods=["POST"])
def stuRepairRequest():
    if request.method == "POST":
        #students post this data 
        conn = get_db()
        cur = conn.cursor()
        try:
            date = request.form.get('visitDate')
            notes = request.form.get('notes')
            user = session["user"]

            if not date:
                flash("Error. Enter a date to come in!")
                return redirect(url_for('manageRent'))
            
            if not notes:
                flash("Error. Enter a description!")
                return redirect(url_for('manageRent'))

            cur.execute("""SELECT BikeNo FROM Reserve WHERE userID=:x""",{"x":user})
            bike = cur.fetchone()[0]


            cur.execute("""SELECT status FROM Reserve WHERE userID=:x""",{"x":user})
            check1 = cur.fetchone()[0]

            if (check1==0):
                flash("Invalid Request. You are have not been confirmed for this bike")
                return redirect(url_for('manageRent'))


            progress = 0

            cur.execute("""INSERT INTO studentRepairRequest VALUES (?,?,?,?,?,?,?)""",(user,bike,date,notes,'Sent to Shop',progress,None))
            conn.commit()
            flash("Request Successful! Check Back on the status.")
            return redirect(url_for('manageRent'))

        except Exception as e:
            #print(e, file=sys.stdout)
            flash("Invalid Request")
            return redirect(url_for('manageRent'))


@app.route("/commRepair",methods=["GET","POST"])
@login_required
def commRepairRequest():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "GET":
        user = session["user"]
        cur.execute("""SELECT date,notes,status FROM commRepairRequest WHERE userID=:y""",{"y":user})
        data3 = cur.fetchall()
        return render_template('commRepair.html',data3=data3)
    if request.method == "POST":
        #comm. users post this data 
        try:
            user = session["user"]
            model = request.form.get('model')
            year = request.form.get('year')
            date = request.form.get('visitDate')
            notes = request.form.get('notes')
            

            if not date:
                flash("Error. Enter a date to come in!.")
                return redirect(url_for('commRepairRequest'))
            
            if not notes:
                flash("Error. Enter description!")
                return redirect(url_for('commRepairRequest'))

            progress = 0

            cur.execute("""INSERT INTO commRepairRequest VALUES (?,?,?,?,?,?,?,?)""",(user,model,year,date,notes,'Req sent to Shop',progress,None))
            conn.commit()
            flash("Request Successful! Check back later on the status.")
            return redirect(url_for('commRepairRequest'))

        except Exception as e:
            print(e, file=sys.stdout)
            flash("Invalid Request")
            return redirect(url_for('commRepairRequest'))

#end repair


#logout function
@app.route("/logout")
@login_required
def logout():
    session['logged'] = False 
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('homePage'))

      
