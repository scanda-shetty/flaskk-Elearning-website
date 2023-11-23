from flask import Flask, render_template, request, session, redirect, url_for, flash
import mysql.connector
from datetime import datetime
import json
from json import loads
import os
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.secret_key ="jusfondiaxylliphyt" 

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def login():
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port=3308,
        database="learning"
    )
    mycursor = mydb.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_regex, email):
            flash("Invalid email address. Please enter a valid email.")
            return rnder_template("register.html")

        try:
            # Use parameterized query to prevent SQL injection
            query = "INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)"
            mycursor.execute(query, (name, email, password))

            mydb.commit()
            flash("Registration successful. You can now log in.", 'success')
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError as e:
            # Handle IntegrityError (duplicate entry)
            flash("Email already exists. Please use a different email.", 'error')
            print(f"IntegrityError: {e}")
            return render_template("register.html")

        finally:
            mydb.close()

    return render_template("register.html")

@app.route('/reset', methods=['POST', 'GET'])
def reset_password():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Replace with your database password
        port=3308,      # Replace with your MySQL server port
        database="learning"
    )
    mycursor = mydb.cursor()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Update the user's password in the database
        update_query = "UPDATE admin SET password = %s WHERE email = %s"
        mycursor.execute(update_query, (password, email))
        mydb.commit()
        mydb.close()
        return redirect(url_for('login'))
    return render_template("register.html")
    

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port=3308,
        database="learning"
    )
    mycursor = mydb.cursor()

    if request.method == 'POST':
        password = request.form.get('password')
        username = request.form.get('name')
        email = request.form.get('email')

        query = "SELECT * FROM admin WHERE email = %s AND password = %s"
        mycursor.execute(query, (email, password))

        r = mycursor.fetchall()
        count = mycursor.rowcount
        if count == 1:
            session['user'] = email
            if email == 'admin1@gmail.com':
                session['admin_id'] = 1
            else:
                session['admin_id'] = 0

            # Check if the user's email is in the students table
            email_exists = email_in_students_table(email)

            return render_template("home.html", user_email_in_students_table=email_exists, is_admin=is_admin())
        elif count > 1:
            return "More than 1 user"
        else:
            return render_template("login.html", is_admin=is_admin())
    elif request.method == 'GET':
        return render_template("home.html", user_email_in_students_table=False)  # Assuming user is not enrolled initially
    mydb.commit()
    mycursor.close()

def is_authenticated():
    return 'user' in session

# Authorization function to check if a user has admin privileges (user_id == 1)
def is_admin():
    result = is_authenticated() and session.get('admin_id') == 1
    print("is_admin result:", result)  # Add this debugging statement
    return result


@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove 'user' key from the session
    return redirect(url_for('login'))

def email_in_students_table(email):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        mycursor = mydb.cursor()

        query = "SELECT * FROM students WHERE email = %s"
        mycursor.execute(query, (email,))

        # Check if the user's email is in the students table
        result = mycursor.fetchone()
        email_exists = result is not None

        return email_exists
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        mycursor.close()
        mydb.close()

@app.route('/update_form')
def update_form():
    if 'user' in session:
        email = session['user']
        if email:
            return render_template('update.html', email=email)
        else:
            return "Error: Email not found in the session."
    else:
        return redirect(url_for('login'))

@app.route('/update_student', methods=['POST'])
def update_student():
    if 'user' in session:
        email = session.get('user')  # Get email from the session
        if not email:
            return "Error: Email not found in the session."

        # Get the form values
        new_fname = request.form.get('new_fname')
        new_lname = request.form.get('new_lname')
        new_age = request.form.get('new_age')
        new_password = request.form.get('new_password')

        # Call the function to update student information
        update_student_info(email, new_fname, new_lname, new_age, new_password)
        flash("Student information and password updated successfully.")

        return redirect(url_for('update_form'))
    else:
        return redirect(url_for('login'))

def update_student_info(email, new_fname, new_lname, new_age, new_password):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port=3308,
        database="learning"
    )
    mycursor = mydb.cursor()

    # Update the student information in the database
    update_query = "UPDATE students SET fname = %s, lname = %s, Age = %s  WHERE email = %s"
    mycursor.execute(update_query, (new_fname, new_lname, new_age, email))
    update_query2 = "UPDATE admin SET password = %s WHERE email = %s"
    mycursor.execute(update_query2, (new_password, email))


    mydb.commit()
    mydb.close()


@app.route('/pp')
def pp():
    if 'user' in session:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        cursor = mydb.cursor()
        query = "SELECT Course_id, name, `Desc`, Price, total_enrolled FROM pp"
        cursor.execute(query)
        # Fetch all rows
        data = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        mydb.close()
        # Render the template with the data
        return render_template('pp.html', data=data, is_admin=is_admin())        
    else:
        return render_template("login.html")

