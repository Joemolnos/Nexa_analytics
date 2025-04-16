import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from functools import wraps
from utils.analyzer import analyze_video
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['DELETE_VIDEOS_AFTER_ANALYSIS'] = True  # Beállítás a videók törléséhez elemzés után

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Statikus bejelentkezési adatok (ezeket a csapat adja majd át)
VALID_CREDENTIALS = {
    'username': os.environ.get('APP_USERNAME', 'tris'),
    'password': os.environ.get('APP_PASSWORD', 'tris123')
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"Session debug: {session}")  # Debug info
        # Teszt mód a fejlesztéshez - Ha TRUE, akkor minden authentikáció átmegy
        test_mode = True
        
        if 'logged_in' not in session and not test_mode:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # Főoldal, ami a login oldalra irányít, ha nincs bejelentkezve
    print(f"Index route - Session tartalom: {session}")  # Debug info
    if 'logged_in' in session:
        return redirect(url_for('upload_page'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Debug információ a session állapotáról
    print(f"Login route - Session tartalom a kérés elején: {session}")
    
    # Ha már be van jelentkezve, átirányítjuk a feltöltés oldalra
    if 'logged_in' in session:
        print("Felhasználó már be van jelentkezve, átirányítás...")
        return redirect(url_for('upload_page'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Bejelentkezési kísérlet: {username} / {password}")
        print(f"Elvárt: {VALID_CREDENTIALS['username']} / {VALID_CREDENTIALS['password']}")
        
        if username == VALID_CREDENTIALS['username'] and password == VALID_CREDENTIALS['password']:
            session['logged_in'] = True
            print(f"Sikeres bejelentkezés! Session beállítva: {session}")
            flash('Sikeres bejelentkezés!', 'success')
            return redirect(url_for('upload_page'))
        else:
            print("Hibás bejelentkezési adatok!")
            flash('Hibás felhasználónév vagy jelszó!', 'danger')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Sikeres kijelentkezés!', 'success')
    return redirect(url_for('login'))

@app.route('/upload')
@login_required
def upload_page():
    # Debug információ a session állapotáról
    print(f"Upload page - Session tartalom: {session}")
    # A videófeltöltési oldal megjelenítése
    return render_template('upload.html')

@app.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No video selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Start analysis (this will be handled asynchronously in a real app)
        try:
            result = analyze_video(filepath)
            result_file = os.path.splitext(filename)[0] + '_analysis.json'
            result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
            
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Töröljük a videófájlt az elemzés után, ha a beállítás engedélyezi
            if app.config['DELETE_VIDEOS_AFTER_ANALYSIS'] and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Videófájl törölve: {filepath}")
                except Exception as e:
                    print(f"Hiba a videófájl törlésekor: {e}")
                
            return jsonify({
                'success': True, 
                'message': 'Analysis complete',
                'result_file': result_file
            })
        except Exception as e:
            error_str = str(e)
            # Check if it's a 503 UNAVAILABLE error from the Gemini API
            if "503 UNAVAILABLE" in error_str and "overloaded" in error_str:
                return jsonify({
                    'success': False,
                    'error': 'Terhelt a szerver, kérlek próbáld elemezni újra: kattints a "Feltöltés és elemzés" gombra!'
                }), 503
            else:
                # Log the full error for debugging
                print(f"Error during video analysis: {error_str}")
                
                # Töröljük a videófájlt hiba esetén is, hogy ne foglalja a helyet
                if app.config['DELETE_VIDEOS_AFTER_ANALYSIS'] and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        print(f"Videófájl törölve hiba után: {filepath}")
                    except Exception as delete_error:
                        print(f"Hiba a videófájl törlésekor: {delete_error}")
                
                return jsonify({'success': False, 'error': error_str}), 500
    
    return jsonify({'success': False, 'error': 'Something went wrong'}), 500

@app.route('/dashboard/<result_file>')
@login_required
def dashboard(result_file):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
    
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # Ha a response mező egy string, akkor azt is parse-oljuk
        if 'response' in analysis_data and isinstance(analysis_data['response'], str):
            try:
                response_data = json.loads(analysis_data['response'])
                analysis_data = response_data  # Használjuk a response-ban lévő adatokat
            except Exception as parse_error:
                app.logger.error(f"Error parsing response JSON: {str(parse_error)}")
        
        # Check if the analysis data has the expected structure
        if 'video_elemzes' not in analysis_data:
            # Create a default structure if key is missing
            analysis_data = {
                "video_elemzes": {
                    "metadata": {
                        "video_hossz": "Unknown",
                        "intervallumok_szama": 0
                    },
                    "intervallumok": [],
                    "osszesites": {
                        "atlagok": {
                            "pszichometria": {},
                            "vizualis_stimulacio": {},
                            "hang_stimulacio": {},
                            "public_speech": {},
                            "kognitiv_tenyezok": {}
                        },
                        "fo_javaslatok": ["Nincs elérhető javaslat"]
                    }
                },
                "raw_response": analysis_data
            }

        # Pass the current year to the template for the footer
        current_year = datetime.now().year
        return render_template('dashboard.html', analysis=analysis_data, current_year=current_year)
    except Exception as e:
        error_message = f"Error loading analysis: {str(e)}"
        app.logger.error(error_message)
        return render_template('error.html', error=error_message)

@app.route('/api/results/<result_file>')
@login_required
def get_results(result_file):
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_file)
    
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        return jsonify(analysis_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Segédfunkció a temp fájlok időszakos törlésére
def cleanup_old_files():
    """Törölje a régi feltöltött fájlokat és elemzési eredményeket"""
    now = datetime.now()
    threshold = 7  # napok száma, amennyinél régebbi fájlokat töröljünk
    
    upload_dir = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(upload_dir):
        filepath = os.path.join(upload_dir, filename)
        try:
            # Ellenőrizzük a fájl korát
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            age_days = (now - file_mtime).days
            
            # Ha régi JSON fájl vagy bármilyen más fájl (pl. videó), ami ottmaradt
            if age_days > threshold:
                os.remove(filepath)
                print(f"Régi fájl törölve: {filepath} (kor: {age_days} nap)")
        except Exception as e:
            print(f"Hiba a fájl törlésénél: {filepath}, {str(e)}")

# Vercel serverless function handler
def handler(event, context):
    return app

if __name__ == '__main__':
    # Induláskor futtassuk a takarítást
    cleanup_old_files()
    
    # Vercel környezetben a port környezeti változóból jön
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
