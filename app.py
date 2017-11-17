from flask import Flask, render_template, flash, request, url_for, redirect, session
from dbconnect import connection
from wtforms import Form, TextField, validators, FloatField, SubmitField, PasswordField
from MySQLdb import escape_string as thwart
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_uploads import UploadSet, IMAGES, configure_uploads
from werkzeug import secure_filename
from werkzeug.contrib.cache import SimpleCache
from flask_caching import Cache
from passlib.hash import sha256_crypt
import gc, os, random

#gc = garbage collector
#os = using operating system dependent functionality

CACHE_TIMEOUT = 600

app = Flask(__name__)
app.secret_key = "super secret key"

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["CACHE_TYPE"] = "simple"

app.cache = Cache(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#class form for Delete
class ReusableForm(Form):
	ID = TextField('StudentID', [validators.Length(min=6, max = 10)])

#class form for Edit
class EditForm(Form):
	stuid = TextField('StudentID', [validators.Length(min=6, max = 10)])
	name = TextField('Name', [validators.Length(min=6, max = 30)])
	gender = TextField('Gender', [validators.Length(min=3, max = 7)])
	phone = TextField('Phone', [validators.Length(min=10, max = 15)])

#class form for Record
class RecordForm(Form):
	stuid = TextField('StudentID', [validators.Length(min=6, max = 10)])
	name = TextField('Name', [validators.Length(min=6, max = 30)])
	gender = TextField('Gender', [validators.Length(min=3, max = 7)])
	phone = TextField('Phone', [validators.Length(min=10, max = 15)])

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    password = PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('main.html')
    return render_template("upload.html")

@app.route('/record/', methods=["GET","POST"])
def record_page():
	try:
		form = RecordForm(request.form)
		if request.method == "POST" and form.validate():
			stuid = form.stuid.data
			name = form.name.data
			gender = form.gender.data
			phone = form.phone.data
			file = request.files['file']
			if file.filename == ' ':
				flash("No selected file")
				return redirect(request.url)
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			file_path =  UPLOAD_FOLDER + '/' + filename
			print file_path
			c, conn = connection()

			c.execute("INSERT INTO student (stu_id, name, gender, phone, avatar) VALUES (%s, %s, %s, %s, %s)", (thwart(stuid), thwart(name), thwart(gender), thwart(phone), thwart(file_path)))

			conn.commit()
			flash("Thank you for your information")
			c.close()
			conn.close()
			gc.collect()
			return render_template('main.html')
		return render_template("record.html", form=form)
	except Exception as e:
		return(str(e))

@app.route('/register/', methods=["GET","POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username  = form.username.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute("SELECT * FROM users WHERE username = (%s)",
                          (thwart(username)))

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)

            else:
                c.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                          (thwart(username), thwart(password)))
                
                conn.commit()
                flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return render_template("main.html")

        return render_template("register.html", form=form)

    except Exception as e:
        return(str(e))

@app.route('/showrecord', methods=['GET', 'POST'])
@app.cache.cached(timeout=50,key_prefix="hello")
def showrecord():
	a=random.randint(0,100)
	try:
		flash(a)
		c, conn = connection()

		c.execute('SELECT stu_id,name,gender,phone,avatar FROM student')
		data = c.fetchall()
		conn.close()
		return render_template("showrecord.html", data=data)
	except Exception as e:
		return (str(e))

#Delete a row in database
@app.route('/delete', methods=["GET", "POST"])
def delete():
	try:
		form = ReusableForm(request.form)
		if request.method == "POST" and form.validate():
			ID = form.ID.data
			c, conn = connection()
			x = c.execute("SELECT * FROM student WHERE stu_id = (%s)", (thwart(ID)))
			#Search ID in database
			if int(x) == 0:
				flash("StudentID is Not Valid")
				return render_template('delrecord.html', form=form)
			else:
				query = "delete from student where stu_id = '%s' " % ID
				c.execute(query)
				conn.commit()
				c.close()
				conn.close()
				return render_template("main.html")
		return render_template("delrecord.html", form=form)
	except Exception as e:
		return(str(e))


@app.route('/edit', methods=["GET", "POST"])
def edit():
	try:
		form = EditForm(request.form)
		if request.method == "POST" and form.validate():
			stuid = form.stuid.data
			name = form.name.data
			gender = form.gender.data
			phone = form.phone.data			

			c, conn = connection()

			x = c.execute("SELECT * FROM student WHERE stu_id = (%s)", (thwart(stuid)))

			if int(x) == 0:
				flash("StudentID is Not Valid")
				return render_template('edit.html', form=form)
			else:
				c.execute("UPDATE student SET name = (%s), gender=(%s), phone=(%s) WHERE stu_id = (%s)", (thwart(name), thwart(gender), thwart(phone),thwart(stuid)))
				conn.commit()
				c.close()
				conn.close()
				gc.collect()
				return render_template('main.html')
		return render_template("edit.html", form=form)
	except Exception as e:
		return(str(e))

@app.route('/login/', methods=["GET","POST"])
def login_page():
    error = ''
    try:
        c, conn = connection()
        if request.method == "POST":

            data = c.execute("SELECT * FROM users WHERE username = (%s)",
                             thwart(request.form['username']))
            
            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']

                flash("You are now logged in")
                return redirect(url_for("homepage"))

            else:
                error = "Invalid username or password, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        #flash(e)
        error = "Invalid username or password, try again."
        return render_template("login.html", error = error)  

@app.route("/logout/")
def logout():
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('homepage'))

@app.route('/')
def homepage():
    return render_template("main.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

'''@app.route('/record/', methods=["GET","POST"])
def record_page():
	try:
		c, conn = connection()
		return("okay")
	except Exception as e:
		return(str(e))
'''
if __name__ == "__main__":
    app.run(host="0.0.0.0")