from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Product, UserFavorites, Siparis, SiparisUrun
import random
from sqlalchemy import func
from flask import request, session
from flask_login import current_user
import re
import os
from flask_login import login_user, login_required, logout_user
from flask import jsonify, session
auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))
    session['user_id'] = user.id 
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    if not email or not name or not password:
        flash('Lütfen tüm alanları doldurduğunuzdan emin olun!')
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Bu mail adresine kayıtlı kullanıcı zaten mevcut!')
        return redirect(url_for('auth.signup'))
    """
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
        flash('Şifreniz en az 8 karakter, bir büyük harf ve bir rakam içermelidir!')
        return redirect(url_for('auth.signup'))
    """
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'))
    db.session.add(new_user)
    db.session.commit()

    flash('Kayıt Başarılı :) ')
    return redirect(url_for('auth.login'))

@auth.route('/urun_ekle', methods=['GET', 'POST'])
def urun_ekle():
    if request.method == 'POST':
        urun_ad = request.form.get('urun_ad')
        urun_etiket = request.form.get('urun_etiket')
        urun_fiyat = request.form.get('urun_fiyat')
        urun_img = request.form.get('urun_img')
        urun_tur = request.form.get('urun_tur')

        if not urun_ad:
            flash('Ürün adı giriniz.', 'danger')
            return redirect(url_for('auth.urun_ekle'))
        if not urun_etiket:
            flash('Ürün etiketini giriniz.', 'danger')
            return redirect(url_for('auth.urun_ekle'))
        if not urun_fiyat:
            flash('Ürün fiyatını giriniz.', 'danger')
            return redirect(url_for('auth.urun_ekle'))
        if not urun_tur:
            flash('Ürün türünü giriniz.', 'danger')
            return redirect(url_for('auth.urun_ekle'))
        if not urun_img:
            flash('Ürüne ait URL giriniz.', 'danger')
            return redirect(url_for('auth.urun_ekle'))

        try:
            urun_img_yolu = f"/static/images/{urun_img}"
            yeni_urun = Product(
                name=urun_ad,
                urun_etiket=urun_etiket,
                price=float(urun_fiyat), 
                image_url=urun_img_yolu,
                description=urun_tur
            )
            db.session.add(yeni_urun)
            db.session.commit()
            flash('Ürün başarıyla eklendi.', 'success')
            return redirect(url_for('auth.urun_ekle'))
        except Exception as e:
            flash(f'Bir hata oluştu: {e}', 'danger')
            return redirect(url_for('auth.urun_ekle'))

    return render_template('urun_ekle.html')

@auth.route('/urunler')
def urunler():
    cinsiyet = request.args.get('cinsiyet')
    kategori = request.args.get('kategori')
    data = ""
    query = Product.query
    if cinsiyet and kategori:
        products = query.filter_by(cinsiyet=cinsiyet, kategori=kategori).all()
        product_count = query.filter_by(cinsiyet=cinsiyet, kategori=kategori).count()
        data = f"{cinsiyet} Bebek {kategori}"
    elif cinsiyet:
        products = query.filter_by(cinsiyet=cinsiyet).all()
        product_count = query.filter_by(cinsiyet=cinsiyet).count()
        data = cinsiyet
    elif kategori:
        products = query.filter_by(kategori=kategori).all()
        product_count = query.filter_by(kategori=kategori).count()
        data = kategori
    else:
        products = query.order_by(func.random()).all()
        product_count = len(products)

    random_products = Product.query.order_by(func.random()).limit(5).all()

    return render_template(
        'urunler.html',
        products=products,
        random_products=random_products,
        product_count=product_count,
        data=data
    )

