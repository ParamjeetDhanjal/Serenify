from datetime import datetime,timedelta
from fileinput import filename
from datetime import date
import os
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import cast, Date
import json
import re # For text preprocessing
import random # For choosing random responses
from fuzzywuzzy import process, fuzz # Fuzzy text matching

# --- Flask App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'paramjeet'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Database Models ---
class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    emoji = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    # Relationships to easily get sender names
    sender = db.relationship('User', backref='sent_messages')

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Changed 'User.id' to 'user.id' to match standard naming
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profession = db.Column(db.String(50))
    bio = db.Column(db.Text)
    full_name = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    certificate = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    # Corrected the backref to avoid confusion
    appointments = db.relationship('Appointment', backref='professional_rel', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)

    full_name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))

    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)

    notes = db.Column(db.Text)

    status = db.Column(
        db.String(20),
        default="pending"   # IMPORTANT
    )



class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id', name='comment_parent_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    author = db.relationship('User', backref='comments', lazy=True)
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy=True
    )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    diary_entries = db.relationship('DiaryEntry', backref='author', lazy=True)
    role = db.Column(db.String(20), default='user')  # user / professional

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- Load chatbot dataset ---
try:
    with open("chatbot.json", "r", encoding="utf-8") as f:
        full_dataset = json.load(f)
except FileNotFoundError:
    print("WARNING: 'chatbot.json' not found. Chatbot responses will be limited.")
    full_dataset = []

pattern_list = [entry.get('pattern', '') for entry in full_dataset if isinstance(entry, dict)]
print(f"Loaded {len(pattern_list)} patterns for chatbot.")

