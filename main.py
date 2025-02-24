### IMPORTS ###
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, EmailField, StringField
import smtplib
from dotenv import load_dotenv
import os
import json
import pandas as pd
from email.message import EmailMessage

### FUNCTIONS ###
def convert_date_format(date: str) -> str:
    """Expects date as a string in the format 'YYYY-MM'.
    Converts date into 'Month YYYY' format.
    If date is null, returns null."""

    if date is None:
        return date
    
    if not isinstance(date, str):
        raise TypeError('date is not a string')

    date = pd.to_datetime(date)
    return f"{date.month_name()} {date.year}" 

def sendEmail(sender: str, subject:str, message: str) -> None:
    try:
        if not isinstance(sender, str):
            raise TypeError(f":sender: is not a string")
        if not isinstance(subject, str):
            raise TypeError(f":subject: is not a string")
        if not isinstance(message, str):
            raise TypeError(f":message: is not a string")
    except TypeError as e:
        return e

    username = os.environ.get('EMAIL_USERNAME')
    password = os.environ.get('EMAIL_PASSWORD')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['Reply-To'] = sender
    msg['To'] = 'wm706513@ohio.edu'
    msg.set_content(f'From: {sender}\nSubject: {subject}\n\n{message}')

    try:
        server = smtplib.SMTP(host='smtp.gmail.com', port=587)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        return e
    else:
        return True

### CLASSES ###
class ContactForm(FlaskForm):
    email = EmailField(label='Email')
    subject = StringField(label='Subject')
    message = TextAreaField(label='Message')
    submit = SubmitField(label='Submit')

### INITIALIZATION ###
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

### DATA ###
with open('./static/data/portfolio.json', 'r') as file:
    projects = json.load(file)
    projects = sorted(projects, key=lambda proj: (proj['startDate'], proj['endDate']), reverse=True) #sort so most recent start date is first, then most recent end date in event of ties

    for project in projects:
        project['startDate'] = convert_date_format(project['startDate'])
        project['endDate'] = convert_date_format(project['endDate'])
        project['tags'] = ' '.join(project['tags'])

with open('./static/data/skills.json', 'r') as file:
    skills = json.load(file)

### ENDPOINTS ###
@app.route('/')
def index():
    return render_template('index.html', methods=['GET'])

@app.route('/about')
def about():
    return render_template('about.html', methods=['GET'])

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html', methods=['GET'], projects=projects, skills=skills)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    form_redirect = False
    error = False

    # Check if redirected from form, then reset to False
    if session.get('form_redirect'):
        form_redirect = True
    session['form_redirect'] = False

    # Check if error on email send, then reset to False
    if form_redirect and session.get('error'):
        error = True
    session['error'] = False

    if form.validate_on_submit():
        err = (sendEmail(form.email.data, form.subject.data, form.message.data) is not True) #is False only if no exception occurred, otherwise is True
        session['form_redirect'] = True
        if err:
            session['error'] = True
        else:
            session['error'] = False
        return redirect(url_for('contact'))  #prevents asking to resubmit every time refresh happens

    return render_template('contact.html', form=form, form_redirect=form_redirect, error=error)



### MAIN ###
if __name__ == '__main__':
    app.run(debug=True)