#bu kısım profilim sayfasındaki siparişlerim için
@auth.route('/api/orders')
def api_orders():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    # Aktif kullanıcının siparişlerini çek
    siparisler = Siparis.query.filter_by(kullanici_id=user_id, iptal_edildi=False).order_by(Siparis.tarih.desc()).all()

    siparisler_data = []
    for siparis in siparisler:
        # Sipariş ürünlerini de çekelim
        urunler = []
        for su in siparis.urunler:
            urunler.append({
                'product_id': su.product.id,
                'name': su.product.name,
                'adet': su.adet,
                'price': su.product.price,
                'image_url': su.product.image_url
            })
        
        siparisler_data.append({
            'id': siparis.id,
            'tarih': siparis.tarih.strftime('%d %B %Y %H:%M'),
            'toplam_fiyat': siparis.toplam_fiyat,
            'durum': siparis.durum,
            'kargo_takip_no': siparis.kargo_takip_no,
            'urunler': urunler
        })

    return jsonify(siparisler_data)


@auth.route('/sepet', methods=['GET', 'POST'])
def sepet():
    if 'sepet' not in session:
        session['sepet'] = []

    if request.method == 'POST':
        product = request.get_json()
        if product:
            product['adet'] = 1
            session['sepet'].append(product)
            session.modified = True
            return jsonify({'message': 'Ürün sepete eklendi!'}), 200
        else:
            return jsonify({'message': 'Geçersiz veri!'}), 400

    sepet_toplam = sum(
        float(item.get('price', 0)) * item.get('adet', 1) for item in session['sepet']
    )

    return render_template(
        'sepet.html', sepet=session.get('sepet', []), sepet_toplam=sepet_toplam
    )

@auth.route('/sepet/sil', methods=['POST'])
def sepetten_kaldir():
    product = request.get_json()
    if not product or 'name' not in product:
        return jsonify({'message': 'Geçersiz veri!'}), 400

    product_name = product['name']
    if 'sepet' in session:
        session['sepet'] = [item for item in session['sepet'] if item['name'] != product_name]
        session.modified = True
        return jsonify({'message': 'Ürün sepetten kaldırıldı!'}), 200

    return jsonify({'message': 'Sepet bulunamadı!'}), 404

@auth.route('/sepet/update_quantity', methods=['POST'])
def update_quantity():
    if 'sepet' not in session:
        return jsonify({'success': False, 'message': 'Sepet boş!'}), 400

    data = request.get_json()
    if not data or 'name' not in data or 'change' not in data:
        return jsonify({'success': False, 'message': 'Geçersiz veri!'}), 400

    product_name = data['name']
    change = data['change']

    for item in session['sepet']:
        if item['name'] == product_name:
            item['adet'] = max(1, item.get('adet', 1) + change)
            session.modified = True

            sepet_toplam = sum(
                float(it.get('price', 0)) * it.get('adet', 1) for it in session['sepet']
            )
            return jsonify({'success': True, 'sepet_toplam': sepet_toplam}), 200

    return jsonify({'success': False, 'message': 'Ürün bulunamadı!'}), 404





@auth.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    data = request.get_json()
    product_id = data.get('product_id')
    # Favori var mı kontrol et
    fav = UserFavorites.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        new_fav = UserFavorites(user_id=current_user.id, product_id=product_id)
        db.session.add(new_fav)
        db.session.commit()
        return jsonify({'status': 'added'})
    





    



@auth.route('/sepet/onayla', methods=['POST'])
def sepet_onayla():
    if 'sepet' not in session or not session['sepet']:
        return jsonify({'success': False, 'message': 'Sepet boş!'}), 400
    try:
        sepet_toplam = sum(float(item['price']) * item.get('adet', 1) for item in session['sepet'])
        yeni_siparis = Siparis(
            kullanici_id=current_user.id,
            toplam_fiyat=sepet_toplam
        )
        db.session.add(yeni_siparis)
        db.session.flush()

        for item in session['sepet']:
            product = Product.query.filter_by(name=item['name']).first()
            if not product:
                return jsonify({'success': False, 'message': f"Ürün bulunamadı: {item['name']}"}), 404

            siparis_urun = SiparisUrun(
                siparis_id=yeni_siparis.id,
                product_id=product.id,
                adet=item.get('adet', 1)
            )
            db.session.add(siparis_urun)
        db.session.commit()

        session.pop('sepet', None)

        return jsonify({'success': True, 'message': 'Sipariş başarıyla oluşturuldu!'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