@app.route('/wb')
def wb():
    if 'user' in session:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        cursor = mydb.cursor()
        query = "SELECT Course_id, name, `Desc`, Price, total_enrolled FROM wb"
        cursor.execute(query)
        # Fetch all rows
        data = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        mydb.close()
        # Render the template with the data
        return render_template('pp.html', data=data, is_admin=is_admin())        
    else:
        return render_template("login.html")

@app.route('/AI')
def AI():
    if 'user' in session:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        cursor = mydb.cursor()
        query = "SELECT Course_id, name, `Desc`, Price, total_enrolled FROM AI"
        cursor.execute(query)
        # Fetch all rows
        data = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        mydb.close()
        # Render the template with the data
        return render_template('pp.html', data=data, is_admin=is_admin())        
    else:
        return render_template("login.html")

@app.route('/ds')
def ds():
    if 'user' in session:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        cursor = mydb.cursor()
        query = "SELECT Course_id, name, `Desc`, Price, total_enrolled FROM ds"
        cursor.execute(query)
        # Fetch all rows
        data = cursor.fetchall()
        # Close the cursor and connection
        cursor.close()
        mydb.close()
        # Render the template with the data
        return render_template('pp.html', data=data, is_admin=is_admin())        
    else:
        return render_template("login.html")

@app.route('/enroll', methods=['POST', 'GET'])
def enroll():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        port=3308,
        database="learning"
    )
    mycursor = mydb.cursor()
    courses = fetch_courses()
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            fname = request.form.get('fname')
            lname = request.form.get('lname')
            Age = request.form.get('Age')
            Course_id = request.form.get('Course_id')
            Amount = request.form.get('Amount')
            print(Course_id)
            mycursor.execute("SELECT Cus_ID FROM students WHERE email = %s", (email,))
            existing_customer = mycursor.fetchone()

                # Insert customer information into the students table
            if existing_customer:
                    # Customer already exists, use the existing Cus_ID
                cus_id = existing_customer[0]
            else:
                mycursor.execute(
                        "INSERT INTO students (email, fname, lname, Age, Courses) VALUES (%s, %s, %s, %s, %s)",
                        (email, fname, lname, Age, Course_id)
                )
                cus_id = mycursor.lastrowid  # Get the generated customer ID

            procedure_query = "CALL InsertIntoAllEnrollments(%s, %s, %s, %s, %s, %s)"
            procedure_values = (cus_id, fname, lname, Age, Course_id, Amount)
            mycursor.execute(procedure_query, procedure_values)

            increment_query = f"UPDATE {get_course_table_name(Course_id)} SET total_enrolled = total_enrolled + 1 WHERE Course_id = %s"
            mycursor.execute(increment_query, (Course_id,))

            mydb.commit()
            return "Enrolled Successfully!"
        else:
            return render_template("enroll.html",courses=courses)

    except Exception as e:
        # Log the error and return an error message
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        return "An error occurred during enrollment. Please check the logs for more information."

    finally:
            # Close the cursor and connection
        mycursor.close()
        mydb.close()

    return render_template("login.html")

def fetch_courses():
    courses = [
        {"Course_id": 0, "Course_name": "Select--", "Price": 0},
        {"Course_id": 101, "Course_name": "C++", "Price": 5999},
        {"Course_id": 102, "Course_name": "Python", "Price": 8999},
        {"Course_id": 201, "Course_name": "MERN", "Price": 6999},
        {"Course_id": 301, "Course_name": "NLP", "Price": 12999},
        {"Course_id": 401, "Course_name": "Basics of Data Science", "Price": 9999},
        # Add more courses as needed
    ]
    return courses

def get_course_table_name(course_id):
    # Convert course_id to string if it's an integer
    course_id_str = str(course_id)
    
    # Extract the first two digits to determine the course category
    category_prefix = course_id_str[:2]
    
    # Dictionary mapping course category to table names
    table_mapping = {
        '10': 'pp',
        '20': 'wb',
        '30': 'AI',
        '40': 'ds',
    }
    
    # Get the table name based on the category_prefix
    table_name = table_mapping.get(category_prefix)
    
    # If the category_prefix is not found in the dictionary, return a default table name
    return table_name if table_name else 'pp'



