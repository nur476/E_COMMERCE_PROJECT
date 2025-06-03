from . import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    favorites = db.relationship('UserFavorites', back_populates='user', lazy='dynamic')
class Product(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), nullable=False)
   urun_etiket = db.Column(db.String(100), nullable=False, unique=True)
   price = db.Column(db.Float, nullable=False)
   image_url = db.Column(db.String(200), nullable=False)
   kategori=db.Column(db.String(200), nullable=True)
   description = db.Column(db.String(300), nullable=True)  
   yas=db.Column(db.Integer,nullable=True)
   cinsiyet=db.Column(db.String(100),nullable=True)
   miktar=db.Column(db.Integer,nullable=True)
   renk=db.Column(db.String(100),nullable=True)
   favorited_by = db.relationship('UserFavorites', back_populates='product', lazy='dynamic')


class Siparis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    toplam_fiyat = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref=db.backref('siparisler', lazy=True))
    durum = db.Column(db.String(100), nullable=True, default="Hazırlanıyor")
    kargo_takip_no = db.Column(db.String(100), nullable=True)
    iptal_edildi = db.Column(db.Boolean, default=False)

    
class SiparisUrun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    siparis_id = db.Column(db.Integer, db.ForeignKey('siparis.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    adet = db.Column(db.Integer, nullable=False)
    siparis = db.relationship('Siparis', backref=db.backref('urunler', lazy=True))
    product = db.relationship('Product', backref=db.backref('siparis_urunler', lazy=True))

class UserFavorites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    user = db.relationship('User', back_populates='favorites')
    product = db.relationship('Product', back_populates='favorited_by')
                      