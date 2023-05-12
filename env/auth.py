########################################################################################
######################          Import packages      ###################################
########################################################################################
import os
import phonenumbers

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from flask_login import login_user, logout_user, login_required, current_user
from __init__ import db
import random
import requests
import json

with open('phonesList.json', 'r') as f:
    phones_list = json.load(f)
 
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
r_path = os.path.join(config_dir, directory, "request.json")

auth = Blueprint('auth', __name__) # create a Blueprint object that we name 'auth'

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        try:
            phone_number = request.form.get('pNum')
            raw_phone_number = phonenumbers.parse(phone_number, region='IN')
            remember = True if request.form.get('remember') else False

            if not phonenumbers.is_possible_number(raw_phone_number):
                flash('Please enter a valid phone number and try again')
                return redirect(url_for('auth.login'))

            return redirect(url_for('auth.otp', phone_number=phone_number))

        except Exception as e:
            flash('An error occurred. Please try again.')
            print(f'An error occurred in login(): {str(e)}')
            return redirect(url_for('auth.login'))




def generate_random_string(length):
    characters = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(characters) for i in range(length))

@auth.route('/otp', methods=['GET', 'POST'])
def otp():
    res = None
    error_message = None
    
    if request.method == 'GET':
        global phoneNum
        phoneNum = request.args.get('phone_number')
        data = {
            "countryCode": "IN",
            "dialingCode": 91,
            "installationDetails": {
                "app": {
                    "buildVersion": 5,
                    "majorVersion": 11,
                    "minorVersion": 7,
                    "store": "GOOGLE_PLAY"
                },
                "device": {
                    "deviceId": generate_random_string(16),
                    "language": "en",
                    "manufacturer": random.choice(phones_list)["manufacturer"],
                    "model": random.choice(phones_list)["model"],
                    "osName": "Android",
                    "osVersion": "10",
                    "mobileServices": ["GMS"]
                },
                "language": "en"
            },
            "phoneNumber": phoneNum,
            "region": "region-2",
            "sequenceNo": 2
        }

        headers = {
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "Truecaller/11.75.5 (Android;10)",
            "clientsecret": "lvc22mp3l1sfv6ujg83rd17btt"
        }

        print(f"Sending OTP to {phoneNum}")
        res = requests.post("https://account-asia-south1.truecaller.com/v2/sendOnboardingOtp", json=data, headers=headers)
        
        global resj
        resj = res.json()
        print(resj)
        # Check OTP sent status
        
        if res.json().get("status") == 9:
            flash("OTP already sent - Enter It")
            
    
        if res.json().get("status") == 6:
            flash("Phone number blocked to reuse - Try again later")
            return redirect(url_for('main.profile'))
        if res.json().get("status") == 5:
            flash("Phone number limit reached - Try again later")
            block_input = True
            return render_template('otp.html', block_input=block_input)
        
        if res.json().get("status") in [1, 9] or res.json().get("message") == "Sent":
            with open(r_path, "w") as f:
                json.dump(res.json(), f, indent=4)
            print("Otp sent successfully")
        else:
            res = None
        
        return render_template('otp.html')
    
    
    
    # if res:
    #     return redirect(url_for('main.profile', res=res.json()))
    # else:
    #     return render_template('otp.html')  # Render a template to show OTP send failure.
    
 
    if request.method == 'POST':
        # Verify OTP code
        otp = request.form['OTP']
        otp = str(otp)

        try:
            if verify_otp(phoneNum, otp, resj):
                # Redirect to profile page if OTP is verified
                print("OTP verified", otp)
                return redirect(url_for('main.profile'))
            else:
                # Add error message to flash message and render the OTP form again
                error_message = 'Invalid OTP. Please try again.'
                
        except Exception as e:
            print("Error occurred during OTP verification:", str(e))
            error_message = 'An error occurred'
        
        if error_message is not None:
            flash(error_message, 'error')
            return redirect(url_for('auth.otp', phone_number=phoneNum))


def verify_otp(phone_number, otp, resj):
    postData = {
            "countryCode": "IN",
            "dialingCode": 91,
            "phoneNumber": phone_number,
            "requestId": resj['requestId'],
            "token": otp
        }
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "accept-encoding": "gzip",
        "user-agent": "Truecaller/11.75.5 (Android;10)",
        "clientsecret": "lvc22mp3l1sfv6ujg83rd17btt"
    }

    
    resp = requests.post('https://account-asia-south1.truecaller.com/v1/verifyOnboardingOtp', headers=headers, json=postData)
    
    try:
        res_json = resp.json()
    except json.JSONDecodeError as e:
        print("Error decoding JSON response:", e)
        return False
    
    print("res_json is : ", resp.json())
    if resp.json().get("status") in [1, 2, 9]:
        authKeyFile = open(pathau, "w")
        json.dump(resp.json(),authKeyFile)
        authKeyFile.close()
        print('------returning true-------Installation id : ', res_json["installationId"])
        return True
       
    else:
        print("OTP verification failed")
        return False
        
         

@auth.route('/logout') # define logout path
@login_required
def logout(): #define the logout function
    logout_user()
    if os.path.exists("result.xlsx"):
        os.remove("result.xlsx")
    return redirect(url_for('main.index'))