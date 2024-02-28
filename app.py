from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import pandas as pd
import os


app = Flask(__name__)

#Configuring the SQLALchmey
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///crs.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)

class Register(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    DOB = db.Column(db.String(200), nullable = False)
    mob = db.Column(db.String(200), nullable = False)
    institute = db.Column(db.String(200), nullable = False)
    gender = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(200), nullable = False)
    password = db.Column(db.String(200), nullable = False)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.name} - {self.email}"

class ContactUs(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable = False)
    email = db.Column(db.String(200), nullable = False)
    urself = db.Column(db.String(200), nullable = False)
    feedback = db.Column(db.String(200), nullable = False)
    
#used to create the database if not present...   
if not os.path.exists("crs.db"):
    with app.app_context():
        db.create_all()

    def __repr__(self) -> str:
        return f"{self.sno} - {self.name} - {self.email} - {self.feedback}"

df = pd.read_csv("D:\Computer Languages\Programming Languages\DataScience\College-Recommendation-System-main\static\collegeinfo.csv")

@app.route('/')
def Login():
    return render_template('login.html')

@app.route('/signup')
def SignUp():
    return render_template('signup.html')

@app.route('/registration', methods = ['GET', 'POST'])
def Registration():
    if request.method == 'POST':
        name = request.form['name']
        DOB = request.form['DOB']
        mob = request.form['mob']
        institute = request.form['institute']
        gender = request.form['Gender']
        email = request.form['email']
        password = request.form['pass']
        user = Register(name = name, DOB = DOB, mob = mob, institute = institute, gender = gender, email = email, password = password)
        db.session.add(user)
        db.session.commit()
    return render_template('index.html')

@app.route('/authentication', methods = ['GET', 'POST'])
def authentication():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Register.query.filter_by(email=email).first()
        if user.password == password:
            # Authentication successful
            return render_template('index.html')
        else:
            return """
                <script>alert("The Login Crediential are Incorrect!!"); 
                window.location.href = '/';</script>
                """


@app.route('/home')
def home():
    return render_template('index.html') 

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contactus', methods = ['GET', 'POST'])
def contactus():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        urself = request.form['urself']
        feedback = request.form['feedback']

        client = ContactUs(name = name, email = email, urself = urself, feedback = feedback)
        db.session.add(client)
        db.session.commit()
    return render_template('contactus.html')

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if request.method == 'POST':
        # Process user input from your form
        user_percentile = float(request.form['Score'])
        user_location = request.form['location']
        user_course = request.form['desiredBranch']
        user_exam = request.form['exam']
        #print(user_percentile)
        #print(user_exam)
        filtered_data = df[(df['Percentile Score'].notna()) &
                       (df['Location'].notna()) &
                       (df['Seat Type'].notna()) &
                       (df['Percentile Score'] <= user_percentile) &
                       (df['Location'] == user_location) &
                       (df['Course Name'] == user_course) &
                       (df['Exam(JEE/ MHT-CET)'] == user_exam)]

        if len(filtered_data) == 0:
            #return "No matching institutes found based on your criteria."
            return """
                <script>alert("No Institute is present in the entered location!!"); 
                window.location.href = '/home';</script>
                """
        # Define the feature names for user input
        user_input_dict = {
            'Percentile Score': [user_percentile],
            'Location': [user_location],
            'Course Name': [user_course],
            'Exam(JEE/ MHT-CET)': [user_exam],
        }

        # Create a user input DataFrame
        user_input_df = pd.DataFrame(user_input_dict)

        # Separate numeric and categorical features
        numeric_features = ['Percentile Score']
        categorical_features = ['Location', 'Course Name', 'Exam(JEE/ MHT-CET)']

        # Create pipelines for data preprocessing
        numeric_transformer = Pipeline(steps=[('scaler', StandardScaler())])
        categorical_transformer = Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore'))])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)])

        # Fit and transform the data
        user_input_encoded = preprocessor.fit_transform(user_input_df)

        # Calculate similarity
        X = preprocessor.transform(filtered_data.drop(['Institute Name'], axis=1))
        similarity_scores = cosine_similarity(user_input_encoded, X)

        # Combine scores with institute names
        filtered_data['Similarity Score'] = similarity_scores[0]

        # Sort by similarity score in descending order
        sorted_data = filtered_data.sort_values(by='Similarity Score', ascending=False)

        # Prepare a list of recommendations
        ##recommendations = sorted_data[['Institute Name', 'Similarity Score']].head(5)
        #print(recommendations)
        recommendations = sorted_data[['Institute Name', 'Similarity Score']].drop_duplicates(subset=['Institute Name']).head(5)

        return render_template('recommendations.html', recommendations=recommendations)

    return render_template('recommendations.html')  # Display the form


if __name__ == "__main__":
    app.run(debug=True)
    