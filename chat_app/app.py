from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime
import random
import time
import threading
import re

app = Flask(__name__)
app.config["SECRET_KEY"] = "pychat_bot_2024"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Bot Brain ──────────────────────────────────────────────────────────────────

BOT_NAME = "PyBot 🤖"

# Conversation memory per session
sessions = {}  # sid -> { "name": str, "history": [...], "mood": str }

GREETINGS = ["hello", "hi", "hey", "hii", "helo", "howdy", "sup", "yo"]
FAREWELLS  = ["bye", "goodbye", "see you", "cya", "later", "quit", "exit"]

PYTHON_TOPICS = {
    "list": "Lists in Python are ordered, mutable collections. Example:\n`fruits = ['apple', 'banana', 'mango']`\nYou can append, remove, slice them!",
    "dict": "Dictionaries store key-value pairs:\n`person = {'name': 'Alice', 'age': 25}`\nAccess with `person['name']` → Alice",
    "loop": "Python loops:\n`for i in range(5):` loops 5 times.\n`while condition:` loops until condition is False.",
    "function": "Define a function with `def`:\n```\ndef greet(name):\n    return f'Hello, {name}!'\n```",
    "class": "Python OOP with classes:\n```\nclass Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        return 'Woof!'\n```",
    "flask": "Flask is a lightweight Python web framework.\nInstall: `pip install flask`\nBasic app:\n```\nfrom flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef home():\n    return 'Hello World!'\n```",
    "exception": "Handle errors with try/except:\n```\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print('Cannot divide by zero!')\n```",
    "lambda": "Lambda = anonymous one-liner function:\n`square = lambda x: x * x`\n`square(5)` → 25",
    "comprehension": "List comprehensions are powerful:\n`evens = [x for x in range(10) if x % 2 == 0]`\n→ [0, 2, 4, 6, 8]",
    "decorator": "Decorators modify functions:\n```\ndef logger(func):\n    def wrapper(*args):\n        print('Calling', func.__name__)\n        return func(*args)\n    return wrapper\n```",
    "api": "To call an API in Python:\n```\nimport requests\nres = requests.get('https://api.example.com/data')\nprint(res.json())\n```",
    "file": "File I/O in Python:\n```\nwith open('file.txt', 'r') as f:\n    content = f.read()\n```\nUse `'w'` to write, `'a'` to append.",
    "pip": "`pip` is Python's package manager.\nInstall packages: `pip install package_name`\nList installed: `pip list`",
    "virtualenv": "Virtual environments isolate project dependencies:\n```\npython -m venv venv\nvenv\\Scripts\\activate  # Windows\nsource venv/bin/activate  # Mac/Linux\n```",
    "socket": "Python sockets enable network communication:\n```\nimport socket\ns = socket.socket()\ns.connect(('localhost', 8080))\ns.send(b'Hello')\n```",
}

JOKES = [
    "Why do Python programmers prefer dark mode? Because light attracts bugs! 🐛",
    "Why was the Python developer sad? Because he had no class. 😢",
    "A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'",
    "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25!",
    "How many programmers does it take to change a light bulb? None — it's a hardware problem.",
    "I told my wife she should embrace her mistakes. She gave me a hug. 😄",
    "Why did the programmer quit? Because they didn't get arrays. 😅",
]

MOTIVATIONS = [
    "You're doing great! Every expert was once a beginner. Keep coding! 💪",
    "The best way to learn programming is to write programs. You're on the right track! 🚀",
    "Bugs are just undiscovered features. Stay positive! ✨",
    "Rome wasn't built in a day, and neither is a great codebase. Keep going! 🏆",
    "Every line of code you write is a step forward. You've got this! 🎯",
]

