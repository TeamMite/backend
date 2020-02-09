from flask import Flask, jsonify,request
from flask_cors import CORS, cross_origin
from flask_pymongo import PyMongo
import statement6dbope as std6
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt_claims

)
app = Flask(__name__)
CORS(app)


app.config["MONGO_URI"] = "mongodb://localhost:27017/dhi_analytics"


mongo = PyMongo(app)
# Setup the Flask-JWT-Extended extension


app.config['JWT_SECRET_KEY'] = 'super-secret' 
jwt = JWTManager(app)


class UserObject:
    def __init__(self, username, roles):
        self.username = username
        self.roles = roles


@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {'roles': user.roles}

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.username

# Provide a method to create access tokens. The create_access_token()
# function is used to actually generate the token, and you can return
# it to the caller however you choose.
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
    username = request.json.get('username', None)
    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    user = mongo.db.dhi_user.find_one({'email': username})
    if not user:
        return jsonify({"msg": "Bad username or password"}), 401
    roles = [ x['roleName'] for x in user['roles']]
    user = UserObject(username=user["email"], roles=roles)
    # Identity can be any data that is json serializable
    access_token = create_access_token(identity=user,expires_delta=False)
    return jsonify(access_token=access_token), 200

@app.route('/message')
def message():
    return {"message":"Check you luck"}

# Protect a view with jwt_required, which requires a valid access token
# in the request to access.


@app.route('/user', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    ret = {
        'user': get_jwt_identity(),  
        'roles': get_jwt_claims()['roles'] ,
        }
    return jsonify(ret), 200


@app.route('/academicyear')
def getacademicyear():
    #return {"message":"Check you luck"}
    year=std6.get_academic_year()
    #return jsonify({"check": 1}), 200
    return jsonify({"year":year})

@app.route('/term')
def term():
    #mogodb query
    
    termType=std6.get_term()
    return jsonify({'term':termType})
@app.route('/get-usn/<email>')
def getusn(email):
    usn=std6.get_student_usn(email)
    return jsonify({"usn":usn})

@app.route('/placement/<usn>/<term>')
def getOffers(usn,term):
    offers = std6.get_student_placement_offers(usn,term)
    return jsonify({"offers":offers})

@app.route('/<usn>/score')
def getScores(usn):
    scores = std6.get_student_score(usn)
    return jsonify({"scores":scores})

@app.route('/dept')
def getallDepts():
    depts=std6.get_all_depts()
    return jsonify({"depts":depts})

@app.route('/<dept>/dept')
def getFacultiesByDept(dept):
    facs=std6.get_faculties_by_dept(dept)
    return jsonify({"facs":facs})
@app.route('/<email>/empid')
def getEmpId(email):
    empid=std6.get_emp_id(email)
    return jsonify({"empid":empid})

@app.route('/emp/subs/<empid>/<term>/<sem>')
def get_emp_subs(empid,term,sem):
    empSubs = std6.get_emp_subjects(empid,term,sem)
    return jsonify({'subs':empSubs})


# @app.route('/<email>/role')
# def getrole(email):
#     roles=std6.get_user_roles_by_email(email)
#     return jsonify({"roles":roles})

if __name__ == "__main__":
    app.run(port=8088,debug=True)
