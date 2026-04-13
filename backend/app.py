import os
import sys

# Add project root to path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from flask_cors import CORS
from backend.config import Config
from backend.utils.db import close_db


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static')
    )
    app.config.from_object(Config)
    CORS(app)

    # Close DB connection at end of each request
    app.teardown_appcontext(close_db)

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.carbon import carbon_bp
    from backend.routes.waste import waste_bp
    from backend.routes.report import report_bp
    from backend.routes.alert import alert_bp
    from backend.routes.ocr import ocr_bp
    from backend.routes.audit import audit_bp
    from backend.routes.admin import admin_bp
    from backend.routes.anomaly import anomaly_bp
    from backend.routes.training import training_bp
    from backend.routes.compliance import compliance_bp
    from backend.routes.supplier import supplier_bp
    from backend.routes.policy import policy_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(carbon_bp)
    app.register_blueprint(waste_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(ocr_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(anomaly_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(policy_bp)

    # Init Flask-Mail (falls back to mock if MAIL_SERVER not set)
    from backend.utils.mail import init_mail
    init_mail(app)

    # Root redirect
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login_page'))

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