FACTS = [
    "Python was created by Guido van Rossum and released in 1991. 🐍",
    "Python is named after Monty Python, not the snake! 🎭",
    "Python is the #1 most popular programming language as of 2024. 📊",
    "Instagram, YouTube, and Spotify are all built with Python. 💡",
    "Python's design philosophy emphasizes code readability (PEP 8). 📖",
    "Python has over 300,000 packages on PyPI (Python Package Index). 📦",
    "The Python logo features two snakes intertwined. 🐍🐍",
]


def get_bot_reply(sid, user_msg):
    """Generate a contextual bot reply."""
    if sid not in sessions:
        return "Hi there! I'm PyBot. What's your name?"

    session = sessions[sid]
    name = session.get("name", "there")
    msg = user_msg.lower().strip()

    # ── Name capture ──
    if not session.get("name_set"):
        # Extract name from "I am X" / "my name is X" / just a plain name
        patterns = [r"i(?:'m| am) (\w+)", r"my name is (\w+)", r"call me (\w+)"]
        for p in patterns:
            m = re.search(p, msg)
            if m:
                name = m.group(1).capitalize()
                break
        else:
            # If short word with no spaces, treat as name
            if len(msg.split()) <= 2 and not any(g in msg for g in GREETINGS):
                name = user_msg.strip().split()[0].capitalize()

        session["name"] = name
        session["name_set"] = True
        return f"Nice to meet you, {name}! 👋 I'm PyBot, your Python learning assistant.\n\nYou can ask me about Python topics (lists, functions, Flask, etc.), tell me to crack a joke, share a fun fact, or just chat. What's on your mind?"

    # ── Greetings ──
    if any(g == msg or msg.startswith(g + " ") for g in GREETINGS):
        return random.choice([
            f"Hey {name}! 👋 How can I help you today?",
            f"Hello {name}! Ready to talk Python? 🐍",
            f"Hi {name}! What would you like to learn or discuss?",
        ])

    # ── Farewells ──
    if any(f in msg for f in FAREWELLS):
        return f"Goodbye {name}! 👋 Keep coding and stay curious. See you next time! 🚀"

    # ── How are you ──
    if re.search(r"how are you|how r u|how do you do|you ok|u ok", msg):
        return random.choice([
            f"I'm doing great, {name}! Running on 100% Python power. ⚡ How about you?",
            f"Always good when there's code to talk about! 😄 What's up, {name}?",
            f"Fantastic! Ready to help. What are you working on, {name}?",
        ])

    # ── What are you / who are you ──
    if re.search(r"who are you|what are you|tell me about yourself|introduce yourself", msg):
        return (f"I'm **PyBot** 🤖 — your AI Python assistant built with Flask + Socket.IO!\n\n"
                f"I can help you with:\n"
                f"• Python concepts & code examples\n"
                f"• Jokes 😄\n"
                f"• Fun Python facts 💡\n"
                f"• Motivation 💪\n"
                f"• General conversation\n\n"
                f"Just ask me anything, {name}!")

    # ── Joke ──
    if re.search(r"joke|funny|laugh|humor|lol|make me laugh", msg):
        return "😄 Here's one:\n\n" + random.choice(JOKES)

    # ── Fact ──
    if re.search(r"fact|did you know|tell me something|interesting|trivia", msg):
        return "💡 Fun fact:\n\n" + random.choice(FACTS)

    # ── Motivation ──
    if re.search(r"motivat|inspire|encourag|sad|stuck|frustrated|help me|i can't|cant do", msg):
        return random.choice(MOTIVATIONS)

    # ── Thanks ──
    if re.search(r"thank|thanks|thx|ty|appreciate", msg):
        return random.choice([
            f"You're welcome, {name}! 😊 Anything else?",
            f"Happy to help! Keep learning, {name}! 🎯",
            f"Anytime! That's what I'm here for. 💪",
        ])

    # ── Python topic match ──
    for keyword, explanation in PYTHON_TOPICS.items():
        if keyword in msg:
            return f"📘 **{keyword.capitalize()}** in Python:\n\n{explanation}"

    # ── What is Python / what can Python do ──
    if re.search(r"what is python|about python|python language|learn python|start python", msg):
        return ("Python is a high-level, beginner-friendly programming language known for its clean syntax. 🐍\n\n"
                "You can use Python for:\n"
                "• Web development (Flask, Django)\n"
                "• Data science & ML (NumPy, Pandas, TensorFlow)\n"
                "• Automation & scripting\n"
                "• APIs & backend systems\n"
                "• Game development\n\n"
                f"Want me to explain any specific Python concept, {name}?")

    # ── Help ──
    if re.search(r"^help$|what can you|what do you know|commands|options", msg):
        return (f"Here's what you can ask me, {name}:\n\n"
                "🐍 Python topics: `list`, `dict`, `function`, `class`, `loop`, `flask`, `decorator`, `lambda`, `api`, `file`, `pip`...\n"
                "😄 `tell me a joke`\n"
                "💡 `share a fact`\n"
                "💪 `motivate me`\n"
                "🤖 `who are you`\n"
                "👋 `bye` to exit\n\n"
                "Or just chat naturally!")

    # ── What's your name ──
    if re.search(r"your name|who r u|what should i call you", msg):
        return f"I'm PyBot 🤖 — your Python buddy! And you're {name}. 😊"

    # ── Math / calculation ──
    math_match = re.search(r"(\d+)\s*([\+\-\*\/\%])\s*(\d+)", msg)
    if math_match:
        try:
            a, op, b = math_match.group(1), math_match.group(2), math_match.group(3)
            result = eval(f"{a}{op}{b}")
            return f"🧮 {a} {op} {b} = **{result}**"
        except:
            pass

    # ── Time ──
    if re.search(r"what time|current time|time now", msg):
        return f"🕐 Current server time: **{datetime.now().strftime('%I:%M %p')}**"

    # ── Default fallback with context ──
    fallbacks = [
        f"Interesting thought, {name}! Could you be more specific? I'm best at Python topics. 🐍",
        f"I'm not sure I follow, {name}. Try asking about a Python concept or type `help`.",
        f"Hmm, that's a tricky one! Ask me about Python — functions, loops, Flask, etc. 🤔",
        f"I'm still learning too, {name}! Try: 'explain Python lists' or 'tell me a joke'. 😄",
    ]
    return random.choice(fallbacks)


