from flask import Flask, render_template, request, redirect,url_for, session, flash
import os
from openai import AzureOpenAI
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import bcrypt


app = Flask(__name__)

app.secret_key = 'Evh|4@%P{c/1<u%<LMMzUCg_5bk+V*'

# MongoDB connection URI
uri = "mongodb+srv://kumarmanket135:KHZTBgh89JK0oaxI@cluster0.ncrvh3r.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Connect to the 'flask_app' database and 'users' collection
db = client.flask_app
users_collection = db.users

# Replace with your OpenAI setup
# ...
# Set up OpenAI client (Azure-specific)
client = AzureOpenAI(
    api_key=os.environ['AZURE_OPENAI_KEY'],
    api_version="2023-05-15",
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
)

@app.route('/')
def index():
    return render_template('landing.html')


# Existing code remains unchanged

@app.route('/generate', methods=['POST'])
def generate():
  selected_event = request.form['selected_event']
  budget_range = int(request.form['budget_range'])
  venue = request.form['venue']
  event_date = request.form['event_date']
  time_input = request.form['time_input']
  guest_count = int(request.form['guest_count'])
  target_audience = request.form['target_audience']
  event_description = request.form['event_description']

  if selected_event and event_date and venue and guest_count and budget_range and target_audience and event_description:
    response = generate_response_for_event(selected_event, budget_range, guest_count)
    email_draft = generate_email_draft(selected_event, event_date, time_input, venue, guest_count, target_audience, event_description)
    return render_template('result.html', response=response, email_draft=email_draft)
  else:
    return render_template('index.html', error="Please fill in all event details.")



def generate_response_for_event(event_name, budget, guest_count):
    message_text = [
        {"role": "system", "content": f"""Create a detailed event plan focusing on 10 essential elements and 5 inventive ideas for an event named {event_name}, designed for {guest_count} attendees. Your plan should prioritize affordability while aiming for high attendee satisfaction. Each suggestion must fit within a budget of Rs {budget} and offer unique, engaging experiences that reflect the attendees' interests and demographic profile. The plan should cover various aspects, including venue selection, entertainment options, catering services, and personalized touches that make the event memorable.

Output Format:

Introduction:

Brief overview of the event concept and goals.
Importance of cost-effectiveness and attendee satisfaction.
Key Elements:

List and describe 10 key elements essential for the event's success, focusing on venue, entertainment, food, and personalized experiences.
For each element, provide a rationale on how it contributes to a memorable experience within the budget constraints.
Creative Ideas:

Present 5 creative ideas that can enhance the event, detailing how they can be implemented cost-effectively.
Explain the expected impact of each idea on the overall event experience.
Budget Allocation:

Break down the budget, allocating specific amounts to each suggested element and idea.
Include cost-saving tips that do not compromise the quality of the experience.
Conclusion:

Summarize how the proposed plan achieves a balance between cost-effectiveness and a high satisfaction rate.
Reiterate the potential of the plan to offer a unique and memorable experience for all attendees."""}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt",  # Retaining the original model
            messages=message_text
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"  # Handle potential errors gracefully

def generate_email_draft(event_name, date, time_input, venue, guest_count, target_audience, event_description):
      message_text = [
          {"role": "system", "content": f"""Compose an engaging email invitation for an event named {event_name}, scheduled to take place at {venue} on {date} at {time_input}, catering to {guest_count} {target_audience}. The invitation should include:

A Captivating Subject Line: Craft a subject line that instantly grabs attention and hints at the event's uniqueness.

Warm Opening: Begin with a personalized greeting that resonates with the {target_audience}.

Event Description: Incorporate a compelling and detailed description of {event_description}, highlighting what makes this event not-to-be-missed. Ensure the description is tailored to appeal to the interests and preferences of the {target_audience}.

Key Details: Clearly state the event's name, venue, date, and time. If there are specific instructions for arrival or attire, include those as well.

RSVP Instructions: Provide clear instructions for RSVPing, including a deadline for responses and any preferred contact method or link for confirmation.

Call to Action: Encourage the recipient to act promptly, whether it's to RSVP, register, or take another required action. Emphasize the importance of their presence to the success of the event.

Closing: Conclude with a warm and inviting closing remark, expressing eagerness to host them at the event.

Ensure the email is structured to engage the recipient from start to finish, with a tone and language that matches the {target_audience}'s expectations and interests. The goal is to make the email not only informative but also irresistible, prompting recipients to respond positively."""}
      ]
      try:
          response = client.chat.completions.create(
              model="gpt",  # Retaining the original model
              messages=message_text
          )
          return response.choices[0].message.content
      except Exception as e:
          return f"Error: {str(e)}"

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/signup_page')
def signup_page():
  return render_template('signup.html')

@app.route('/forgot')
def forgot():
  return render_template('forgot.html')

@app.route('/login-verify', methods=['POST'])
def home():
    email = request.form['email']
    password_input = request.form['password'].encode('utf-8')  # Encode the input password to bytes

    user = users_collection.find_one({'email': email})

    if user and bcrypt.checkpw(password_input, user['password']):
        # Passwords match, allow login
        session['user_email'] = user['email']
        session['user_name'] = user['first_name']
        return render_template('index.html',user_name=session['user_name'])
    else:
        # Wrong email or password, redirect to login page with a flash message
        flash('Wrong email or password', 'error')
        return redirect('/login')
      
@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        salt = bcrypt.gensalt()

        # Hash the password using the salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        # hasher = argon2.PasswordHasher()
        # hashed_password = hasher.hash(password)
        

        # Check if the username already exists
        existing_email = users_collection.find_one({'email': email})
        if existing_email:
            return "Email already exists. Please choose another Email."

        # Create a document to insert into the 'users' collection
        user_data = {
           'first_name': first_name,
           'last_name': last_name,
           'email': email,
           'phone': phone,
           'password': hashed_password,
           
          }


        try:
            # Insert the document into the 'users' collection
            users_collection.insert_one(user_data)
            return redirect('/')
        except DuplicateKeyError:
            return "An error occurred during signup."


@app.route('/forgot_email',methods=['POST'])
def forgot_email():
  email = request.form['email']
  user_email = users_collection.find_one({'email':email})
  if not user_email:
    flash('No user with that email address exists.')
    return redirect('/forgot')
  
    
  
if __name__ == "__main__":
  app.run(host='0.0.0.0', port=81)

