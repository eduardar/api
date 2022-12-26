from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from datetime import datetime

# set up the Flask app and the SQLAlchemy database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///change_log.db'
app.config['JWT_SECRET_KEY'] = 'secret'
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# define the models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    creator = db.Column(db.String(80), nullable=False)
    publication_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Update(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

class ProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        load_instance = True

class UpdateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Update
        load_instance = True

# routes for managing updates
@app.route('/projects/<int:project_id>/updates', methods=['POST'])
@jwt_required()
def create_update(project_id):
    # retrieve the request data
    content = request.json['content']

    # create a new update in the database
    update = Update(project_id=project_id, content=content)
    db.session.add(update)
    db.session.commit()

    # return the new update in JSON format
    schema = UpdateSchema()
    result = schema.dump(update)
    return jsonify(result)

@app.route('/projects/<int:project_id>/updates', methods=['GET'])
@jwt_required()
def get_updates(project_id):
    # retrieve the updates from the database
    updates = Update.query.filter_by(project_id=project_id).all()

    # return the updates in JSON format
    schema = UpdateSchema(many=True)
    result = schema.dump(updates)
    return jsonify(result)

@app.route('/projects/<int:project_id>/updates/<int:update_id>', methods=['GET'])
@jwt_required()
def get_update(project_id, update_id):
    # retrieve the update from the database
    update = Update.query.get((update_id, project_id))
    if not update:
        return jsonify({'error': 'update not found'}), 404

    # return the update in JSON format
    schema = UpdateSchema()
    result = schema.dump(update)
    return jsonify(result)

@app.route('/projects/<int:project_id>/updates/<int:update_id>', methods=['PUT'])
@jwt_required()
def update_update(project_id, update_id):
    # retrieve the update from the database
    update = Update.query.get((update_id, project_id))
    if not update:
        return jsonify({'error': 'update not found'}), 404

    # retrieve the request data
    content = request.json['content']

    # update the update in the database
    update.content = content
    db.session.commit()

    # return the updated update in JSON format
    schema = UpdateSchema()
    result = schema.dump(update)
    return jsonify(result)

@app.route('/projects/<int:project_id>/updates/<int:update_id>', methods=['DELETE'])
@jwt_required()
def delete_update(project_id, update_id):
    # retrieve the update from the database
    update = Update.query.get((update_id, project_id))
    if not update:
        return jsonify({'error': 'update not found'}), 404

    # delete the update from the database
    db.session.delete(update)
    db.session.commit()

    # return a success message
    return jsonify({'message': 'update deleted successfully'})

# run the app
if __name__ == '__main__':
    app.run(debug=True)


# routes for managing projects
@app.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    # retrieve the request data
    name = request.json['name']
    creator = request.json['creator']
    publication_date = request.json['publication_date']

    # create a new project in the database
    project = Project(name=name, creator=creator, publication_date=publication_date)
    db.session.add(project)
    db.session.commit()

    # return the new project in JSON format
    schema = ProjectSchema()
    result = schema.dump(project)
    return jsonify(result)

@app.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    # retrieve the request parameters
    name = request.args.get('name')
    creator = request.args.get('creator')
    publication_date = request.args.get('publication_date')
    page = request.args.get('page')
    per_page = request.args.get('per_page')

    # apply filters to the query
    query = Project.query
    if name:
        query = query.filter_by(name=name)
    if creator:
        query = query.filter_by(creator=creator)
    if publication_date:
        query = query.filter_by(publication_date=publication_date)

    # apply pagination to the query
    if page and per_page:
        page = int(page)
        per_page = int(per_page)
        projects = query.paginate(page, per_page, error_out=False)
    else:
        projects = query.all()

    # return the projects in JSON format
    schema = ProjectSchema(many=True)
    result = schema.dump(projects)
    return jsonify(result)

@app.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    # retrieve the project from the database
    project = Project.query.get(project_id)

    # return the project in JSON format
    schema = ProjectSchema()
    result = schema.dump(project)
    return jsonify(result)

@app.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    # retrieve the project from the database
    project = Project.query.get(project_id)

    # update the project with the request data
    project.name = request.json['name']
    project.creator = request.json['creator']
    project.publication_date = request.json['publication_date']
    db.session.commit()

    # return the updated project in JSON format
    return jsonify(project.serialize())

# route for deleting a project
@app.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    # retrieve the project from the database
    project = Project.query.get(project_id)

    # delete the project and commit the changes to the database
    db.session.delete(project)
    db.session.commit()

    # return a success message
    return jsonify({'message': 'Project deleted successfully'})

# run the app
if __name__ == '__main__':
    app.run(debug=True)
