"""
ATM

Username    Phone   Acc No.     PIN     User ID     Avl. Bal.
Anjali      1234    452452      1414    A111        10000
Honey       1244    748596      2563    H112        20000
Harsh       1734    784152      4785    H113        25000
Keval       1234    965263      0125    K114        80000


1. Withdraw Money(function)
    -> amt less than avl bal
    -> atm only have 500 notes

2. Deposit Money
    -> we can only deposit 500 notes amount
    -> deposit amt more than 3000 

3. Show withdraw history

4. Show deposit history

5. Show available balance

6. Exit
    
Program flow

1. take User id and password from user
2. check user id and password
3. if true -> show options
4. do transactions
5. save data
6. exit
"""

user_data = {
    "A111":{
        "username": "Anjali",
        "phone": "1234",
        "acc_no": "452452",
        "pin": "1414",
        "user_id": "A111",
        "avl_bal": 10000,
        "history":{
            "withdraw_history": [],
            "deposit_history": []
        }
    },
    "H112":{
        "username": "Honey",
        "phone": "1244",
        "acc_no": "784152",
        "pin": "2563",
        "user_id": "H112",
        "avl_bal": 20000,
        "history":{
            "withdraw_history": [],
            "deposit_history": []
        }
    },
    "H113":{
        "username": "Harsh",
        "phone": "1734",
        "acc_no": "748596",
        "pin": "4785",
        "user_id": "H113",
        "avl_bal": 25000,
        "history":{
            "withdraw_history": [],
            "deposit_history": []
        }
    },
        "K114":{
        "username": "Keval",
        "phone": "1234",
        "acc_no": "965263",
        "pin": "0125",
        "user_id": "K114",
        "avl_bal": 80000,
        "history":{
            "withdraw_history": [],
            "deposit_history": []
        }
    }
    
}
id_final = ""
#print(user_data["K114"]["avl_bal"])
def login():
    id=input(" enter user_id :")
    user_pin=input(" enter your pin : ")
    if user_data[id]["user_id"]==id  and user_data[id]["pin"]==user_pin :
        print(" login succesfully... ")
        return True
    else:
        print(" invalid id or passwrod ")
        return False
      

def get_id():
    id=input("enter your id : ")
    return id
    
    
def withdraw():
    id_1=get_id()
    amount=int(input("enter amount to withdraw : "))
    #print(user_data[id_1]["avl_bal"])
    if amount<=user_data[id_1]["avl_bal"]:
        if amount/500:
            user_data[id_1]["avl_bal"]=user_data[id_1]["avl_bal"]-amount
            print(f"your avilable balance : {user_data[id_1]["avl_bal"]}")
            user_data[id_1]["history"]["withdraw_history"].append(amount)
        else:
            print("atm have only 500 notes../nenter valid amount to withdraw.")
    else:
        print("not sufficent balance in your account.")
 
 
 
def deposit():
    id_2=get_id()
    amount=int(input("enter amount to deposit : "))
    if amount>=5000:
        if amount/500:
            user_data[id_2]["avl_bal"]=user_data[id_2]["avl_bal"]+amount
            print(f"your avilable balance : {user_data[id_2]["avl_bal"]}")
            user_data[id_2]["history"]["deposit_history"].append(amount)
        else:
            print("enter amout in multiple of 500..")
    else:
        print("you can deposite only more than 5000")
 
    
def withdrawhistory():
    id_3=get_id()
    print(f"your withdraw history : {user_data[id_3]["history"]["withdraw_history"]}")
    
    
def  deposithistory():
    id_4=get_id()
    print(f"your deposit history : {user_data[id_4]["history"]["deposit_history"]}")
    
    
    
def avilablebalance():
    id_5=get_id()
    print(f"your available balance : {user_data[id_5]["avl_bal"]}")
    A
    
def  add_user():
    new_user={}
    history_1={"withdraw_history":[],"deposit_history":[]}
    user_name=input(" enter username : ")
    acc_no=input("enter account number : ")
    number=input("enter contact number : ")
    pin1=input("enter  pin : ")
    user_id1=input("enter user id : ")
    balance=input("enter available balance  : ")
    user_data.update({user_id1:""})
    new_user["username"]=user_name
    new_user["phone"]=number
    new_user["acc_no"]=acc_no
    new_user["pin"]=pin1
    new_user["user_id"]=user_id1
    new_user["history"]=history_1
    user_data["user_id1"]=new_user

    
    
def resetpin():
    id_6=get_id()
    new_pin=input("enter new pin :")
    #print(user_data[id_6]["pin"])
    user_data[id_6]["pin"]=new_pin
    print(user_data)
    
 
def  clear_withdrawhistory():
    id_7=get_id()
    if user_data[id_7]["history"]["withdraw_history"] == []:
        print(" your withdraw history is empty.")
    else:
        user_data[id_7]["history"]["withdraw_history"].clear()
        print(f"your withdraw history : {user_data[id_7]["history"]["withdraw_history"]}")
 
 
def  clear_deposithistory():
    id_8=get_id()
    if user_data[id_8]["history"]["deposit_history"] == []:
        print(" your deposit history is empty.")
    else:
        user_data[id_8]["history"]["deposit_history"].clear()
        print(f"your withdraw history : {user_data[id_8]["history"]["deposit_history"]}")
        
        
if login():   
    while True:    
        print("1. Withdraw Money")
        print("2. Deposit Money")
        print("3. Show withdraw history")
        print("4. Show deposit history")
        print("5. Show available balance")
        print("6. add user")
        print("7. resetpin")
        print("8. clear withdrawhisroy")
        print("9. clear depositwhisroy")
        print("10.exit")
        choice=int(input("enter your choice : "))
        if choice==1:
            withdraw()
        elif choice==2:
            deposit()
        elif choice==3:
            withdrawhistory()
        elif choice==4:
            deposithistory()
        elif choice==5:
            avilablebalance()
        elif choice==6:
            add_user()
        elif choice==7:
            resetpin()
        elif choice==8:
            clear_withdrawhistory()            
        elif choice==9:
            clear_deposithistory()
        else:
            print("......")
else:
    login()
    
    
    
        
       
       
