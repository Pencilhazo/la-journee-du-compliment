from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os, requests, atexit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///compliments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'ma_cle_secrete'
db = SQLAlchemy(app)

# Liste des membres de l'équipe
TEAM_MEMBERS = [
    "Clément", "Fabiola", "Fanny", "Nans", "Natacha", "Wendy",
    "Angelo", "Rindra", "Claudia", "Henitsoa", "Tsiory", "Jimmy",
    "Florida", "Muriella", "Rojo", "Joan", "Nidah", "Mendrika",
    "Pris", "Hariliva", "Mihary"
]

# Modèle pour les compliments
class Compliment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100))
    recipient = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    anonymous = db.Column(db.Boolean, default=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent = db.Column(db.Boolean, default=False)
    delivery_method = db.Column(db.String(10), nullable=False, default='email')
    dest_email = db.Column(db.String(100), nullable=True)
    email_subject = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    now = datetime.now()
    # On vérifie que l'événement se passe entre le 10 et le 13 février
    if now < datetime(2025, 2, 10) or now > datetime(2025, 2, 13, 23, 59, 59):
        return "<h2>L'événement n'est pas en cours. Revenez le 10 février ou attendez le prochain événement.</h2>"

    if request.method == 'POST':
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        text = request.form.get('text')
        anonymous = request.form.get('anonymous') == 'on'
        delivery_method = request.form.get('delivery_method')
        dest_email = request.form.get('dest_email') if delivery_method == 'email' else None
        email_subject = request.form.get('email_subject') if delivery_method == 'email' else None

        if recipient not in TEAM_MEMBERS:
            flash("Destinataire invalide.", "error")
            return redirect(url_for('index'))
        if not text.strip():
            flash("Le message ne peut être vide.", "error")
            return redirect(url_for('index'))

        sender_display = "Anonyme" if anonymous or not sender.strip() else sender.strip()
        if not anonymous and sender_display == recipient:
            flash("Vous ne pouvez pas vous envoyer un compliment si vous révélez votre nom.", "error")
            return redirect(url_for('index'))

        nouveau = Compliment(
            sender=sender_display,
            recipient=recipient,
            text=text,
            anonymous=anonymous,
            delivery_method=delivery_method,
            dest_email=dest_email,
            email_subject=email_subject
        )
        db.session.add(nouveau)
        db.session.commit()
        flash("Votre compliment a été enregistré ! Il sera envoyé le 14 février à 8h.", "success")
        return redirect(url_for('index'))

    return render_template('index.html', team_members=TEAM_MEMBERS)

# Fonction pour envoyer les compliments (simulation)
def send_compliments():
    with app.app_context():
        compliments = Compliment.query.filter_by(sent=False).all()
        for c in compliments:
            if c.delivery_method == 'email':
                print("Envoi d'un email à", c.dest_email)
                print("Objet :", c.email_subject)
                print("Message :", c.text)
                print("De :", "Anonyme" if c.anonymous else c.sender)
            elif c.delivery_method == 'slack':
                slack_url = os.environ.get("SLACK_WEBHOOK_URL")
                if slack_url:
                    message = {
                        "text": f"Compliment pour {c.recipient}:\n> {c.text}\nDe : {'Anonyme' if c.anonymous else c.sender}"
                    }
                    requests.post(slack_url, json=message)
            c.sent = True
        db.session.commit()

# Planifier l'envoi des compliments pour le 14 février à 8h
scheduler = BackgroundScheduler()
send_time = datetime(2025, 2, 14, 8, 0, 0)
scheduler.add_job(func=send_compliments, trigger='date', run_date=send_time)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(debug=True)
