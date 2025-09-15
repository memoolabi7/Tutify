from flask import Blueprint, render_template, request, jsonify, session, redirect
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
import plotly.graph_objs as go
import plotly

gebra_blueprint = Blueprint('gebra', __name__, template_folder='templates', static_folder='static')
gebra_blueprint.secret_key = "gebra"  


def train_model():
    easy = [
        {
            "parametters": [
                np.random.randint(1, 10),
                np.random.randint(1, 10),
                np.random.randint(10, 20),
                np.random.choice([1, 2]),
            ],
            "difficulty": "easy",
        }
        for _ in range(100)
    ]

    medium = [
        {
            "parametters": [
                np.random.randint(-10, 10),
                np.random.randint(1, 10),
                np.random.randint(-50, 50),
                np.random.choice([1, 2, 3]),
            ],
            "difficulty": "medium",
        }
        for _ in range(100)
    ]

    hard = [
        {
            "parametters": [
                np.random.randint(1, 10),
                np.random.randint(1, 10),
                np.random.randint(-100, 100),
                np.random.choice([2, 3, 4]),
            ],
            "difficulty": "hard",
        }
        for _ in range(100)
    ]

    data = easy + medium + hard

    parametters = [array["parametters"] for array in data]
    difficulties = [item["difficulty"] for item in data]

    encoder = LabelEncoder()
    encoded_difficulties = encoder.fit_transform(difficulties)

    model = KNeighborsClassifier(n_neighbors=1)
    model.fit(parametters, encoded_difficulties)

    return model, encoder


model, encoder = train_model()


def generate_question(difficulty):
    a = np.random.randint(-10, 10)
    b = np.random.randint(0, 10)
    c = np.random.randint(0, 50)

    operations_by_difficulty = {"easy": [1, 2], "medium": [1, 2, 3], "hard": [2, 3, 4]}

    predicted_level = encoder.transform([difficulty])[0]
    allowed_operations = operations_by_difficulty[difficulty]

    op = np.random.choice(allowed_operations)
    predicted_difficulty = model.predict([[a, b, c, op]])[0]

    if predicted_difficulty == predicted_level:
        match op:
            case 1:  
                if a == 0:
                    return generate_question(difficulty)
                question = f"{a} x + {b} = {c}"
                answer = (c - b) / a
                operation = ["subtraction", "division"]
            case 2:  
                if a == 0:
                    return generate_question(difficulty)
                question = f"{a} x - {b} = {c}"
                answer = (c + b) / a
                operation = ["addition", "division"]
            case 3:  
                if (a == 0 or b == 0):
                    return generate_question(difficulty)
                question = f"{a} x * {b} = {c}"
                answer = (c / b) / a
                operation = ["division"]
            case 4:
                if a == 0:
                    return generate_question(difficulty)
                question = f"{a} x / {b} = {c}"
                answer = (c * b) / a
                operation = ["multiplication", "division"]

        return {"question": question, "answer": round(answer, 2), "operation": operation}
    else:
        return generate_question(difficulty)

##########################################

@gebra_blueprint.route("/")
def index():
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template("gebra-index.html", title="Math Quiz", gebra_css="gebra", subject=subject)


@gebra_blueprint.route("/set-difficulty", methods=["POST"])
def set_difficulty():
    data = request.json
    difficulty = data.get("difficulty")
    num_questions = int(data.get("num_questions", 10)) 

    
    session["difficulty"] = difficulty
    session["num_questions"] = num_questions

    
    questions = [generate_question(difficulty) for _ in range(num_questions)]
    session["questions"] = questions
    session["answers"] = []
    return jsonify({"message": "Difficulty and question count set."})


@gebra_blueprint.route("/questions")
def questions_page():
    questions = session.get("questions", [])
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template("gebra-questions.html", questions=questions, enumerate=enumerate, title="Questions", gebra_css="gebra", subject=subject)


@gebra_blueprint.route("/submit-answers", methods=["POST"])
def submit_answers():
    data = request.json
    user_answers = data.get("answers", [])
    questions = session.get("questions", [])
    answers = []

    for i, question in enumerate(questions):
        correct_answer = question["answer"]
        operation = question["operation"]
        user_answer = float(user_answers[i])
        result = "Correct" if abs(user_answer - correct_answer) < 1e-2 else "Incorrect"
        answers.append({"operation": operation, "result": result})

    session["answers"] = answers
    return jsonify({"message": "Answers submitted successfully."})


import plotly.graph_objs as go
import plotly
import json

@gebra_blueprint.route("/results")
def results():
    answers = session.get("answers", [])
    operations = ["addition", "subtraction", "multiplication", "division"]
    correct_counts = {op: 0 for op in operations}
    total_counts = {op: 0 for op in operations}

    for answer in answers:
        for operation in answer["operation"]:
            total_counts[operation] += 1
            if answer["result"] == "Correct":
                correct_counts[operation] += 1

    percentages = {
        op: (correct_counts[op] / total_counts[op]) * 100 if total_counts[op] > 0 else 0
        for op in operations
    }

    tips = {}
    for op, accuracy in percentages.items():
        if accuracy == 100:
            tips[op] = f"Great job on {op}! Keep up the excellent work."
        elif accuracy >= 70:
            tips[op] = f"Good work on {op}, but there's still room for improvement. Review some practice problems."
        elif accuracy >= 40:
            tips[op] = f"Your performance on {op} is okay, but you should practice more."
        else:
            if total_counts[op] == 0:
                tips[op] = f"There was no {op}s from previous questions. So, there are no comments about it."
            else:
                tips[op] = f"You need to focus on {op}. Consider revisiting the basics and practicing more."

    
    bar_chart = go.Figure(
        data=[
            go.Bar(
                x=list(percentages.keys()),
                y=list(percentages.values()),
                marker=dict(color=["blue", "orange", "green", "red"]),
            )
        ]
    )

    bar_chart.update_layout(
        title="Accuracy by Operation",
        xaxis_title="Operations",
        yaxis_title="Accuracy (%)",
        yaxis=dict(range=[0, 100]),
    )

    
    graph_json = json.dumps(bar_chart, cls=plotly.utils.PlotlyJSONEncoder)

    
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])

    return render_template(
        "gebra-results.html",
        graph_json=graph_json,
        title="Results",
        tips=tips,
        percentages=percentages,
        gebra_css="gebra",
        subject=subject,
    )


@gebra_blueprint.route("/reset")
def reset():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    gebra_blueprint.run(debug=True)

