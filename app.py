# importing required modueles
from flask import Flask, render_template, redirect, request,url_for, session, flash
import random
from database.tables import create_tables
from database.utility import addUser
from database.utility import checkUserStatus, getPasswordFromDB, updatePassword
from emailsend import emailSend
from database.utility import addNotesInDB

from itsdangerous import URLSafeTimedSerializer
from itsdangerous import SignatureExpired, BadSignature

app = Flask(__name__)
app.secret_key = "srinubabu@123"

# secure time based url serializer
serializer = URLSafeTimedSerializer(app.secret_key)


#home route
@app.route('/')
def home():
    return render_template('home.html')

#login route
@app.route('/login', methods=['GET',"POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if checkUserStatus(username=username):
            if getPasswordFromDB(username=username) == password:
                token = serializer.dumps(
                    username,
                    salt = 'login-auth'
                )

                return redirect(url_for('dashboard', token =token))
            return render_template('login.html',msg = "Invalid credenticalis")

        return render_template('login.html',msg = "username not found")

    return render_template('login.html')


# getnerate otp token
def generate_otp_token(email):
    otp = random.randint(1000,9999)
    token = serializer.dumps(
        {"email":email, "otp":otp},
        salt = "register_otp"
    )
    return otp, token

# register route
@app.route('/register', methods=['GET',"POST"])
def register():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        session['email'] = request.form['email']
        
        if not checkUserStatus(session['email']) == True:
            # generate otp
            otp, token = generate_otp_token(session['email'])
            print("Registe_otp token:",token)
            session['register_otp_token'] = token
            # otp send via email

            # print('------------Assume like this otp came \
                #   via email:',otp) 
            body = f"""
                    Dear customer {session['username']},
                    This mail is to vefiry your notes management app!!!
                    Verification OTP is:{otp}.

                    This OTP expires within 2 mins.
                    Don't replay to this email.

                    Best Regards
                    Notes App. 
                    """
            emailSend(
                to_email=session['email'],
                subject = "Notes Management OTP Verification",
                body = body
            )
            return redirect(url_for('verifyOTP', token=session['register_otp_token']))
        return render_template('register.html', msg = "Username email already exist")
    return render_template('register.html')

# verifyOTP route
@app.route("/register/verifyotp/<token>", methods=['GET','POST'])
def verifyOTP():
    if 'register_otp_token' not in session:
        redirect(url_for('register'))
    if request.method == "POST":
        try:
            entered_otp = int(request.form['otp'])
            data = serializer.loads(
                session['register_otp_token'],
                salt = "register_otp",
                max_age = 120 # 2 mins
            )
            # verify otp
            
            if entered_otp == data['otp']:
                # add new user to table
                
                add_user = addUser(
                    username=session['username'],
                    email= session['email'],
                    password=session['password']
                )
                
                if add_user==True:
                    
                    session.pop('username')
                    session.pop('email')
                    session.pop('password')        
                    return render_template('login.html', msg ='User registred successfully')
        except SignatureExpired:
            return redirect(url_for("verifyOTP", msg ='OTP Expired'))
        except BadSignature:
            return redirect(url_for("verifyOTP", msg ='Invalid OTP URL'))
        return redirect(url_for("verifyOTP", msg ='Invalid otp'))
        

    return render_template('verifyotp.html')





# -----------------------forgot password-----------------------------------
@app.route('/forgotPassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        if checkUserStatus(username=email):
            # generating forgot password token
            token = serializer.dumps(email, salt = 'forgot-password')
            

            # generate reset link
            # reset_link = url_for('reset_password', token= token, _external = True)
            reset_link = url_for('reset_password', token=token, _external=True)

            # send reset password link via email
            body = f"""
                    Dear customer ,
                    This mail is to update notes management app password !
                    Password reset link:{reset_link}.

                    This link expires within 10 mins.
                    Don't replay to this email.

                    Best Regards
                    Notes App. 
                    """

            emailSend(
                to_email= email,
                subject="Notes App password reset request!",
                body = body
            )
            return redirect(url_for('login', msg = "check you email! Successfully \
                                    Password reset link send"))
        
        return redirect(url_for('login', msg = "User Email not found!!!"))

    return render_template('forgot_password.html')

@app.route('/resetPassword/<token>', methods=['GET','POST'])
def reset_password(token):
   
    # get email from token
    try:
        email = serializer.loads(token,
                             salt = 'forgot-password',
                             max_age=600)
    except SignatureExpired:
        return redirect(url_for('forgot_password', msg = "Link Expired"))
    except BadSignature:
        return redirect(url_for('forgot_password', msg = "Incorret url"))
    
    # get data from form
    if request.method == 'POST':
        new_password = request.form['password']

        # update new password in database
        if updatePassword(email=email,new_password=new_password):
            # redirect to login page
            return redirect(url_for('login', msg = "Password reset successfully"))
        return redirect(url_for('login', msg = "Password not updated"))
    return render_template('reset_password.html', token=token)

# ------------------------------------


# get email from login-auth token
def verify_login_token(token):
    try:
        email = serializer.loads(
            token,
            salt = 'login-auth',
            max_age=7200
        )
        return email
    except:
        return None
    

#dashboard route
@app.route('/dashboard/<token>', methods=['GET', 'POST'])
def dashboard(token):
    email = verify_login_token(token)
    if not email:
        return redirect(url_for('login',msg = "Session expired"))
    


    return render_template('dashboard.html', token=token, username = email)

## add new notes route
@app.route('/dashboard/addnotes/<token>', methods=['GET', 'POST'])
def add_notes(token):
    email = verify_login_token(token)
    if not email:
        return redirect(url_for('login',msg = "Session expired"))
    if request.method == 'POST':
        title = request.form('title')
        content = request.form('content')


        # add notes in database
        if addNotesInDB(email=email, title=title, content=content):
        
        
            #redirect to dashboard
            return redirect(url_for("dashboard",token=token, msg = "Notes added"))
        else:
            return redirect(url_for("add_notes", msg = "Notes not updated"))

    return render_template('add_notes.html', token=token)




if __name__ == '__main__':
    create_tables()
    app.run(debug = True, port =5004 )