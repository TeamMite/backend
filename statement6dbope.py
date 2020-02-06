from pymongo import MongoClient
url="mongodb://localhost:27017/"
client=MongoClient(url)
db=client.dhi_analytics
#print(client.list_database_names())
def get_academic_year():
    dhi_internal = db.pms_placement_student_details
    academicyear=dhi_internal.aggregate([{"$group":{"_id":"null","academicyear":{"$addToSet":"$academicYear"}}},{"$project":{"academicyear":"$academicyear","_id":0}}])
    for year in academicyear:
        year=year['academicyear']
    return year

def get_term():
  term = db.dhi_term_detail.find_one({"degreeId":"BE"})
  termType=[]
  for sem in term["academicCalendar"]:
        termType.append(sem["termName"])
  termType.sort()
  return termType

def get_student_usn(email):
    collection=db.dhi_user
    usn=collection.aggregate([
        {"$match":{"email":email}},
        {"$project":{"_id":0,"usn":1}}
    ])
    res=[]
    for x in usn:
        res=x["usn"]
    return res

def get_student_placement_offers(usn,term):
    print(usn," ",term)
    collection=db.pms_placement_student_details
    offers = collection.aggregate([
    {"$unwind":"$studentList"},
    {"$match":{"studentList.regNo":usn,"academicYear":term}},
    {"$project":{"companyName":1,"salary":1,"_id":0}}
    ])
    res = []
    for x in offers:
        # print(x)
        res.append(x)
    
    return res
# get_student_placement_offers('4MT15CS066','2018-19')

def get_student_score(usn):
    score=db.dhi_user
    scoredetails=score.aggregate([
        {"$match":{"usn":usn,"education":{"$exists":"true"}}},
        {"$unwind":"$education"},
        {"$project":{"qualification":"$education.qualification","result":"$education.overallPercentage","_id":0}},
        {"$match":{"$or":[{"qualification":"X"},{"qualification":"XII"},{"qualification":"SSLC"},{"qualification":"PUC"}]}}
    ])
    res = []
    for x in scoredetails:
        res.append(x)
    return res

# get_student_score('4MT15CS066')