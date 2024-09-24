from flask import request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app_factory import db, login_manager
from user_model import User
from file_model import File
from policy_manager import PolicyManager
from sqlalchemy.exc import IntegrityError

policy_manager = PolicyManager()

def register_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            DistrictName = request.form['DistrictName']
            SchoolName = request.form['SchoolName']
            ClassID = request.form['ClassID']
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password, DistrictName = DistrictName, SchoolName = SchoolName, ClassID = ClassID)

            try:
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))

            # Catch the IntegrityError if the username already exists
            except IntegrityError:
                db.session.rollback()  # Rollback the transaction in case of error
                flash('Username already exists. Please choose a different username.')
                return redirect(url_for('register'))
            
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('file_list'))
            flash('Invalid credentials')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/files')
    @login_required
    def file_list():
        files = File.query.all()  # In a real app, filter based on user access
        return render_template('file_list.html', files=files)

    @app.route('/view_file/<int:file_id>')
    @login_required
    def view_file(file_id):
        file = File.query.get_or_404(file_id)

        # Check if a policy exists, if not, generate one
        """policy_id = f"policy_{current_user.id}_{file.id}"
        try:
            if not policy_manager.storage.get(policy_id):
                print("Policy does not exist, generating policy...")
                # Check if the policy generation succeeds
                policy_generated = policy_manager.generate_policy(current_user, file)
                if policy_generated:
                    print("Policy generated successfully!")
                else:
                    print("Policy generation has failed!")
                    return "Policy generation has failed", 500
        except Exception as e:
            # Log the actual error message
            print(f"Error during policy creation: {e}")
            return f"Error in policy creation: {e}", 500"""

        # Evaluate the request
        try:
            if policy_manager.evaluate_request(current_user, file):
                print("Access granted")
                return render_template('view_file.html', file=file)
            else:
                print("Access Denied")
                return "Access Denied", 403
        except Exception as e:
            print(f"Error evaluating access request: {e}")
            return f"Error in access evaluation: {e}", 500

    @app.route('/add_policy', methods=['POST'])
    def add_policy():
        policy_data = request.json
        try:
            policy_manager.add_policy(policy_data)
            return jsonify({"status": "Policy added successfully!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/evaluate', methods=['POST'])
    def evaluate_request():
        access_request = request.json
        try:
            result = policy_manager.evaluate_request(access_request)
            return jsonify({"allowed": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/track_access', methods=['POST'])
    def track_access():
        access_data = request.json
        try:
            tracking_info = policy_manager.track_access(access_data)
            return jsonify(tracking_info), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/')
    def index():
        return render_template('home.html')