@app.route('/mycourses')
def mycourses():
    if 'user' in session:
        user_email = session['user']
        print(user_email)
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        mycursor = mydb.cursor()

        # Check if the user's email is in the students_data
        mycursor.execute("SELECT courses FROM students WHERE email = %s", (user_email,))
        result = mycursor.fetchone()

        if result:
            course_id = result[0]

            # Use the get_course_table_name function to get the table name
            table_name = get_course_table_name(course_id)

            # Fetch content details for the enrolled course
            mycursor.execute(f"SELECT header, img, footer, resources, quiz FROM content WHERE Course_id = %s", (course_id,))
            content_details = mycursor.fetchone()

            if content_details:
                header, img, footer, resources, quiz = content_details
                course_name = get_course_name(course_id)  # Add this line to get course name
                return render_template('mycourses.html', course_id=course_id, course_name=course_name, header=header, img=img, footer=footer, resources=resources, quiz=quiz)
        
        # If no course or user is not found, display a default message or handle as needed
        return render_template('mycourses.html', course_name='No Course Found')
    
    return redirect(url_for('login'))

def get_course_name(course_id):
    # Get the table name using the provided function
    connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
    cursor = connection.cursor()
    table_name = get_course_table_name(course_id)

    if table_name != 'default_table_name':
        # Assuming you have a connection to your MySQL database
        cursor = connection.cursor()

        # Fetch the course name from the corresponding table
        query = f"SELECT name FROM {table_name} WHERE Course_id = %s"
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()

        cursor.close()

        if result:
            return result[0]

    # Return a default course name if the table name is not found or an error occurs
    return 'Unknown Course'

def strip(text):
    # Split the string by the / character
    split_text = text.split("/")
    # Return the last element of the split string
    return split_text[-1]

def stripp(text):
  # Find the last occurrence of the \ character
  last_backslash_index = text.rfind("\\")
  # If the \ character is found, return the substring from the last occurrence of \ to the end of the string
  if last_backslash_index != -1:
    return text[last_backslash_index+1:]
  # If the \ character is not found, return the original string
  else:
    return text

@app.route('/curate', methods=['GET', 'POST'])
def curate():
    if 'user' in session and is_admin():
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3308,
            database="learning"
        )
        cursor = mydb.cursor()
        
        if request.method == 'POST':
            # Process the form data for a POST request
            cus_id = request.form.get('cus_id')
            header = request.form.get('header')
            footer = request.form.get('footer')
            img = request.files.get('image')
            resources = request.files.get('resources')
            resource = request.form.get('resources')
            quiz = request.form.get('quiz')

            if img and allowed_file(img.filename):
                filename = secure_filename(img.filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(img_path)
            else:
                img_path = None
            imagee = strip(img_path)
            image = stripp(imagee) 
            if resources and allowed_file(resources.filename):
                filename = secure_filename(resources.filename)
                resources_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resources.save(resources_path)
            else:
                resources_path = None

            # Assuming you have a connection to your MySQL database

            # Insert data into the content table
            query = "INSERT INTO content (Course_id, header, img, footer, resources, quiz) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (cus_id, header, image, footer, resource, quiz)

            cursor.execute(query, values)
            mydb.commit()

            cursor.close()
            # Close the mydb (ensure to close it in a 'finally' block for robustness)
            mydb.close()

            return "Content uploaded successfully!"

        elif request.method == 'GET':
            # Handle the GET request, for example, render a form
            return render_template("curate.html")

    return "Unauthorized Access"



@app.route('/quiz')
def quiz():
    return render_template('c++.html')

@app.route('/quizz')
def quizz():
    return render_template('py.html')

@app.route('/quiiz')
def quiiz():
    return render_template('react.html')

@app.route('/quizzz')
def quizzz():
    return render_template('NLP.html')

# def fetch_quiz_template(course_id):
#     try:
#         # Establish a database connection
#         mydb = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="",
#             port=3308,
#             database="learning"
#         )
#         mycursor = mydb.cursor()

#         # Assuming 'content' is the name of the table and 'quiz' is the column storing quiz templates
#         query = "SELECT quiz FROM content WHERE Course_id = %s"
#         mycursor.execute(query, (course_id,))
#         result = mycursor.fetchone()

#         if result:
#             # Return the path or name of the quiz template
#             return result[0]

#     except mysql.connector.Error as err:
#         print("Error: {}".format(err))
    
#     finally:
#         # Close the database connection
#         mycursor.close()
#         mydb.close()

#     # Return a default quiz template if nothing is found in the database
#     return "default_quiz_template.html"

# @app.route('/quiz')
# def quiz():
#     if 'user' in session:
#         user_email = session['user']
#         # Query the course_id based on the user's email from your students table
#         course_id = fetch_course_id(user_email)
        
#         # Fetch the quiz template based on the course_id
#         quiz_template = fetch_quiz_template(course_id)

#         # Render the quiz template
#         return render_template(quiz_template)

#     return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)