########################################################################################
######################          Import packages      ###################################
########################################################################################
from flask import Blueprint, send_file, url_for, render_template, flash
from flask_login import login_required, current_user
from __init__ import create_app, db
from werkzeug.utils import secure_filename
import pandas as pd
from xml.dom import minidom
import openpyxl as xl
import cgi, os
import cgitb; cgitb.enable()
from flask import Flask, render_template, redirect, url_for, request
from truecallerpy import search_phonenumber
import json
########################################################################################
#our main blueprint
main = Blueprint('main', __name__)




css_string = """
<style>
/* Add styles to the table */
.table {
  width: 100%;
  border-collapse: collapse;
  border-spacing: 0;
}

/* Add styles to the table header */
.table thead th {
  text-align: center;
  background-color: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

/* Add styles to the table body */
.table tbody td {
  text-align: center;
  border-bottom: 1px solid #ddd;
}
</style>
"""

def instid():
    if "HOME" in os.environ:
        config_dir = os.environ['HOME'] + "/.config"
    else:
        config_dir = os.environ['HOMEPATH'] + "\.config"
        # print(config_dir)
    directory = "truecallerjs"
    file = "authkey.json"
    dir_path = os.path.join(config_dir, directory)
    global pathau
    pathau = os.path.join(config_dir, directory, file)
    instIdFile = open(pathau, "r")
    content = json.load(instIdFile)
    print(content)
    id = content['installationId']
    return id     

@main.route('/') # home page that return 'index'
def index():
    return render_template('index.html')

@main.route('/profile') # profile page that return 'profile'
def profile():

    return render_template('profile.html')

@main.route('/data', methods = ['GET', 'POST'])
 
def data():

    if request.method == 'POST' and request.form['submit'] == 'view':
        f = request.files['upload']

        try:
            f.save(secure_filename(f.filename))
            print(f.filename)
            wb = xl.load_workbook(f.filename)
            sheet = wb['Sheet1']
            data= pd.read_excel(f.filename)
            html_table = data.to_html(classes=["table"])
            html_string = css_string + html_table
            return render_template('view.html' , data =html_string)
        except FileNotFoundError:

            data = "oops! Cant find file"
            file_exists="False"
            return render_template('view.html' , data =data)




    if request.method == 'POST' and request.form['submit'] == 'submit':
        f = request.files['upload']

        try:
            f.save(secure_filename(f.filename))
            fname = f.filename
            print(f.filename)
            wb = xl.load_workbook(f.filename)
            sheet = wb['Sheet1']
        except FileNotFoundError:
            data = "oops! Cant find file"
            file_exists = False
            return render_template('view.html', data=data, file_exists=file_exists)


        def cellEntry(row, column, attribute ):
            new_cell = sheet.cell(row, column)
            new_cell.value = str(attribute)
            #enters cell data in specific cell, attribute is the data entered
        def trial():
            #takes input str and the row where the corresponding data has to be printed

            for row in range(2, sheet.max_row+1):
                data = sheet.cell(int(row), 1)
                print(str(type(data.value)))
                print(data.value)
                phn = str(data.value)
                if(str(type(data.value)) != "<class 'int'>"):
                    cellEntry(row, 2 , "invalid character")
                else:
                    if(len(str(data.value)) != 10):
                        cellEntry(row, 2 , "invalid number")
                    else:
                        
                        id = instid()
                        json_data = search_phonenumber(phn, "IN", id)
                        for item in json_data['data']:
                            cellEntry(1,1,"Phone Number")
                            for phone in item['phones']:
                                cellEntry(row,1,phone['e164Format'])
                            cellEntry(1,2,"ID")
                            cellEntry(row,2,item['id'])
                            cellEntry(1,3,"Name")
                            cellEntry(row,3,item['name'])
                            cellEntry(1,4,"Score")
                            cellEntry(row,4,item['score'])
                            cellEntry(1,5,"image")
                            if 'image' in item and item['image'] is not None:
                                cellEntry(row,5,item['image'])
                            cellEntry(1,6,"Access")
                            cellEntry(row,6,item['access'])

                            cellEntry(1,7,"city")
                            for address in item['addresses']:
                                cellEntry(row,7,address['city']) 
                        
                        

        trial()
        wb.save('result.xlsx')
        data= pd.read_excel('result.xlsx')
        html_table = data.to_html(classes=["table"])
        html_string = css_string + html_table
        return render_template('data.html' , data =html_string)

@main.route('/download')
def download():
         path = 'result.xlsx'
         return send_file(path, as_attachment=True)
     
@main.route('/singleNumber', methods=['POST'])
def singleNumber():
    if request.method == 'POST':
        search_number = request.form['search_number']

        try:
            id = instid()
            json_data = search_phonenumber(search_number, "IN", id)
            if json_data is not None and 'data' in json_data:
                return render_template('profile.html', json_data=json_data)
            else:
                raise Exception('Invalid response from search_phonenumber')
        except Exception as e:
            print(f"Error occurred: {e}")
            json_data = {"data": {
                "name": "",
                "id": "",
                "access": "",
                "score": "",
                "addresses": [],
                "image": "",
                "phones": [],
                "error": "While searching the phone number an error occured. Try Again Later",
            }}
            return render_template('profile.html', json_data=json_data)

     


app = create_app() # we initialize our flask app using the __init__.py function
if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run() # run the flask app on debug mode
