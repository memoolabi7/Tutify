from flask import Blueprint, render_template, request, jsonify, session, redirect
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
import plotly.graph_objs as go
import plotly
import json

geometry_blueprint = Blueprint('geometry', __name__, template_folder='templates', static_folder='static')
geometry_blueprint.secret_key = "geometry"

def train_model():
    # تعريف البيانات
    shapes = ['rectangle', 'square', 'triangle', 'parallelogram', 'complex-shape']
    shape_encoder = LabelEncoder()
    shape_encoder.fit(shapes)

    easy = [
        {
            "parameters": [
                np.random.randint(1, 10),
                np.random.randint(1, 10),
                shape_encoder.transform([np.random.choice(['rectangle', 'square'])])[0],
            ],
            "difficulty": "easy",
        }
        for _ in range(100)
    ]

    medium = [
        {
            "parameters": [
                np.random.randint(1, 20),
                np.random.randint(1, 20),
                shape_encoder.transform([np.random.choice(['triangle', 'parallelogram'])])[0],
            ],
            "difficulty": "medium",
        }
        for _ in range(100)
    ]

    hard = [
        {
            "parameters": [
                np.random.randint(1, 20),
                np.random.randint(1, 20),
                shape_encoder.transform([np.random.choice(['triangle', 'complex-shape'])])[0],
            ],
            "difficulty": "hard",
        }
        for _ in range(100)
    ]

    # دمج البيانات
    data = easy + medium + hard
    parameters = [item["parameters"] for item in data]
    difficulties = [item["difficulty"] for item in data]

    # ترميز مستوى الصعوبة
    difficulty_encoder = LabelEncoder()
    encoded_difficulties = difficulty_encoder.fit_transform(difficulties)

    # تدريب النموذج
    model = KNeighborsClassifier(n_neighbors=1)
    model.fit(parameters, encoded_difficulties)

    return model, difficulty_encoder, shape_encoder

model, difficulty_encoder, shape_encoder = train_model()

def generate_geometry_question(difficulty):
    # قائمة الأشكال المتاحة
    shape_types = {
        "rectangle": "rectangle",
        "square": "square",
        "triangle": "triangle",
        "parallelogram": "parallelogram"
    }

    # توليد الأبعاد العشوائية
    a = int(np.random.randint(1, 20))  # تحويل إلى int
    b = int(np.random.randint(1, 20))  # تحويل إلى int
    shape = np.random.choice(list(shape_types.keys()))

    # ترميز الشكل باستخدام shape_encoder
    shape_encoded = int(shape_encoder.transform([shape])[0])  # تحويل إلى int

    # العمليات المتاحة بناءً على مستوى الصعوبة
    operations_by_difficulty = {
        "easy": ["area", "perimeter"],
        "medium": ["area", "perimeter", "side"],
        "hard": ["area", "perimeter", "side"]
    }

    # اختيار العملية بناءً على مستوى الصعوبة
    allowed_operations = operations_by_difficulty[difficulty]
    operation = np.random.choice(allowed_operations)

    # إعداد بيانات السؤال والإجابة
    question_data = {}
    if shape == "rectangle":
        question = f"The figure is a rectangle with AB={a} and AC={b}. Calculate its {operation}."
        answer = a * b if operation == "area" else 2 * (a + b)
    elif shape == "square":
        question = f"The figure is a square with side AB={a}. Calculate its {operation}."
        answer = a * a if operation == "area" else 4 * a
    elif shape == "triangle":
        c = (a ** 2 + b ** 2) ** 0.5
        question = f"The figure is a right triangle with AB={a} and AC={b}. Calculate {operation}."
        if operation == "area":
            answer = 0.5 * a * b
        elif operation == "perimeter":
            answer = a + b + c
        elif operation == "side":
            answer = c
    elif shape == "parallelogram":
        question = f"The figure is a parallelogram with base AB={a} and height AC={b}. Calculate its {operation}."
        answer = a * b if operation == "area" else 2 * (a + b)

    # تخزين السؤال والإجابة والعملية
    question_data["question"] = question
    question_data["answer"] = round(float(answer), 2)  # تحويل الإجابة إلى float
    question_data["operation"] = operation
    question_data["parameters"] = [a, b, shape_encoded]  # إضافة الشكل المرمز للـ parameters

    return question_data

@geometry_blueprint.route("/")
def index():
    return render_template("geometry-index.html", title="Geometry Quiz", geometry_css="geometry")

@geometry_blueprint.route("/set-difficulty", methods=["POST"])
def set_difficulty():
    data = request.json
    difficulty = data.get("difficulty")
    num_questions = int(data.get("num_questions", 10))

    session["difficulty"] = difficulty
    session["num_questions"] = num_questions

    questions = [generate_geometry_question(difficulty) for _ in range(num_questions)]
    session["questions"] = questions
    session["answers"] = []
    return jsonify({"message": "Difficulty and question count set."})

@geometry_blueprint.route("/questions")
def questions_page():
    questions = session.get("questions", [])
    return render_template("geometry-questions.html", questions=questions, enumerate=enumerate, title="Questions", geometry_css="geometry")

@geometry_blueprint.route("/submit-answers", methods=["POST"])
def submit_answers():
    data = request.json
    user_answers = data.get("answers", [])
    questions = session.get("questions", [])
    answers = []

    for i, question in enumerate(questions):
        correct_answer = question["answer"]
        user_answer = float(user_answers[i])
        result = "Correct" if abs(user_answer - correct_answer) < 1e-2 else "Incorrect"
        answers.append({"operation": question["operation"], "result": result})

    session["answers"] = answers
    return jsonify({"message": "Answers submitted successfully."})

@geometry_blueprint.route("/results")
def results():
    answers = session.get("answers", [])
    total_questions = len(answers)
    correct_count = sum(1 for answer in answers if answer["result"] == "Correct")

    operation_counts = {"area": 0, "perimeter": 0, "side": 0}
    operation_correct = {"area": 0, "perimeter": 0, "side": 0}

    for answer in answers:
        operation = answer["operation"]
        operation_counts[operation] += 1
        if answer["result"] == "Correct":
            operation_correct[operation] += 1

    accuracy_by_operation = {
        op: (operation_correct[op] / operation_counts[op]) * 100 if operation_counts[op] > 0 else 0
        for op in operation_counts
    }

    overall_accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    # إنشاء الرسم البياني باستخدام Plotly
    bar_chart = go.Figure(
        data=[
            go.Bar(
                x=list(accuracy_by_operation.keys()),
                y=list(accuracy_by_operation.values()),
                marker=dict(color=["blue", "orange", "green"]),
            )
        ]
    )

    bar_chart.update_layout(
        title="Accuracy by Operation",
        xaxis_title="Operation",
        yaxis_title="Accuracy (%)",
        yaxis=dict(range=[0, 100]),
    )

    # تحويل الرسم البياني إلى JSON
    graph_json = json.dumps(bar_chart, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template(
        "geometry-results.html",
        graph_json=graph_json,
        overall_accuracy=overall_accuracy,
        accuracy_by_operation=accuracy_by_operation,
        title="Results",
        geometry_css="geometry",
    )

@geometry_blueprint.route("/reset")
def reset():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    geometry_blueprint.run(debug=True)