from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
import datetime
import mysql.connector
from mysql.connector import FieldType
import connect

app = Flask(__name__)

dbconn = None
connection = None


def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
                                         password=connect.dbpass, host=connect.dbhost, \
                                         database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn


@app.route("/")
def home():
    return render_template("base.html")

# OPL第三方包，内置了写好的模型，图片路径传进去
# 中间的所有

@app.route("/add_borrower", methods=['POST', "GET"])
def add_borrower():
    if request.method == "POST":
        form = (request.form)
        connection = getCursor()
        connection.execute("""
                INSERT INTO library.borrowers (firstname, familyname, dateofbirth,
                 housenumbername, street, town, city, postalcode)
VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');
                """
                           .format(form.get('firstname'), form.get('familyname'), form.get('dateofbirth'),
                                   form.get('housenumbername'), form.get('street'), form.get('town'),
                                   form.get('city'), form.get('postalcode')))
    return render_template("addborrower.html")


@app.route("/firstpage")
def firstpage():
    search = request.args.get('search')
    bookList = []
    if search:
        connection = getCursor()
        connection.execute("""
        select br.borrowerid,
       br.firstname,
       br.familyname,
       l.borrowerid,
       l.bookcopyid,
       l.loandate,
       l.returned,
       b.bookid,
       b.booktitle,
       b.author,
       b.category,
       b.yearofpublication,
       bc.format
from books b         inner join bookcopies bc on b.bookid = bc.bookid
         inner join loans l on bc.bookcopyid = l.bookcopyid
         inner join borrowers br on l.borrowerid = br.borrowerid
where concat(b.booktitle, b.author) like '%{}%' or  concat(b.booktitle, b.author) like '%{}%'
and l.bookcopyid not in (SELECT l.bookcopyid from loans where returned <> 1 or returned is NULL)
order by br.familyname, br.firstname, l.loandate;
        """
                           .format(search, search))
        bookList = connection.fetchall()
        print(bookList)
    return render_template("firstpage.html", booklist=bookList)
# 基本数据结构
# 列表，字典，
# 类
# def
# define
# 函数名(id)

@app.route("/availablity_books")
def availablity_books():
    search = request.args.get('search')
    availablity_books_list = []
    connection = getCursor()
    connection.execute("""
select b.booktitle,b.author,l.returned,l.loandate
        from books b
        inner join bookcopies bc on b.bookid = bc.bookid
         inner join loans l on bc.bookcopyid = l.bookcopyid
    order by booktitle;
    """
                       .format(search, search))
    availablity_books_list = connection.fetchall()
    print(availablity_books_list)
    return render_template("availablity_books.html", availablity_books_list=availablity_books_list)


@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if fmt is None:
        fmt = '%Y-%m-%d '
    return (date + datetime.timedelta(days=28)).strftime(fmt)


# The second interface, not requiring any log in, is focused on library staff,
# allowing them toissue books to borrowers and return books that have been on loan.


@app.route("/admin")
def admin():
    loanlist = []
    return render_template("admin.html", loanlist=loanlist)



@app.route("/search_borrower")
def search():
    search = request.args.get('search')
    borrowers = []
    if search:
        connection = getCursor()
        connection.execute("""   select *
from borrowers
where borrowerid='{}' or firstname like '%{}%' or familyname like '%{}%';         """
                           .format(search, search, search))
        borrowers = connection.fetchall()  # sql line
        print(borrowers)
    return render_template("search.html", borrowers=borrowers)


@app.route("/borrowing", methods=['POST', 'GET'])
def borrowing():
    if request.method == "POST":
        borrowerid = request.form.get('borrower')
        bookid = request.form.get('book')
        loandate = request.form.get('loandate')
        cur = getCursor()
        cur.execute("INSERT INTO loans (borrowerid, bookcopyid, loandate, returned) VALUES(%s,%s,%s,0);",
                    (borrowerid, bookid, str(loandate),))
        return redirect('/admin')
    todaydate = datetime.datetime.now().date()
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    sql = """SELECT *
    FROM bookcopies
             inner join books on books.bookid = bookcopies.bookid
    WHERE bookcopyid not in (SELECT bookcopyid from loans where returned <> 1 or returned is NULL);"""
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("borrowing.html", loandate=todaydate, borrowers=borrowerList, books=bookList)


@app.route("/borrowing_management", methods=['POST', 'GET'])
def borrowing_management():
    if request.method == "POST":
        pass
    connection = getCursor()
    sql = """ select br.borrowerid, br.firstname, br.familyname,  
                    l.loanid,l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author,
                    b.category, b.yearofpublication, bc.format
                from books b
                    inner join bookcopies bc on b.bookid = bc.bookid
                        inner join loans l on bc.bookcopyid = l.bookcopyid
                            inner join borrowers br on l.borrowerid = br.borrowerid
                where l.returned =0
                order by br.familyname, br.firstname, l.loandate;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("borrowing_management.html", loanlist=loanList)


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    if request.method == "POST":
        form = (request.form)
        connection = getCursor()
        connection.execute("""
                        UPDATE library.borrowers t
