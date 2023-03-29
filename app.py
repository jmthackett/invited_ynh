from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import uuid

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
          used=0
        )

        db.session.add(invite)
        db.session.commit()

        return render_template('invite_generated.html', invite_code=invite_code)
    return render_template('generate_invite.html')

# define a route for the form page
@app.route('/<invite_code>', methods=['GET', 'POST'])
def fill_form(invite_code):
    try:
        user = db.session.query(Invite).filter_by(invite_code=invite_code).one()
        if user:
            print(invite_code)
    except Exception:
        print("invalid code")
        pass

    # TODO: validate invite code
    if request.method == 'POST':
        form_data = {}
        form_data['name'] = request.form['name']
        form_data['email'] = request.form['email']
        invite_codes[invite_code].append(form_data)

        # TODO: set invite code status to 'used'
        # TODO: create user (subprocess.Popen)
        
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
