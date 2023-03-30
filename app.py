from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import uuid
import logging
import shlex, subprocess
import re
from email_validator import validate_email, EmailNotValidError

logging.basicConfig(level=logging.DEBUG)

db = SQLAlchemy()
app = Flask(__name__)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///invited.db"
# initialize the app with the extension
db.init_app(app)

class Invite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inviter_ynh_username = db.Column(db.String, nullable=False)
    invitee_email = db.Column(db.String, unique=True, nullable=False)
    invite_code = db.Column(db.String, unique=True, nullable=False)
#    used_time = db.Column(db.DateTime, nullable=True)
    used = db.Column(db.Boolean)

def check_username(username):
    if not username.replace(" ", "").isalpha():
        return False
    exists = subprocess.Popen(["yunohost", "user", "info", username])
    if exists.returncode != 0:
        return False
    return True

# define a route for the invite code generation page
@app.route('/', methods=['GET', 'POST'])
def generate_invite():
    if request.method == 'POST':

        try:
            validation = validate_email(request.form['email'], check_deliverability=True)
        except EmailNotValidError as e:
            logging.info(str(e))
            return redirect(url_for('error'))

        invite_code = uuid.uuid1()
        invite = Invite(
          invitee_email=request.form['email'], 
          inviter_ynh_username="jahn", 
          invite_code=str(invite_code),
          used=False
        )

        db.session.add(invite)
        db.session.commit()

        return render_template('invite_generated.html', invite_code=invite_code)
    return render_template('generate_invite.html')

# define a route for the form page
@app.route('/<invite_code>', methods=['GET', 'POST'])
def fill_form(invite_code):
    if request.method == 'POST':
        if not request.form['fullname'].replace(" ", "").isalpha():
            return redirect(url_for('error'))
        try:
            validation = validate_email(request.form['email'], check_deliverability=True)
        except EmailNotValidError as e:
            logging.info(str(e))
            return redirect(url_for('error'))
        
        try:
            invite = db.session.execute(db.select(Invite).filter_by(invite_code=invite_code)).scalar_one()
            logging.info(f"{invite_code} use status: {invite.used}")
            if invite.used == False:
                fullname = request.form['fullname']
                email = request.form['email']
          
                invite.used = True
                db.session.commit()
                logging.info(f"{invite_code} has been set to used")
                subprocess.Popen(
                    [
                        "yunohost",
                        "user",
                        "create",
                        request.form['username'],
                        "-F",
                        request.form['fullname'],
                        "-p", 
                        request.form['password']
                    ])
                logging.info(f"User created: {request.form['username']}")
                subprocess.Popen(["yunohost","user","group","add","invitees",request.form['username']])
                logging.info(f"User {request.form['username']} added to group invitees")
                return redirect(url_for('thank_you'))
            else:
                logging.error(f"{invite_code} is set to used: aborting")
                return redirect(url_for('already_used'))
            # TODO: sudoers.d
            # %invited ALL = /path/to/yunohost user create*
            # %invited ALL = /path/to/yunohost user group add invitees*

            # TODO: Setup stage, from YNH app packaging
            # yunohost user permissions add xmpp invitees
        except Exception as e:
            logging.error(str(e))
            return redirect(url_for('error'))

        return redirect(url_for('thank_you'))
    # render the form page with the invite code as a parameter
    return render_template('fill_form.html', invite_code=invite_code)

# define a route for the thank you page
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/error')
def error():
    return render_template('error.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
