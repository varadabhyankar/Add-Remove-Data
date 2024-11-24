from flask import Flask, request, render_template, redirect, jsonify, session
from flask_migrate import Migrate, migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PrimaryKeyConstraint
from werkzeug.utils import secure_filename
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os, shutil, string, random, atexit
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from docarray import Document, DocumentArray
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "interface_key"
app.config['SESSION_PERMANENT'] = False
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:/Smart Webpages/Add Remove Data/instance/site.db'
bcrypt = Bcrypt(app)

load_dotenv()
embedding_model = OpenAIEmbeddings()
docs = DocumentArray(storage='memory')
storage_db = SQLAlchemy(app)
migrate = Migrate(app, storage_db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class ChatHistoryUpdated(storage_db.Model):
    session_id = storage_db.Column(storage_db.String(10), primary_key=True)
    timestamp = storage_db.Column(storage_db.DateTime, unique=False, nullable=False, default=datetime.now())
    faculty_name = storage_db.Column(storage_db.String(), primary_key=True)
    chats = storage_db.Column(storage_db.String(), unique=False, nullable=False)
    __table_args = (PrimaryKeyConstraint('session_id', 'faculty_name'))
    def __repr__(self):
        return f"ID : {self.session_id}, Time: {self.timestamp}"
    
class User(storage_db.Model, UserMixin):
    id = storage_db.Column(storage_db.Integer, primary_key=True)
    username = storage_db.Column(storage_db.String(20), nullable=False, unique=True)
    password = storage_db.Column(storage_db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError('The username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

def save_chat_entry(session_id, chats, faculty_name):
    entry = search_chat_entry(session_id, faculty_name)
    if(entry==None):
        new_entry = ChatHistoryUpdated(
            session_id=session_id,
            timestamp=datetime.now(),
            faculty_name=faculty_name,
            chats=chats
        )
        storage_db.session.add(new_entry)
        storage_db.session.commit()
        delete_old_entries()
    else:
        entry.timestamp = datetime.now()
        entry.chats = entry.chats + chats
        storage_db.session.commit()
        delete_old_entries()

def search_chat_entry(session_id, faculty_name):
    entry = ChatHistoryUpdated.query.filter_by(session_id=session_id, faculty_name=faculty_name).first()
    return entry

def delete_old_entries():
    time_threshold = datetime.now() - timedelta(minutes=30)
    ChatHistoryUpdated.query.filter(ChatHistoryUpdated.timestamp < time_threshold).delete()
    storage_db.session.commit()

def get_embedding(text):
    response = embedding_model.embed_query(text)
    np_response = np.array(response)
    return np_response

def generate_random_name(length=8):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def update_db(category, path):
    if(category!="general_research.csv"):
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': category}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)
        file = os.path.join(path, category)
        data = pd.read_csv(file, encoding='ISO-8859-1')
        for i, row in data.iterrows():
            embedding = get_embedding(row['Text'])
            doc = Document(
                content=row['Text'],
                embedding=embedding,
                tags={'category': category, 'faculty': current_user.username}  # Storing non-vector fields as tags
            )
            docs.append(doc)
    else:
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': "General"}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': "Research"}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)
        file = os.path.join(path, category)
        data = pd.read_csv(file, encoding='ISO-8859-1')
        for i, row in data.iterrows():
            embedding = get_embedding(row['Text'])
            doc = Document(
                content=row['Text'],
                embedding=embedding,
                tags={'category': row['Category'], 'faculty': current_user.username}  # Storing non-vector fields as tags
            )
            docs.append(doc)

def save_to_db(category, path):
    if(category!="general_research.csv"):
        file = os.path.join(path, category)
        data = pd.read_csv(file, encoding='ISO-8859-1')
        for i, row in data.iterrows():
            embedding = get_embedding(row['Text'])
            doc = Document(
                content=row['Text'],
                embedding=embedding,
                tags={'category': category, 'faculty': current_user.username}  # Storing non-vector fields as tags
            )
            docs.append(doc)
    else:
        file = os.path.join(path, category)
        data = pd.read_csv(file, encoding='ISO-8859-1')
        for i, row in data.iterrows():
            embedding = get_embedding(row['Text'])
            doc = Document(
                content=row['Text'],
                embedding=embedding,
                tags={'category': row['Category'], 'faculty': current_user.username}  # Storing non-vector fields as tags
            )
            docs.append(doc)

def delete_from_db(category):
    if(category!="general_research"):
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': category}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)
    else:
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': "General"}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)
        docs_to_delete = docs.find(filter={'tags__category': {'$eq': "Research"}, 'tags__faculty': {'$eq': current_user.username}})
        for doc in docs_to_delete:
            docs.remove(doc)

def get_chat_response(category, user_query, option, faculty_name):
    try:
        query_embedding = get_embedding(user_query)
        results_filtered = docs.find({'tags__category': {'$eq': category}, 'tags__faculty': {'$eq': faculty_name}})
        if(len(results_filtered)==0):
            return "Database does not have any record related to the selected category."
        results = results_filtered.find(query_embedding, limit=3)
        result_text = ""
        for result in results:
            result_text= result_text+"\n"+result.content
        llm_model = "gpt-3.5-turbo"
        if(option=="course_query"):
            prompt = f"Given that a user is asking questions about the {category} course at a university and the below context, answer the query: {user_query} If the answer is not clear in the context reply with 'Not sure. Contact the professor'. Answer in maximum 4 to 5 lines. Context: {result_text}"
        else:
            prompt = f"Given the below context, answer the query: {user_query} If the query has multiple questions answer each one individually. Give any relevant links from the context as text. If the answer to a specific question is not clear in the context ask the user to contact the professor regarding that. Context: {result_text}"
        llm = ChatOpenAI(temperature = 0.0, model = llm_model)
        response = llm.call_as_llm(prompt)
        return response
    except Exception as e:
        return str(e)


@app.route('/')
def home():
    return redirect('/run_query')


@app.route('/upload_data')
@login_required
def index():
    return render_template('index.html', flask_msg="")


@app.route('/submit_form', methods=['GET', 'POST'])
@login_required
def submit_form():
    try:
        try:
            option = request.form['options']
        except:
            option = ""
        try:
            text_field = request.form['textField']
        except:
            text_field = ""
        try:
            delete_option = request.form['newSelect']
        except:
            delete_option = ""

        if(option=="upload_research"):
            input_file = request.files['inputFile']
            if(input_file.filename==""):
                raise Exception("Please upload a file")
            if(text_field==""):
                raise Exception("File name is empty")
            upload_dir = 'D:/Smart Webpages/Add Remove Data/media/research/' + current_user.username
            filename = f"{text_field}.csv"
            filename = secure_filename(filename)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            if(os.path.exists(os.path.join(upload_dir, filename))):
                input_file.save(os.path.join(upload_dir, filename))
                update_db(category = filename, path = upload_dir)
            else:
                input_file.save(os.path.join(upload_dir, filename))
                save_to_db(category = filename, path = upload_dir)

        elif(option=="upload_course"):
            input_file = request.files['inputFile']
            if(input_file.filename==""):
                raise Exception("Please upload a file")
            if(text_field==""):
                raise Exception("File name is empty")
            upload_dir = 'D:/Smart Webpages/Add Remove Data/media/course/' + current_user.username
            filename = f"{text_field}.csv"
            filename = secure_filename(filename)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            if(os.path.exists(os.path.join(upload_dir, filename))):
                input_file.save(os.path.join(upload_dir, filename))
                update_db(category = filename, path = upload_dir)
            else:
                input_file.save(os.path.join(upload_dir, filename))
                save_to_db(category = filename, path = upload_dir)

        elif(option=="upload_general"):
            input_file = request.files['inputFile']
            if(input_file.filename==""):
                raise Exception("Please upload a file")
            upload_dir = 'D:/Smart Webpages/Add Remove Data/media/general/' + current_user.username
            filename = "general_research.csv"
            filename = secure_filename(filename)
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            if(os.path.exists(os.path.join(upload_dir, filename))):
                input_file.save(os.path.join(upload_dir, filename))
                update_db(category = "general_research.csv", path = upload_dir)
            else:
                input_file.save(os.path.join(upload_dir, filename))
                save_to_db(category = "general_research.csv", path = upload_dir)

        elif(option=="delete_research"):
            delete_dir = 'D:/Smart Webpages/Add Remove Data/media/research/' + current_user.username
            file_path = os.path.join(delete_dir,delete_option)
            os.remove(file_path)
            delete_from_db(delete_option)

        elif(option=="delete_course"):
            delete_dir = 'D:/Smart Webpages/Add Remove Data/media/course/' + current_user.username
            file_path = os.path.join(delete_dir,delete_option)
            os.remove(file_path)
            delete_from_db(delete_option)
        else:
            return render_template('uploadMsg.html', flask_msg="Unexpected action type")
        return render_template('uploadMsg.html', flask_msg="Action completed successfully")
    
    except Exception as e:
        return render_template('uploadMsg.html', flask_msg="Error: "+str(e))


@app.route('/get_file_names', methods=['GET'])
def get_file_names():
    try:
        dir = request.args.get('param')
        if(dir!=""):
            mypath = 'D:/Smart Webpages/Add Remove Data/media/' + dir + '/' + current_user.username
        else:
            mypath = 'D:/Smart Webpages/Add Remove Data/media/' + current_user.username
        file_name_list = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
        return jsonify(file_name_list)
    except:
        return jsonify({"Error": "Invalid file"})
    

@app.route('/get_query_file_names', methods=['GET'])
def get_query_file_names():
    try:
        dir = request.args.get('param')
        faculty = request.args.get('faculty')
        if(dir!=""):
            mypath = 'D:/Smart Webpages/Add Remove Data/media/' + dir + '/' + faculty
        else:
            mypath = 'D:/Smart Webpages/Add Remove Data/media/' + faculty
        file_name_list = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
        return jsonify(file_name_list)
    except:
        return "Error fetching data"


@app.route('/run_query/<faculty_name>')  
def run_query(faculty_name):
    if(session.get("session_id")==None):
        session["session_id"] = generate_random_name(10)
    return render_template('query.html', output="")


@app.route('/get_llm_response/<faculty_name>', methods=['POST'])
def get_llm_response(faculty_name):
    try:
        try:
            option = request.form['options']
        except:
            option = ""
        try:
            text_field = request.form['textField']
        except:
            text_field = ""
        try:
            new_option = request.form['newSelect']
        except:
            new_option = ""
        if(text_field==""):
                raise Exception("User query is empty")
        text_to_return = ""

        if(option=="course_query" or option=="research_paper"):
            if(new_option==""):
                raise Exception("Select an option")
            category = new_option
        elif(option=="general_query"):
            category = "General"
        elif(option=="research_query"):
            category = "Research"
        else:
            text_to_return = "Error: Unexpected action type"
            return jsonify(text_to_return)
        
        text_to_return = get_chat_response(category, text_field, option, faculty_name)

        session_id = session.get("session_id")
        text_to_save = text_field + "|next-entry|" + text_to_return + "|next-entry|"
        save_chat_entry(session_id,text_to_save,faculty_name)

        return jsonify(text_to_return)

    except Exception as e:
        text_to_return = "Error getting response"
        return jsonify(text_to_return)


@app.route('/get_chat_history/<faculty_name>', methods=['GET'])
def get_chat_history(faculty_name):
    try:
        session_id = session.get("session_id")
        entry = search_chat_entry(session_id, faculty_name)
        if(entry==None):
            chat_list = []
        else:
            history_string = search_chat_entry(session_id, faculty_name).chats
            chat_list = history_string.split("|next-entry|")
        return jsonify(chat_list)
    except Exception as e:
        chat_list = ["Error fetching chat history"]
        return jsonify(chat_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error_msg = ""
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect('/upload_data')
        else:
            error_msg = "Invalid username or password. Please try again."
    return render_template('login.html', form=form, error_msg=error_msg)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        storage_db.session.add(new_user)
        storage_db.session.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


@atexit.register
def cleanup():
    with app.app_context():
        try:
            storage_db.session.query(ChatHistoryUpdated).delete()
            storage_db.session.commit()
        except:
            storage_db.session.rollback()
            print("Error cleaning chat history db")
    media_path = 'D:/Smart Webpages/Add Remove Data/media'
    for filename in os.listdir(media_path):
        file_path = os.path.join(media_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s during cleanup. Reason: %s' % (file_path, e))


if __name__ == '__main__':
    app.run(debug=True)