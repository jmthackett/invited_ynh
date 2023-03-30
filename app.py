from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import uuid
import logging

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

# define a route for the invite code generation page
@app.route('/', methods=['GET', 'POST'])
def generate_invite():
    if request.method == 'POST':

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
        try:
            invite = db.session.execute(db.select(Invite).filter_by(invite_code=invite_code)).scalar_one()
            logging.info(f"{invite_code} use status: {invite.used}")
            if invite.used == False:
        #name = request.form['name']
        #email = request.form['email']

            # TODO: set invite code status to 'used'
                invite.used = True
                db.session.commit()
                logging.error(f"{invite_code} has been set to used")
            else:
                logging.error(f"{invite_code} is set to used: aborting")
            # TODO: sudoers.d
            # %invited ALL = /path/to/yunohost user create*
            # %invited ALL = /path/to/yunohost user group add invitees*

            # TODO: Popen from this app
            # yunohost user create -F -d -p
            # yunohost user group add invitees user

            # TODO: Setup stage, from YNH app packaging
            # yunohost user permissions add xmpp invitees
        except Exception as e:
            print(str(e))
            pass

        return redirect(url_for('thank_you'))
    # render the form page with the invite code as a parameter
    return render_template('fill_form.html', invite_code=invite_code)

# define a route for the thank you page
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
