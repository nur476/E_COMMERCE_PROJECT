from flask import Blueprint,render_template
from.import db

from flask_login import login_required, current_user



from .models import Product
 
main = Blueprint('main',__name__)

@main.route('/')
def index():
    return  render_template('index.html')

@main.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)