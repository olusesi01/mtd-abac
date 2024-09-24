from py_abac import PDP
from py_abac.storage.memory import MemoryStorage
from py_abac import AccessRequest
import json
from py_abac import PDP, AccessRequest, Policy as AbacPolicy
from py_abac.storage.memory import MemoryStorage
import json

class PolicyManager:
    
    def __init__(self):
        self.storage = MemoryStorage()
        self.pdp = PDP(self.storage)
        self.policy_counter = 1  # Sequential policy ID counter
        self.highest_counter = 1

    def load_policies_from_db(self):
        from app_factory import create_app, db
        from policy_model import Policy
        from py_abac import Policy as AbacPolicy
        self.storage = MemoryStorage()

        try:
            # Get all current policies from MemoryStorage
            current_policies = list(self.storage.get_all(limit=10, offset=0))

            # Remove existing policies from MemoryStorage
            #for policy in current_policies:
                #self.storage.remove(policy.id)
            
            # Fetch all policies from the database
            all_policies_db = Policy.query.all()

            # Get the highest policy id in the database
            highest_counter = db.session.query(db.func.max(Policy.id)).scalar()

            # If there are policies in the database, start incrementing from the highest id
            if highest_counter is None:
                self.highest_counter = 0  # No existing policies
            else:
                self.highest_counter = highest_counter
            
            # Load policies into MemoryStorage
            for policy_db in all_policies_db:
                # Convert Policy object from database to py-abac Policy
                policy_data = {
                    "uid": str(policy_db.id),
                    "description": policy_db.description,
                    "effect": policy_db.effect,
                    "rules": json.loads(policy_db.rules),
                    "targets": json.loads(policy_db.targets),
                    "priority": policy_db.priority
                }
                abac_policy = AbacPolicy.from_json(policy_data)
                self.storage.add(abac_policy)
            
            print("Policies successfully loaded from database into memory storage.")
        except Exception as e:
            print(f"Error loading policies from database: {e}")





    def delete_all_policies_from_db(self):
        from app_factory import create_app, db
        from policy_model import Policy

        try:
            # Fetch all policies from the database
            all_policies_db = Policy.query.all()

            if not all_policies_db:
                print("No policies found in the database.")
                return

            # Delete all policies from the database
            for policy_db in all_policies_db:
                db.session.delete(policy_db)

            # Commit the changes to the database
            db.session.commit()

            print("All policies have been successfully deleted from the database.")
        except Exception as e:
            db.session.rollback()  # Roll back the session in case of an error
            print(f"Error deleting policies from database: {e}")




    def generate_policy(self, user, file):
        try:
            # Generate a sequential policy ID
            policy_id = f"policy_{self.policy_counter}"
            self.policy_counter += 1
            policy_data = {
                "uid": policy_id,
                "description": "Dynamic policy for file access",
                "effect": "allow",
                "rules": {
                    "subject": {

                        "$.districtname": {
                            "condition": "Equals",
                            "value": user.DistrictName
                        },
                        "$.schoolname": {
                            "condition": "Equals",
                            "value": user.SchoolName
                        },
                        "$.classid": {
                            "condition": "Equals",
                            "value": user.ClassID
                        }
                    },
                    "resource": {
                        "$.districtname": {
                            "condition": "Equals",
                            "value": file.DistrictName
                        },
                        "$.schoolname": {
                            "condition": "Equals",
                            "value": file.SchoolName
                        },
                        "$.classid": {
                            "condition": "Equals",
                            "value": file.ClassID
                        }
                    },
                    "action": {
                        "$.method": {
                            "condition": "Equals",
                            "value": "view"
                        }
                    }
                },
                "targets": {},
                "priority": 0
            }
            print("Policy Data:", policy_data)

            # Step 1: Store policy in memory (using py-abac)
            abac_policy = AbacPolicy.from_json(policy_data)
            self.storage.add(abac_policy)

            # Step 2: Store policy in the database
            from app_factory import create_app, db
            from policy_model import Policy

            # Convert the JSON data to a Policy object for database storage
            policy_db = Policy(
                description=policy_data["description"],
                effect=policy_data["effect"],
                rules=json.dumps(policy_data["rules"]),  # Store rules as JSON text
                targets=json.dumps(policy_data["targets"]),  # Store targets as JSON text
                priority=policy_data["priority"]
            )

            db.session.add(policy_db)
            db.session.commit()
            print("Policy successfully added to database.")

            # Print all stored policies for debugging
            #all_policies = list(self.storage.get_all(limit=10, offset=0))  # Convert generator to list
            #print("All Stored Policies:", all_policies)
            #all_policies = list(self.storage.get_all(limit=10, offset=0))  # Convert generator to list
            #print("All Stored Policies:", [policy.to_dict() for policy in all_policies])


            all_policies_db = Policy.query.all()
            print("All Policies in Database:")
            for policy in all_policies_db:
                print({
                    "policy_id": policy.id,
                    "description": policy.description,
                    "rules": json.loads(policy.rules),
                    "targets": json.loads(policy.targets),
                    "priority": policy.priority
                })
            #print("All Policies in Database:", all_policies_db)

            return True
        except Exception as e:
            print(f"Error during policy creation: {e}")
            return False



    def evaluate_request(self, user, file):
        access_request = {
                "subject": {
                    "id": "",
                    "attributes": {
                        "districtname": user.DistrictName,  # Note lowercase "districtname"
                        "schoolname": user.SchoolName,
                        "classid": user.ClassID
                    }
                },
                "resource": {
                    "id": "",
                    "attributes": {
                        "districtname": file.DistrictName,
                        "schoolname": file.SchoolName,
                        "classid": file.ClassID
                    }
                },
                "action": {
                    "id": "",
                    "attributes": {"method": "view"}
                },
                "context": {}
            }

        try:
            #policy_manager = PolicyManager()
            # Dynamically generate policy for user and file

            self.generate_policy(user, file)
            #self.delete_all_policies_from_db()
            self.load_policies_from_db()

            # Convert access request to py-abac format
            request = AccessRequest.from_json(access_request)
            
            # Step 1: Load policies and check initial access
            
            initial_status = self.pdp.is_allowed(request)
            print("Initial access status:", initial_status)
            
            if initial_status:
                return True  # Access granted with real attributes
            
            # Step 2: If access is denied, check for correlated attributes
            correlated_attributes = self.get_correlated_attributes(user, file)
            if correlated_attributes:
                print("Correlated attributes found:", correlated_attributes)
                
                # Step 3: Update policy with correlated attributes
                self.update_policy_with_correlated_attributes(user, file, correlated_attributes)
                
                # Step 4: Re-evaluate access with updated policies
                #self.storage = MemoryStorage()
                self.load_policies_from_db()  # Reload updated policies
                recheck_status = self.pdp.is_allowed(request)
                print("Access status with correlated attributes:", recheck_status)
                
                return recheck_status  # Return the updated access status
            
            # No correlated attributes found, or access still denied
            return False

        except Exception as e:
            print(f"Error evaluating request: {e}")
            return False

    def get_correlated_attributes(self, user, file):
        # Integrate your association model to retrieve correlated attributes for the user or file
        # Return a dictionary of correlated attributes or None if no correlation exists
        # Example: return {'username': 'correlated_username', 'department': 'correlated_department'}
        corr_schoolname_list = ['Romoland Elementary', 'M. H. Stanley Middle', 'West Park Charter Academy', 'Bret Harte Union High', 'Harvest Valley Elementary', 'Ethan A Chase Middle', 'Boulder Ridge Elementary', 'John Vierra High', 'Lafayette Elementary', 'Mesa View Elementary', 'West Park Elementary']
        corr_classid_list = ['9656711130', '02-01-Gym', '03-01-GYM', '07-01-Gym', '593623304', '3356757484', '05-01-Gym', '6001', '04-01-Gym', '32272591121', '532159', '2709', '2703', '67996441132', '271966303', '2207', '39251872', '96876009', '2613', '2517', '72995111', '2711', '3353-01', '1E+14', '4542752846', '699111584', '81861183', '2410', '03-01-Gym', '167781', '8465436302', '1851302', '06-01-Gym', '15789441129', '2626', '1186631186', '39172891128', '35216455739', '2.16583E+11', '2403', '2110', '2402', '35869581122', '42656615745', '3464-04', '2130', '02-01-GYM', '08-01-GYM', '04-01-GYM', '2701', '1E+13', '2100', '8_Y_804_8', '4335272', '2102', '2105', '3.92512E+11', '9.99858E+11']
        corr_districtname_list = ['San Diego Unified', 'Lafayette Elementary', 'San Francisco Unified']

        if len(corr_districtname_list) > 0:
            corr_district = corr_districtname_list
        else:
            corr_district = user.DistrictName
        if len(corr_schoolname_list) > 0:
            corr_school = corr_schoolname_list
        else:
            corr_school = user.SchoolName
        if len(corr_classid_list) > 0:
            corr_class = corr_classid_list
        else:
            corr_class = user.ClassID
        correlated_attributes = {"User_DistrictName": corr_district, "User_SchoolName": corr_school, "User_ClassID": corr_class, "Resource_DistrictName": file.DistrictName, "Resource_SchoolName": file.SchoolName, "Resource_ClassID": file.ClassID}  # Your logic to generate correlated attributes
        # Example call to association analysis model
        # correlated_attributes = association_model.get_correlated_attributes(user, file)
        return correlated_attributes if correlated_attributes else None

    def update_policy_with_correlated_attributes(self, user, file, correlated_attributes):
        try:
            # Create a new policy or update the existing one with correlated attributes
            policy_id = f"policy_{self.policy_counter}"
            #self.policy_counter += 1

            self.highest_counter
            
            # Example: Updating policy rules with correlated attributes
            policy_data = {
                "uid": policy_id,
                "description": "Dynamic policy with correlated attributes",
                "effect": "allow",
                "rules": {
                    "subject": {
                        "$.districtname": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('User_DistrictName')
                        },
                        "$.schoolname": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('User_SchoolName')
                        },
                        "$.classid": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('User_ClassID')
                        },
                    },
                    "resource": {
                        "$.districtname": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('Resource_DistrictName')
                        },
                        "$.schoolname": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('Resource_SchoolName')
                        },
                        "$.classid": {
                            "condition": "Equals",
                            "value": correlated_attributes.get('Resource_ClassID')
                        },
                    },
                    "action": {
                        "$.method": {
                            "condition": "Equals",
                            "value": "view"
                        }
                    }
                },
                "targets": {},
                "priority": 0
            }
            
            # Store policy in DB and memory
            #abac_policy = AbacPolicy.from_json(policy_data)
            #self.storage.add(abac_policy)
            
            # Also store in your database for persistence
            from app_factory import db
            from policy_model import Policy
            policy_db = Policy(
                description=policy_data["description"],
                effect=policy_data["effect"],
                rules=json.dumps(policy_data["rules"]),
                targets=json.dumps(policy_data["targets"]),
                priority=policy_data["priority"]
            )
            db.session.add(policy_db)
            db.session.commit()
            print("Policy with correlated attributes successfully added.")

        except Exception as e:
            print(f"Error updating policy with correlated attributes: {e}")

    def update_policy(self, policy_id, new_policy_data):
        policy = self.storage.get(policy_id)
        if not policy:
            raise ValueError("Policy not found")

        policy.description = new_policy_data.get('description', policy.description)
        policy.effect = new_policy_data.get('effect', policy.effect)
        policy.rules = new_policy_data.get('rules', policy.rules)
        policy.targets = new_policy_data.get('targets', policy.targets)
        policy.priority = new_policy_data.get('priority', policy.priority)

        self.storage.update(policy)

    def track_access(self, access_data):
        # Implement your tracking logic here
        pass