# ----------------------------------------------------
# --- Chatbot Improvement: Preprocessing Function ---
# ----------------------------------------------------
def preprocess_text(text):
    """Converts to lowercase and removes punctuation for better matching."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Remove punctuation, keeping only letters, numbers, and spaces
    text = re.sub(r'[^\w\s]', '', text) 
    return text

# -------------------------------------------------
# --- Chatbot Improvement: Retrieval Logic ---
# -------------------------------------------------
def retrieve_response(user_input):
    if not pattern_list:
        return "I'm sorry, my response database is empty."

    # Preprocess the user input before comparison
    processed_input = preprocess_text(user_input)
    
    # Use token_set_ratio for better sentence/phrase matching
    best_match_tuple = process.extractOne(
        processed_input, 
        pattern_list, 
        scorer=fuzz.token_set_ratio # The key improvement!
    )
    
    # Use a stricter similarity threshold
    MIN_SIMILARITY_SCORE = 80 
    
    if best_match_tuple and best_match_tuple[1] >= MIN_SIMILARITY_SCORE:
        best_match_pattern = best_match_tuple[0]
        
        # Find the corresponding entry in the full dataset
        for entry in full_dataset:
            if entry.get('pattern') == best_match_pattern:
                response = entry.get('response')
                
                # Handle single response string or a list of responses
                if isinstance(response, list):
                    return random.choice(response)
                
                return response or "I found a relevant topic, but the full response is missing."
    
    # Fallback response
    return "I hear that you're struggling, and I'm listening. Could you rephrase or tell me more about what you're feeling?"

# --- Routes ---
@app.route('/')
def home():
    user = None
    EMOJIS = [
        "😃","😄","😁","😆","😅","😂","🤣","🥲","🥹","☺️","😊","😇","🙂","🙃","😉","😌",
        "😍","🥰","😘","😗","😙","😚","😋","😛","😝","😜","🤪","🤨","🧐","🤓","😎","🥸",
        "🤩","🥳","🙂‍↕️","😏","😒","🙂‍↔️","😞","😔","😟","😕","🙁","☹️","😣","😖","😫","😩",
        "🥺","😢","😭","😮‍💨","😤","😠","😡","🤬","🤯","😳","🥵","🥶","😱","😨","😰","😥",
        "😓","🫣","🤗","🫡","🤔","🫢","🤭","🤫","🤥","😶","😶‍🌫️","😐","😑","😬","🫨","🫠",
        "🙄","😯","😦","😧","😮","😲","🥱","😴","🫩","🤤","😪","😵","😵‍💫","🫥","🤐","🥴",
        "🤢","🤮","🤧","😷","🤒","🤕","🤑","🤠"
    ]
    diary_entries = []

    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        diary_entries = DiaryEntry.query.filter_by(author=user).order_by(DiaryEntry.created_at.desc()).limit(7).all()
        
    return render_template('home.html', user=user, diary_entries=diary_entries, EMOJIS=EMOJIS)

@app.route('/login/', methods=['GET','POST'])
def login(): 
    message = "" 
    if request.method == 'POST': 
        username = request.form.get('username') 
        password = request.form.get('password') 
        if not username and not password: 
            pass 
        else: 
            user = User.query.filter_by(username=username).first()
            if not user:
                message = "Invalid username or password"
            else:
                if user.role == 'professional':
                    professional = Professional.query.filter_by(user_id=user.id).first()
                    session["professional_id"] = professional.id
                    session["username"] = user.username
                    session['display_name']= professional.full_name
                    return redirect(url_for('professional_dashboard'))
                elif user.check_password(password):
                    session["username"] = user.username
                    return redirect(url_for('home'))
                else:
                    message = "Invalid username or password"
    return render_template('login.html', message=message)


@app.route('/signup/', methods=['GET','POST'])
def signup():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']

        if User.query.filter((User.username==username) | (User.email==email)).first():
            message = "Username or email already exists!"
            return render_template('signup.html', message=message)

        new_user = User(username=username, name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session["username"] = new_user.username
        return redirect(url_for('home'))

    return render_template('signup.html', message=message)

@app.route('/diary/', methods=['POST'])
def diary():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    content = request.form.get('diary-entries')
    emoji = request.form.get('emoji')

    new_entry = DiaryEntry(
        content=content,
        emoji=emoji,
        author=user,
        created_at=datetime.now()
    )
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for('home'))

# --- Chatbot Session-Based Route ---
@app.route('/chatbot/', methods=['GET','POST'])
def chatbot():
    # Initialize history
    if 'chat_history' not in session:
        session['chat_history'] = [{'speaker':'bot', 'text':"Hello! I'm here to listen without judgment. How can I support you today?"}]

    if request.method == 'POST':
        user_input = request.form.get('message','').strip()
        if user_input:
            bot_response = retrieve_response(user_input)
            session['chat_history'].append({'speaker':'user','text':user_input})
            session['chat_history'].append({'speaker':'bot','text':bot_response})
            session.modified = True
        return redirect(url_for('chatbot'))

    return render_template('chatbot.html', history=session['chat_history'])

# Optional: clear chat history
@app.route('/chatbot/clear/')
def clear_chat():
    session.pop('chat_history', None)
    return redirect(url_for('chatbot'))

@app.route('/past-entries/',methods=['GET','POST'])
def past_entries():
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method == "POST":
            entries = None
            date = request.form.get("search")
            search_date = datetime.strptime(date, '%Y-%m-%d').date()
            entries = DiaryEntry.query.filter(
                    DiaryEntry.user_id == User.id,
                    db.func.date(DiaryEntry.created_at) == search_date
                ).order_by(DiaryEntry.created_at.desc()).all()
        else:
            entries = DiaryEntry.query.filter_by(author=User.query.filter_by(username=session['username']).first()).order_by(DiaryEntry.created_at.desc()).all()
    return render_template('entries.html', entries=entries)

# The updated delete route from the previous response:
@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        # In case the session key exists but the user doesn't (shouldn't happen)
        return redirect(url_for('login')) 

    # CRITICAL: Filter by entry ID AND user ID for security
    entry = DiaryEntry.query.filter_by(id=entry_id, user_id=user.id).first()
    
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('past_entries'))

@app.route('/update_entry/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if request.method=="POST":
        udpated_entry = request.form.get("updated_entry")
        entry = DiaryEntry.query.filter_by(id=entry_id, user_id=user.id).first()
        if entry:
            entry.content = udpated_entry
            db.session.commit()
    return redirect(url_for('past_entries'))

@app.route('/logout/', methods=['POST'])
def logout():   
    session.pop('username', None)
    return redirect(url_for('home'))

# ---------------- COMMENT SYSTEM (DYNAMIC TOPICS) ----------------

@app.route('/distress/<topic>/')
def distress_page(topic):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    comments = Comment.query.filter_by(topic=topic) \
        .order_by(Comment.created_at.desc()) \
        .all()

    # Decide template based on topic
    template_map = {
        "study": "study.html",
        "family": "family.html",
        "chronic": "chronic.html",
        "financial": "financial.html",
        "existential":"existential.html"
    }

    template = template_map.get(topic)
    if not template:
        return "Invalid topic", 404

    return render_template(
        template,
        comments=comments,
        user=user,
        topic=topic
    )

# 26 Mental Health Questions
QUESTIONS = [
    "How often have you felt little interest or pleasure in doing things?",
    "How often have you felt down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure?",
    "Trouble concentrating on things, such as reading the news?",
    "Moving or speaking so slowly that other people could have noticed?",
    "Feeling nervous, anxious, or on edge?",
    "Not being able to stop or control worrying?",
    "Worrying too much about different things?",
    "Trouble relaxing?",
    "Being so restless that it is hard to sit still?",
    "Becoming easily annoyed or irritable?",
    "Feeling afraid, as if something awful might happen?",
    "Feeling lonely even when you are with others?",
    "Feeling detached or numb?",
    "Feeling overwhelmed by your responsibilities?",
    "Difficulty making simple daily decisions?",
    "Feeling that your future looks hopeless?",
    "Avoiding social situations you used to enjoy?",
    "Experiencing physical tension (tight chest, clenched jaw)?",
    "Waking up feeling unrefreshed?",
    "Finding it hard to find meaning in your work or hobbies?",
    "Dwelling on things from the past?",
    "Feeling like you have to put on a 'mask' for others?"
]

OPTIONS = [
    (0, "Not at all"),
    (1, "Several days"),
    (2, "More than half the days"),
    (3, "Nearly every day")
]

@app.route('/quiz/', methods=['GET', 'POST'])
def health_quiz():
    results = None
    if request.method == 'POST':
        # Collect all scores from the form
        try:
            total_score = 0
            for i in range(len(QUESTIONS)):
                # Each radio group is named 'q0', 'q1', etc.
                total_score += int(request.form.get(f'q{i}', 0))
            
            # Simple scoring logic
            if total_score < 20:
                status, color = "Low Distress", "#27ae60"
            elif total_score < 45:
                status, color = "Moderate Distress", "#f39c12"
            else:
                status, color = "High Distress", "#e74c3c"
                
            results = {"score": total_score, "status": status, "color": color}
        except ValueError:
            results = {"error": "Please answer all questions."}

    return render_template('quiz.html', questions=QUESTIONS, options=OPTIONS, results=results)
@app.route('/comment/<topic>/', methods=['POST'])
def add_comment(topic):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    comment_text = request.form.get("comment_text", "").strip()
    parent_id = request.form.get('parent_id')  
    if comment_text:
        # prevent same-user exact duplicates
        existing_comment = Comment.query.filter_by(
            topic=topic,
            user_id=user.id,
            text=comment_text
        ).first()
        if not parent_id or parent_id == "":
            parent_id = None
        if not existing_comment:
            new_comment = Comment(
                topic=topic,
                text=comment_text,
                user_id=user.id,
                parent_id=parent_id if parent_id else None,
                created_at=datetime.now()
            )
            db.session.add(new_comment)
            db.session.commit()

    return redirect(url_for('distress_page', topic=topic))


@app.route('/delete_comment/<topic>/<int:comment_id>/', methods=['POST'])
def delete_comment(topic, comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    comment = Comment.query.filter_by(
        id=comment_id,
        user_id=user.id,
        topic=topic
    ).first()

    if comment:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('distress_page', topic=topic))

@app.route('/apply_professional/', methods=['GET','POST'])
def apply_professional():   
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        profession = request.form.get('profession')
        bio = request.form.get('bio')
        full_name = request.form.get("name")
        experience = request.form.get("experience")
        certificate_file = request.files.get('certificate')
        certificate_filename = None

        if certificate_file and certificate_file.filename:
            certificate_filename = certificate_file.filename

            cert_folder = os.path.join(app.static_folder, 'certificates')
            os.makedirs(cert_folder, exist_ok=True)

            certificate_file.save(os.path.join(cert_folder, certificate_filename))
        professional = Professional(
            user_id=user.id,
            bio=bio,
            full_name= full_name,
            profession = profession,
            experience=experience,
            certificate=certificate_filename,
            verified=False
        )
        user.role = 'professional'  # Update user role
        db.session.add(professional)
        db.session.commit()

    return redirect(url_for('professional_dashboard'))
@app.route("/appointment/<int:appt_id>/accept", methods=["POST"])
def accept_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "accepted"
    db.session.commit()
    return redirect(url_for("professional_dashboard"))


@app.route("/appointment/<int:appt_id>/decline", methods=["POST"])
def decline_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "declined"
    db.session.commit()
    return redirect(url_for("professional_dashboard"))

@app.route('/profession/', methods=['GET','POST'])  
def profession():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('profession_application.html')

@app.route('/profession_logout/', methods=['GET','POST'])
def profession_logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route("/support/", methods=["GET", "POST"])
def professional_support():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()
    today = date.today()
    professionals = Professional.query.filter_by(verified=False).all()

    # 🔑 Fetch user's appointments
    appointments = Appointment.query.filter_by(user_id=user.id).all()

    # 🔑 Create lookup: { professional_id : appointment }
    appt_map = {appt.professional_id: appt for appt in appointments}

    return render_template(
        "professional_support.html",
        user=user,
        today = today,
        professionals=professionals,
        appt_map=appt_map
    )


@app.route("/appointments/")
def appointments():
    if 'username' not in session:
        return redirect(url_for('login'))

    professional = Professional.query.get(session["professional_id"])
    appointments = Appointment.query.filter_by(professional_id=professional.id).order_by(Appointment.date.desc()).all()

    return render_template(
        "appointments.html",
        professional = professional,
        appointments=appointments
    )
MAX_APPOINTMENTS_PER_DAY = 5
@app.route("/appointment/<int:professional_id>", methods=["GET", "POST"])
def appointment(professional_id):
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first_or_404()
    professional = Professional.query.get_or_404(professional_id)
    today = date.today()
    message = success = None

    if request.method == "POST":
        appointment_date = datetime.strptime(
            request.form["appointment_date"], "%Y-%m-%d"
        ).date()

        # Error 1: Past Dates
        if appointment_date < today:
            message = "You cannot book past dates."
        
        else:
            time_slot = request.form["time_slot"]

            # FIX 1: Check if slot is taken (Both Pending AND Accepted statuses)
            # This ensures that if Person A books 10 AM on the 28th, Person B cannot.
            is_taken = Appointment.query.filter(
                Appointment.professional_id == professional.id,
                db.func.date(Appointment.date) == appointment_date,
                Appointment.time_slot == time_slot,
                Appointment.status.in_(["pending", "accepted"]) 
            ).first()

            if is_taken:
                message = f"The {time_slot} slot on {appointment_date} is already reserved."
            
            else:
                # FIX 2: Check daily limit for that specific professional on that specific day
                daily_count = Appointment.query.filter(
                    Appointment.professional_id == professional.id,
                    db.func.date(Appointment.date) == appointment_date,
                    Appointment.status != "declined" # Don't count declined ones against the limit
                ).count()

                if daily_count >= MAX_APPOINTMENTS_PER_DAY:
                    message = "This professional is fully booked for this date."
                
                else:
                    # Logic is clear, create the appointment
                    appt = Appointment(
                        user_id=user.id,
                        professional_id=professional.id,
                        full_name=request.form["full_name"],
                        mobile=request.form["mobile"],
                        # Store only the date part or use combine for DateTime
                        date=appointment_date, 
                        time_slot=time_slot,
                        notes=request.form.get("notes"),
                        status="pending"
                    )
                    db.session.add(appt)
                    db.session.commit()
                    success = "Your appointment request has been sent!"

    return render_template(
        "appointment.html",
        professional=professional,
        message=message,
        success=success,
        today=today,
         user= user,
          date=date # Pass today to the template to restrict the date picker
    )

# ----------------- Update Appointment Status -----------------
@app.route("/appointment/<int:appointment_id>/update/<string:action>", methods=["POST"])
def update_appointment_status(appointment_id, action):
    if "professional_username" not in session:
        return redirect(url_for("professional_login"))

    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = "accepted" if action == "accept" else "declined"
    db.session.commit()

    return redirect(url_for("professional_dashboard"))




# ----------------- Professional Dashboard -----------------
@app.route("/professional/")
def professional_dashboard():
    if "professional_id" not in session:
        return redirect(url_for("login"))

    professional = Professional.query.get_or_404(session["professional_id"])
    today = date.today()

    # FIX: Fetch ALL appointments from today onwards (removes the "only today" restriction)
    # This includes tomorrow, next week, etc.
    upcoming_appointments = Appointment.query.filter(
        Appointment.professional_id == professional.id,
        Appointment.date >= today
    ).order_by(Appointment.date.asc(), Appointment.time_slot.asc()).all()

    # Stats for your dashboard cards
    today_count = sum(1 for a in upcoming_appointments if a.date == today)
    pending_count = sum(1 for a in upcoming_appointments if a.status == 'pending')

    return render_template(
        "professional.html",
        professional=professional,
        appointments=upcoming_appointments, # All future appts sent to the table
        today_count=today_count,
        pending_count=pending_count,
        today=today,
        total_appointments=len(upcoming_appointments)
    )

@app.route('/chat/<int:appt_id>/', methods=['GET', 'POST'])
def session_chat(appt_id):
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if not user: return redirect(url_for('login'))
    
    appt = Appointment.query.get_or_404(appt_id)

    if request.method == 'POST':
        msg_text = request.form.get('message', '').strip()
        if msg_text:
            new_msg = ChatMessage(appointment_id=appt.id, sender_id=user.id, message=msg_text)
            db.session.add(new_msg)
            db.session.commit()
        return redirect(url_for('session_chat', appt_id=appt.id))

    chat_messages = ChatMessage.query.filter_by(appointment_id=appt.id).order_by(ChatMessage.timestamp.asc()).all()

    # --- THE MAGIC PART ---
    # If the request has this header, return JUST the bubbles
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = ""
        for m in chat_messages:
            side = "sent" if m.sender_id == user.id else "received"
            html += f'<div class="msg {side}">{m.message}</div>'
        return html

    # Otherwise, return the whole page
    return render_template('session_chat.html', appt=appt, chat_messages=chat_messages, current_user=user)
# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
'''
flask --app serenify.py db init
flask --app serenify.py db migrate -m "Initial migration"
flask --app serenify.py db upgrade
'''