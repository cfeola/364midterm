###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, ValidationError# Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy

import requests
import json


## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/midterm_db"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################



##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64), unique=True)
    Locations = db.relationship('Locations',backref='Name')

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

    def __init__(self, name):
        self.name = name

class Locations(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    City = db.Column(db.String(280))
    State = db.Column(db.String(280))
    Restaurants = db.relationship('Restaurants',backref='Locations')
    Name_id = db.Column(db.Integer, db.ForeignKey('names.id'))

    def __repr__(self):
        return "{}, {}".format(self.City, self.State)


class Restaurants(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    Restaurant_Name = db.Column(db.String(280))
    Cuisine =  db.Column(db.String(280))
    Rating = Price = db.Column(db.String(280))
    Price = db.Column(db.String(280))
    Address = db.Column(db.String(500))
    Phone_Number = db.Column(db.String(280))
    Location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    def __repr__(self):
        return "{} {} {} {} {} {}".format(self.Restaurant_Name, self.Cuisine,self.Rating, self.Price, self.Address,self.Phone_Number)


class Contacts(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    Name = db.Column(db.String(280), unique=True)
    Email = db.Column(db.String(280), unique=True)
    Phone = db.Column(db.String(280), unique=True)

    def __repr__(self):
        return "{}, {}, {}".format(self.Name, self.Email, self.Phone)

###################
###### FORMS ######
###################

class WelcomeForm(FlaskForm):
    choice = RadioField("What would you like to do?", choices=[('1','Search for a restaurant'),('2','See what others have searched for')], validators=[Required()])
    submit = SubmitField()

class SearchForm(FlaskForm):
    name = StringField("Please enter your first and last name.",validators=[Required()])
    city = StringField('Enter the name of the city.',validators=[Required()])
    state = StringField('Enter the name of the state.',validators=[Required()])
    cuisine = StringField('Enter the type of cuisine.',validators=[Required()])
    price = StringField('Enter the price level (1 = $, 2 = $$, 3 = $$$, 4 = $$$$).',validators=[Required()])
    submit = SubmitField()

    def validate_name(self,field):
        spaces = 0
        for char in field.data:
            if char == " ":
                spaces += 1
        if spaces == 0:
            raise ValidationError("Please enter your first AND last name separated by a space.")

    def validate_state(self,field):
        if len(field.data) <= 2:
            raise ValidationError("Please enter the full name of the state - not the state's abbreviation.")

    def validate_price(self, field):
        if field.data not in ['1','2','3','4']:
            raise ValidationError("Please enter a number between 1 and 4.")



class Complete(FlaskForm):
    done = RadioField("Would you like to search for more restaurants?", choices=[('Yes','Yes'),('No','No')], validators=[Required()])
    submit = SubmitField()

class Evaluation(FlaskForm):
    eval = RadioField("Did you have a positive experience using our website?", choices=[('Yes','Yes'),('No','No')], validators=[Required()])
    submit = SubmitField()

class Contact(FlaskForm):
    Name = StringField("Please enter your first and last name.",validators=[Required()])
    Email = StringField("Please enter your e-mail address.",validators=[Required()])
    Phone = StringField("Please enter your phone number.",validators=[Required()])
    submit = SubmitField()

#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/',methods=['GET','POST'])
def home():
    form = WelcomeForm() 
    if form.validate_on_submit():
        choice = form.choice.data
        if choice == '1':
            return redirect(url_for('search'))
        if choice == '2':
            return redirect(url_for('restaurants'))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('base.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/search',methods=['GET','POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():        
        access_token = "C8ntKALJDEPi_xP0MY7VbQXOEDuAIEGCJnCjcmheNq3X1uFSf2pUg4ggHsZFdPap8CpSFPC9-MN9aZE0M4eZqkN1h3bh_s0kjkjCAppJw-JoNfZDi0MTQtTqIaOgWnYx"
        api_url = "https://api.yelp.com/v3/businesses/search"
        
        name = form.name.data
        city = form.city.data
        state = form.state.data
        location = city + ", " + state
        cuisine = form.cuisine.data
        price = form.price.data

        if not Name.query.filter_by(name=name).first():
            new_user = Name(name=name)
            db.session.add(new_user)
            db.session.commit()
        
        user = Name.query.filter_by(name=name).first()
        user_id = user.id

        new_location = Locations(City = city, State = state, Name_id = user_id)
        db.session.add(new_location)
        db.session.commit()

        params_dict = {'term':cuisine,'location':city, 'price':price, 'limit':5}
        headers = {'Authorization': 'bearer %s' % access_token}
        resp = requests.get(api_url, params = params_dict, headers=headers)
        data = json.loads(resp.text)

        display = {}
        if 'error' not in data.keys():
            for place in data['businesses']:
                display[place['name']] = {}
                display[place['name']]['Rating (out of 5)'] = place['rating'] 
                display[place['name']]['Address'] = ' '.join(place['location']['display_address'])
                display[place['name']]['Phone Number'] = place['phone']
                display[place['name']]['Link to website'] = place['url']
                display[place['name']]['Price Range'] = place['price']
                category_list = []
                for each in place['categories']:
                    category_list.append(each['title'])
                display[place['name']]['Cuisine'] = ', '.join(category_list)

                
                if Locations.query.filter_by(City = place['location']['city'], Name_id=user_id).first():
                    location = Locations.query.filter_by(City = place['location']['city'], Name_id=user_id).first()
                    new_restaurant = Restaurants(Restaurant_Name= place['name'], Cuisine = display[place['name']]['Cuisine'], Rating=place['rating'], Price =place['price'], Address = display[place['name']]['Address'], Phone_Number = place['phone'],Location_id = location.id)
                    db.session.add(new_restaurant)
                    db.session.commit()
        
            return render_template('results.html', data = display)
        else:
            flash("Sorry, we couldn't find any restaurants to match your criteria.")
            return redirect(url_for('doneForm'))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('search.html',form=form)

@app.route('/cities',methods=['GET','POST'])
def cities():
    cities = Locations.query.all()
    return render_template('cities.html',cities=cities)

@app.route('/restaurants',methods=['GET','POST'])
def restaurants():
    restaurants = Restaurants.query.all()
    return render_template('restaurants.html',restaurants=restaurants)

@app.route('/doneForm')
def doneForm():
    form = Complete()
    return render_template('done.html',form=form)
   
@app.route('/eval',methods=['GET','POST'])
def eval():
    form = Evaluation()
    return render_template('eval.html',form=form)

@app.route('/evalResults',methods=['GET','POST'])
def evalResults():
    form = Evaluation()
    if request.args:
        return render_template('contact.html', form = Contact())
    return redirect(url_for('eval'))

@app.route('/doneResults',methods=['GET','POST'])
def doneResults():
    form = Complete()
    if request.args:
        done = request.args.get('done')
        print(done)
        if done == "Yes":
            return redirect(url_for('search'))
        else:
            return render_template('thanks.html')
    return redirect(url_for('doneForm'))

@app.route('/thanks',methods=['GET','POST'])
def thanks():
    form = Contact()
    if form.validate_on_submit():
        name = form.Name.data
        email = form.Email.data
        phone = form.Phone.data
        
        if not Contacts.query.filter_by(Name=name, Email = email, Phone=phone).first():
            new_contact = Contacts(Name=name, Email= email, Phone=phone)
            db.session.add(new_contact)
            db.session.commit()
            return render_template('thanks.html')
        else:
            flash("ERROR: You've already submitted an evaluation form.")
            return render_template('thanks.html')
    return redirect(url_for('thanks'))

@app.route('/contacts',methods=['GET','POST'])
def contacts():
    contacts = Contacts.query.all()
    return render_template('contact_info.html',contacts=contacts)


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    db.create_all() 
    app.run(use_reloader=True,debug=True) 