def bot_reply_async(sid, user_msg):
    """Send typing indicator, delay, then reply."""
    socketio.emit("bot_typing", {"typing": True}, to=sid)
    # Simulate thinking time based on msg length
    delay = min(0.8 + len(user_msg) * 0.01, 2.5)
    time.sleep(delay)
    reply = get_bot_reply(sid, user_msg)
    socketio.emit("bot_typing", {"typing": False}, to=sid)
    socketio.emit("bot_message", {
        "msg": reply,
        "time": datetime.now().strftime("%I:%M %p")
    }, to=sid)


# ── Routes & Socket Events ────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def on_connect():
    from flask import request
    sid = request.sid
    sessions[sid] = {"name": None, "name_set": False, "history": []}
    # Greet after short delay
    def greet():
        time.sleep(0.5)
        socketio.emit("bot_message", {
            "msg": "👋 Hello! I'm **PyBot**, your Python learning assistant.\n\nWhat's your name?",
            "time": datetime.now().strftime("%I:%M %p")
        }, to=sid)
    threading.Thread(target=greet, daemon=True).start()


@socketio.on("user_message")
def on_user_message(data):
    from flask import request
    sid = request.sid
    msg = data.get("msg", "").strip()
    if not msg:
        return
    # Reply in background thread so UI stays responsive
    threading.Thread(target=bot_reply_async, args=(sid, msg), daemon=True).start()


@socketio.on("disconnect")
def on_disconnect():
    from flask import request
    sessions.pop(request.sid, None)


if __name__ == "__main__":
    print("🚀 PyBot Chat running at http://127.0.0.1:5000")
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