SET t.firstname       = '{}',
    t.familyname      = '{}',
    t.dateofbirth     = '{}',
    t.housenumbername = '{}',
    t.street          = '{}',
    t.town            = '{}',
    t.city            = '{}',
    t.postalcode      = '{}'
WHERE t.borrowerid = {};
                        """
                           .format(form.get('firstname'), form.get('familyname'), form.get('dateofbirth'),
                                   form.get('housenumbername'), form.get('street'), form.get('town'),
                                   form.get('city'), form.get('postalcode'), int(form.get('id'))))
        return redirect("/borrower_management")
    id = request.args.get('id')
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers where borrowerid={};".format(int(id)))
    borrower = connection.fetchone()
    return render_template("editborrower.html", borrower=borrower)


@app.route("/return", methods=['POST', 'GET'])
def returnd():
    id = request.args.get('loan_id')
    connection = getCursor()
    connection.execute("""
    UPDATE library.loans t
    SET t.returned = 1
    WHERE t.loanid = {};
    """.format(int(id)))

    return redirect('/borrowing_management')


@app.route("/overdue_list", methods=['POST', 'GET'])
def overdue():
    connection = getCursor()
    connection.execute("""
    select b3.booktitle,b3.category,b.familyname,b.firstname,b2.format,loandate
     from loans
    join borrowers b on b.borrowerid = loans.borrowerid
    join bookcopies b2 on b2.bookcopyid = loans.bookcopyid
    join books b3 on b3.bookid = b2.bookid
    where datediff(now(),loans.loandate)>35 and returned=0
        order by loandate;
    """)
    overdue_list = connection.fetchall()
    return render_template("overdue_list.html", overdue_list=overdue_list)


@app.route("/load_summary", methods=['POST', 'GET'])
def load_summary():
    connection = getCursor()
    connection.execute("""
    select b3.booktitle,b3.category,b.familyname,b.firstname,b2.format,count(*)
    from loans
    join borrowers b on b.borrowerid = loans.borrowerid
    join bookcopies b2 on b2.bookcopyid = loans.bookcopyid
    join books b3 on b3.bookid = b2.bookid
    group by loanid

    """)
    load_summary_list = connection.fetchall()
    return render_template("overdue_list.html", load_summary=load_summary_list)


@app.route("/borrower_summary", methods=['POST', 'GET'])
def borrower_summary():
    connection = getCursor()
    connection.execute("""
    select b3.booktitle,b3.category,b.familyname,b.firstname,b2.format,count(*)
    from loans
    join borrowers b on b.borrowerid = loans.borrowerid
    join bookcopies b2 on b2.bookcopyid = loans.bookcopyid
    join books b3 on b3.bookid = b2.bookid
    group by loanid
    order by b.firstname
    """)
    borrower_summary_list = connection.fetchall()
    return render_template("overdue_list.html", borrower_summary=borrower_summary_list)


@app.route("/borrower_management")
def borrower_management():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    print(borrowerList)
    return render_template("admin.html", borrowerList=borrowerList)


@app.route("/listbooks")
def listbooks():
    connection = getCursor()
    connection.execute("SELECT * FROM books;")
    bookList = connection.fetchall()
    print(bookList)
    return render_template("booklist.html", booklist=bookList)


@app.route("/loanbook")
def loanbook():
    todaydate = datetime.now().date()
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    sql = """SELECT * FROM bookcopies
inner join books on books.bookid = bookcopies.bookid
 WHERE bookcopyid not in (SELECT bookcopyid from loans where returned <> 1 or returned is NULL);"""
    connection.execute(sql)
    bookList = connection.fetchall()
    return render_template("addloan.html", loandate=todaydate, borrowers=borrowerList, books=bookList)


@app.route("/loan/add", methods=["POST"])
def addloan():
    borrowerid = request.form.get('borrower')
    bookid = request.form.get('book')
    loandate = request.form.get('loandate')
    cur = getCursor()
    cur.execute("INSERT INTO loans (borrowerid, bookcopyid, loandate, returned) VALUES(%s,%s,%s,0);",
                (borrowerid, bookid, str(loandate),))
    return redirect("/currentloans")


@app.route("/listborrowers")
def listborrowers():
    connection = getCursor()
    connection.execute("SELECT * FROM borrowers;")
    borrowerList = connection.fetchall()
    return render_template("borrowerlist.html", borrowerlist=borrowerList)


@app.route("/currentloans")
def currentloans():
    connection = getCursor()
    sql = """ select br.borrowerid, br.firstname, br.familyname,  
                l.borrowerid, l.bookcopyid, l.loandate, l.returned, b.bookid, b.booktitle, b.author, 
                b.category, b.yearofpublication, bc.format 
            from books b
                inner join bookcopies bc on b.bookid = bc.bookid
                    inner join loans l on bc.bookcopyid = l.bookcopyid
                        inner join borrowers br on l.borrowerid = br.borrowerid
            order by br.familyname, br.firstname, l.loandate;"""
    connection.execute(sql)
    loanList = connection.fetchall()
    return render_template("currentloans.html", loanlist=loanList)
