from app_factory import create_app
from db import db  # Make sure this points to your db module
from user_model import User
from file_model import File
from policy_manager import PolicyManager

def store_generated_policy():
    # Use lists instead of sets for ids and departments
    user_data = {

        "DistrictName": ["district1", "district2", "district3", "district4", "district5"],
        "SchoolName": ["school1", "school2", "school3", "school4", "school5"],
        "ClassID": ["class1", "class1", "class1", "class1", "class1"]
    }
    
    file_data = {
        "DistrictName": ["district1", "district2", "district3", "district4", "district5"],
        "SchoolName": ["school1", "school2", "school3", "school4", "school5"],
        "ClassID": ["class1", "class1", "class1", "class1", "class1"]
    }
    
    policy_manager = PolicyManager()
    
    for i in range(len(user_data["username"])):
        # Create User and File objects using correct list indexing
        user = User(username=user_data["username"][i], password=user_data["password"][i], department=user_data["department"][i])
        file = File(name=file_data["name"][i], department=file_data["department"][i], type="", content="")

        # Now, user.id and file.id should be available
        policy_generated = policy_manager.generate_policy(user, file)
        
        if policy_generated:
            print(f"Policy generated successfully for {user.username} and {file.name}")
        else:
            print(f"Policy generation failed for {user.username} and {file.name}")

# Create the app and push the app context
app = create_app()  # Ensure create_app initializes your Flask app properly
with app.app_context():
    store_generated_policy()
