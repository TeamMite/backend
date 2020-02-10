from pymongo import MongoClient
import re
import math
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
        {"$unwind":"$education" },
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

def get_emp_sub_education(empID,year,sub,sem):
    collection = db.dhi_student_attendance
    students = collection.aggregate([
        {"$match":{"faculties.employeeGivenId" :empID,"departments.termName": sem ,"courseName":sub,"academicYear":year}},
        {"$unwind":"$students"},
        {"$group":{"_id":"$courseName","studentUSNs":{"$addToSet":"$students.usn"}}},
    ])
    res = []
    for x in students:
        res.append(x)
    education = []
    for x in res:
        for usn in x["studentUSNs"]:
            edu = get_student_education(usn)
            for e in edu:
                education.extend(edu)
    
    xCount = 0
    xiiCount = 0
    xMarks = 0
    xiiMarks = 0
    for edu in education:
        e = edu['education']
        if "qualification" in e.keys() and ("overallPercentage" in e.keys()):
            if e["qualification"] == "X" or e["qualification"] == "SSLC":
                if True or e["board"] != "CBSE":
                    marks = e["overallPercentage"]
                else:
                    marks = e["overallPercentage"] 
                xCount += 1
                xMarks += marks
            if e["qualification"] == "XII" or e["qualification"] == "PUC":
                if True or  e["board"] != "CBSE":
                    marks = e["overallPercentage"]
                else:
                    marks = e["overallPercentage"] 
                xiiCount += 1
                xiiMarks += marks
    
    # print(xCount," : ",round(xMarks/xCount))
    # print(xiiCount," : ",round(xiiMarks/xiiCount))
    if xCount != 0:
        m1 = round(xMarks/xCount)
    else:
        m1 = 0
    if xiiCount != 0:
        m2 = round(xiiMarks/xiiCount)
    else:
        m2 = 0
    return (m1,m2)

def get_emp_subjects(empid,term,sem):
    collection = db.dhi_internal
    marks = collection.aggregate([
    {"$match":{"faculties.facultyGivenId":empid,"academicYear":term,"departments.termName":sem}},
    {"$unwind":"$departments"},
    {"$unwind":"$studentScores"},
    {"$match":{"studentScores.totalScore":{"$gt":0}}},
    {"$group":{"_id":"$courseCode","courseCode":{"$first":"$courseCode"},"courseName":{"$first":"$courseName"}}},
    {"$project":{"_id":0}}
    ])
    res = []
    for mark in marks:
        place = get_emp_sub_placement(empid,mark['courseName'],sem)
        education = get_emp_sub_education(empid,term,mark['courseName'],sem)
        mark['xPercentage'] = education[0]
        mark['xiiPercentage'] = education[1]
        if place[0] != 0:
            mark['placePercentage'] = 100 * place[1] / place[0]
        else:
            mark['placePercentage'] = 0
        res.append(mark)
    return res

def get_emp_sub_details(empid,term,sem,subject):
    collection = db.dhi_internal
    marks = collection.aggregate([
    {"$match":{"faculties.facultyGivenId":empid,"academicYear":term,"departments.termName":sem,"courseName":subject}},
    {"$unwind":"$departments"},
    {"$unwind":"$studentScores"},
    {"$match":{"studentScores.totalScore":{"$gt":0}}},
    {"$group":{"_id":"$courseCode","courseCode":{"$first":"$courseCode"},"courseName":{"$first":"$courseName"}}},
    {"$project":{"_id":0}}
    ])
    res = []
    for mark in marks:
        place = get_emp_sub_placement(empid,mark['courseName'],sem)
        education = get_emp_sub_education(empid,term,mark['courseName'],sem)
        mark['xPercentage'] = education[0]
        mark['xiiPercentage'] = education[1]
        if place[0] != 0:
            mark['placePercentage'] = 100 * place[1] / place[0]
        else:
            mark['placePercentage'] = 0
        res.append(mark)
    return res

def get_emp_sub_placement(empID,sub,sem):
    collection = db.dhi_student_attendance
    students = collection.aggregate([
        {"$match":{"faculties.employeeGivenId" : empID,"departments.termName":sem,"courseName":sub}},
        {"$unwind":"$students"},
        {"$group":{"_id":"$courseName","studentUSNs":{"$addToSet":"$students.usn"}}},
    ])
    res = []
    for x in students:
        res.append(x)
    totalStudents = 0
    filtered = []
    for x in res:
        for usn in x["studentUSNs"]:
            status = get_placed_details(usn)
            if status!=0:
                filtered.append(status)
            totalStudents = len(x["studentUSNs"])
    # print("filtered",filtered)
    # print(f"Placed Students :{len(filtered)},No.of Offers : {sum(filtered)}")
    return (totalStudents,len(filtered),sum(filtered))

def get_placed_details(usn):
    collection = db.pms_placement_student_details
    people = collection.aggregate([
    {"$match":{"studentList.regNo":usn}},
    {"$unwind":"$studentList"},
    {"$match":{"studentList.regNo":usn}},
    ])
    res = []
    for x in people:
        res.append(x)
    return len(res)

def get_student_education(usn):
    collection = db.dhi_user
    education = collection.aggregate([
        {"$match":{"usn":usn}},
        {"$unwind":"$education"},
        {"$project":{"education":1,"_id":0}},
    ])
    one =  [ e for e in education]
    return one
get_emp_sub_education("CSE308","2017-18","SOFTWARE TESTING","Semester 8")