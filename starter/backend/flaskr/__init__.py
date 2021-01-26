import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# complete paginate_questions
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  Set up CORS. Allow '*' for origins. '''
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
  Use the after_request decorator to set Access-Control-Allow
  '''

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS'
        )
        return response

    '''
  Create an endpoint to handle GET requests 
  for all available categories.
  '''

    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            total_categories = Category.query.order_by(Category.id).all()
            categories = {category.id: category.type for category in
                          total_categories}

            if len(categories) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'categories': categories,
                'total_categories': len(Category.query.all())
            })
        except():
            abort(404)

    '''
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 
  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen 
  for three pages.
  Clicking on the page numbers should update the questions. 
  '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        try:
            question_selection = Question.query.order_by(Question.id).all()
            questions = paginate_questions(request, question_selection)

            category_selection = Category.query.order_by(Category.id).all()

            categories = {}
            for c in category_selection:
                categories[c.id] = c.type
            if len(questions) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(Question.query.all()),
                'categories': categories,
                'current_category': None
            })
        except():
            abort(404)

    '''
  Create an endpoint to DELETE question using a question ID. 
  TEST: When you click the trash icon next to a question, the question 
  will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': questions,
                'total_questions': len(Question.query.all())
            })

        except Exception as e:
            abort(422)
            print(e)

    '''
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.
  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            body = request.get_json()
            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_category = body.get('category', None)
            new_difficulty = body.get('difficulty', None)
            if new_question == "" or new_answer == "":
                abort(422)

            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
            )
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except Exception as e:
            abort(422)
            print(e)

    '''
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 
  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        try:
            body = request.get_json()
            search_term = body.get('searchTerm', None)
            selection = Question.query.order_by(Question.id).filter(
                Question.question.ilike('%' + search_term + '%')).all()
            questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(questions),
                'current_category': None
            })

        except Exception as e:
            abort(422)
            print(e)

    '''
  Create a GET endpoint to get questions based on category. 
  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''

    @app.route('/categories/<string:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            category = Category.query.filter(
                Category.id == category_id).one_or_none()

            if category is None:
                abort(404)

            selection = Question.query.order_by(Question.id).filter(
                Question.category == category_id).all()
            questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(questions),
                'current_category': category_id
            })

        except Exception as e:
            abort(404)
            print(e)

    '''
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 
  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        try:
            body = request.get_json()
            quiz_category = body.get('quiz_category', None).get('id', None)
            previous_questions = body.get('previous_questions', None)

            if quiz_category == 0:  # click all
                selection = Question.query.filter(
                    Question.question != '').order_by(Question.id).all()
            else:
                selection = Question.query.order_by(Question.id).filter(
                    Question.category == str(int(quiz_category))).all()

            questions = [question.format() for question in selection]
            available_questions = [
                question for question in questions
                if question.get('id', None) not in previous_questions
            ]

            if len(available_questions) != 0:
                question = available_questions.pop(
                    random.randrange(len(available_questions)))
                previous_questions.append(question.get('id', None))
            else:
                question = None

            return jsonify({
                'success': True,
                'question': question,
                'previous_questions': previous_questions
            })

        except Exception as e:
            abort(422)

    '''
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method NOT allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable Entity"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    return app