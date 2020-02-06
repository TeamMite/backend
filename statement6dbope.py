from pymongo import MongoClient
import re
import bson
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

def get_all_depts():
    collection=db.dhi_user
    depts=collection.aggregate([{"$match":{"roles.roleName":"FACULTY"}},{"$project":{"_id":0,"employeeGivenId":1}}])
    res=[]
    for d in depts:
        if "employeeGivenId" in d:
            res.append(d["employeeGivenId"])
    dept=[]
    for d in res:
        name=re.findall('([a-zA-Z]*).*',d)
        if name[0].upper() not in dept:
            dept.append(name[0].upper())
    dept.remove('ADM')
    dept.remove('EC')
    return dept

def get_faculties_by_dept(dept):
    collection=db.dhi_user
    pattern=re.compile(f'^{dept}')
    regex=bson.regex.Regex.from_native(pattern)
    regex.flags ^=re.UNICODE
    faculties=collection.aggregate([
        {"$match":{"roles.roleName":"FACULTY","employeeGivenId":{"$regex":regex}}},{"$project":{"employeeGivenId":1,"name":1,"_id":0} }

    ])
    res=[]
    for x in faculties:
        res.append(x)
    return res
def get_emp_id(email):
    collection=db.dhi_user
    usn=collection.aggregate([{"$match":{"email":email}},{"$project":{"_id":0,"employeeGivenId":1}}])
    res=[]
    for x in usn:
        res=x["employeeGivenId"]
    return res
    
# def get_user_roles_by_email(email):
#     collection=db.dhi_user
#     roledetails=collection.aggregate([
#     {"$match":{"email":email}},
#     {"$project":{"email":1,"roles.roleName":1,"_id":0}}])
#     res=[]
#     for x in roledetails:
#         res.append(x)
#     return res

# get_student_score('4MT15CS066')