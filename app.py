from flask import Flask, Response
import os
from routes.pages import bp as pages_bp
from routes.weather import bp as weather_bp
from routes.soil import bp as soil_bp
from routes.recommend import bp as recommend_bp
from routes.calendar import bp as calendar_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.register_blueprint(pages_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(soil_bp)
    app.register_blueprint(recommend_bp)
    app.register_blueprint(calendar_bp)
    @app.route('/favicon.ico')
    def favicon():
        p = os.path.join(app.static_folder, 'favicon.svg')
        with open(p, 'rb') as f:
            return Response(f.read(), mimetype='image/svg+xml')
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
