from flask import Flask, redirect, url_for, render_template, request, flash, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os
import logging
import requests
from flask_login import current_user
import openai
from openai import OpenAI
from dotenv import load_dotenv

import pickle
import os


#  /\_/\
# ( o.o )
#  > ^ <


logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
db = SQLAlchemy()
migrate = Migrate()

from .models import User, db, Product,SiparisUrun,Siparis  

SECRET_KEY = os.urandom(24)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Bu alana erişmek için admin yetkisine sahip olmalısınız.', 'error')
        return redirect(url_for('auth.login'))

from flask_admin import Admin, AdminIndexView, expose

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

class UserAdmin(ModelView):
    column_list = ('id', 'name', 'email', 'password')
    column_labels = {
        'id': 'ID',
        'name': 'Adı',
        'email': 'E-mail',
        'password': 'Şifre'
    }
    column_filters = ('name', 'email')

class ProductAdmin(ModelView):
    column_list = ('id', 'name', 'price', 'image_url', 'kategori', 'description', 'yas', 'cinsiyet', 'miktar', 'renk')
    form_columns = ('name', 'price', 'image_url', 'kategori', 'description', 'yas', 'cinsiyet', 'miktar', 'renk')  

    column_labels = {
        'id': 'ID',
        'name': 'Ürün Adı',
        'price': 'Fiyat',
        'image_url': 'Resim URL',
        'kategori': 'Kategori',
        'description': 'Açıklama',
        'yas': 'Yaş',
        'cinsiyet': 'Cinsiyet',
        'miktar': 'Miktar',
        'renk': 'Renk'
    }

    column_filters = ('name', 'price', 'miktar', 'kategori')
#durum = db.Column(db.String(100), nullable=True, default="Hazırlanıyor")
    #kargo_takip_no = db.Column(db.String(100), nullable=True)
   # iptal_edildi = db.Column(db.Boolean, default=True)

class SiparisAdmin(ModelView):
    column_list = ('id', 'kullanici_id', 'user.name', 'tarih', 'toplam_fiyat','durum','kargo_takip_no','iptal_edildi')
    form_columns = ('kullanici_id', 'tarih', 'toplam_fiyat','durum')

    column_labels = {
        'id': 'ID',
        'kullanici_id': 'Kullanıcı ID',
        'user.name': 'Kullanıcı Adı',  
        'tarih': 'Sipariş Tarihi',
        'toplam_fiyat': 'Toplam Fiyat',
        'durum':'Durum',
        'kargo_takip_no':'Kargo Takip No',
        'iptal_edildi':'İptal'
    }

    column_filters = ('tarih', 'toplam_fiyat', 'kullanici_id','durum')


class SiparisUrunAdmin(ModelView):
    column_list = ('id', 'siparis_id', 'product_id', 'adet', 'product.name', 'product.price')
    form_columns = ('siparis_id', 'product_id', 'adet')
    column_labels = {
        'id': 'ID',
        'siparis_id': 'Sipariş ID',
        'product_id': 'Ürün ID',
        'adet': 'Adet',
        'product.name': 'Ürün Adı',
        'product.price': 'Fiyat'
    }
    column_filters = ('siparis_id', 'product_id', 'adet')


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tavsan'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:duven_password@localhost/Duven'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

   
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  


    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)


    admin = Admin(app, name='Admin Paneli', template_mode='bootstrap4', index_view=MyAdminIndexView())
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(ProductAdmin(Product, db.session))
    admin.add_view(SiparisAdmin(Siparis, db.session))
    admin.add_view(SiparisUrunAdmin(SiparisUrun ,db.session))



    OLLAMA_URL = "http://localhost:11434/api/generate"
    VALID_DURUMLAR = ["Hazırlanıyor", "Kargoya Verildi", "Teslim Edildi", "İptal edildi"]


    class SiparisYonetimi:
        @staticmethod
        def durum_guncelle(siparis_id, yeni_durum):
            if yeni_durum not in VALID_DURUMLAR:
                return "Geçersiz durum değeri.", 400

            siparis = Siparis.query.get_or_404(siparis_id)
            siparis.durum = yeni_durum
            db.session.commit()
            return redirect(url_for("admin_siparis_paneli"))

        @staticmethod
        def takip_no_guncelle(siparis_id, takip_no):
            siparis = Siparis.query.get_or_404(siparis_id)
            siparis.kargo_takip_no = takip_no
            db.session.commit()
            return redirect(url_for("admin_siparis_paneli"))

        @staticmethod
        def iptal_et(siparis_id, kullanici_id):
            siparis = Siparis.query.get(siparis_id)
            if not siparis or siparis.kullanici_id != kullanici_id:
                return "Sipariş bulunamadı."
            if siparis.durum != "Hazırlanıyor":
                return f"Bu siparişi iptal edemezsiniz. Çünkü durumu: {siparis.durum}"

            siparis.durum = "İptal edildi"
            siparis.iptal_edildi = True
            db.session.commit()
            return f"📦 Sipariş No {siparis.id} başarıyla iptal edildi."

        @staticmethod
        def get_siparis_durumlari(kullanici_id):
            siparisler = Siparis.query.filter_by(kullanici_id=kullanici_id).order_by(Siparis.tarih.desc()).all()
            if not siparisler:
                return "🛒 Henüz hiç sipariş vermemişsiniz."

            cevaplar = []
            print("siparişler")
            for s in siparisler:
                cevaplar.append(
                    f"""🧾 Sipariş Bilgisi:
                        • Sipariş No: {s.id}
                        • Tarih: {s.tarih.strftime('%d.%m.%Y')}
                        • Durum: {s.durum}
                        • Tutar: {s.toplam_fiyat:.2f} TL"""
                             )
            print(cevaplar)      
            return "\n\n".join(cevaplar)

        @staticmethod
        def get_kargo_takip_bilgisi(kullanici_id):
            siparisler = Siparis.query.filter_by(kullanici_id=kullanici_id).all()
            cevaplar = [
                f"📦 Sipariş No: {s.id} | Kargo Takip No: {s.kargo_takip_no} | Durum: {s.durum}"
                for s in siparisler if s.kargo_takip_no
            ]
            return "\n".join(cevaplar) if cevaplar else "Kargo takip numarası bulunan bir siparişiniz bulunmamaktadır."


    class UrunYonetimi:
        @staticmethod
        def urun_bilgilerini_getir():
            urunler = Product.query.all()
            urun_ozellik = []

            for p in urunler:
                ozellik = f"- {p.name} ({p.price} TL): {p.description or 'Açıklama yok'}"
                if p.renk:
                    ozellik += f", Renk: {p.renk}"
                if p.yas:
                    ozellik += f", Yaş: {p.yas}+"
                if p.cinsiyet:
                    ozellik += f", Cinsiyet: {p.cinsiyet}"
                if p.kategori:
                    ozellik += f", Kategori: {p.kategori}"
                urun_ozellik.append(ozellik)

            return "\n".join(urun_ozellik)


    class Asistan:
        model_path = os.path.join("project", "intent_model.pkl")
        try:
            with open(model_path, "rb") as f:
                vectorizer, model = pickle.load(f)
        except Exception as e:
            print("Model yüklenemedi:", e)
            vectorizer, model = None, None

            @staticmethod
            def tahmin_et(user_message):
                if not Asistan.vectorizer or not Asistan.model:
                    return "bilinmiyor"
                try:
                    X = Asistan.vectorizer.transform([user_message])
                    intent = Asistan.model.predict(X)[0]
                    return intent
                except Exception as e:
                    print("Intent sınıflandırma hatası:", str(e))
                    return "bilinmiyor"
        @staticmethod
        def create_prompt(user_message):
            urun_bilgisi = UrunYonetimi.urun_bilgilerini_getir()
            siparis_durumlari = SiparisYonetimi.get_siparis_durumlari(current_user.id)
            kargo_bilgisi = SiparisYonetimi.get_kargo_takip_bilgisi(current_user.id)

            return f"""
    Sen bir e-ticaret asistanısın. 
    Aşağıdaki ürün bilgilerine göre kullanıcılara yardımcı ol.
    Yanıtlarını Türkçe ver. Net, kısa ve açıklayıcı ol.
    📦 Sipariş Durumları:
    {siparis_durumlari}
    🚚 Kargo Takip Bilgileri:
    {kargo_bilgisi}
    🛍️ Ürünler:
    {urun_bilgisi}
    Kullanıcı: {user_message}
    Asistan:
    """

        @staticmethod
        def ollama_chat(prompt):
            payload = {
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
            try:
                response = requests.post(OLLAMA_URL, json=payload)
                return response.json().get("response", "").strip()
            except Exception as e:
                return f"🤖 Asistan hata verdi: {str(e)}"

        
        @staticmethod
        def yorumla_ve_cevapla(user_message):
            if not current_user.is_authenticated:
                return "Lütfen giriş yapınız."

            mesaj = user_message.lower()
            
            tesekkur_kelimeleri = ["teşekkürler", "teşekkür ederim", "sağol", "sağolun", "çok teşekkürler"]

            if any(tk in mesaj for tk in tesekkur_kelimeleri):
                return "Rica ederim! Her zaman yardımcı olmaktan mutluluk duyarım. 😊"

            intent = Asistan.tahmin_et(user_message)

            if intent == "siparis_iptal":
                siparis = Siparis.query.filter_by(kullanici_id=current_user.id).order_by(Siparis.tarih.desc()).first()
                if siparis:
                    return SiparisYonetimi.iptal_et(siparis.id, current_user.id)
                else:
                    return "İptal edilecek sipariş bulunamadı."

            elif intent == "kargo_takip":
                return SiparisYonetimi.get_kargo_takip_bilgisi(current_user.id)

            elif intent == "siparis_durumu":
                return SiparisYonetimi.get_siparis_durumlari(current_user.id)

            elif intent == "urun_bilgisi":
                urun_bilgisi = UrunYonetimi.urun_bilgilerini_getir()
                return f"İşte ürünlerimiz hakkında bilgi:\n\n{urun_bilgisi}"

            elif mesaj.strip() in ["merhaba", "selam", "sa", "hello", "hi"]:
                return "Merhaba! Size nasıl yardımcı olabilirim? Lütfen yapmak istediğiniz işlemi seçiniz."

            else:
                prompt = Asistan.create_prompt(user_message)
                cevap = Asistan.ollama_chat(prompt)
                if not cevap.strip():
                    return "Lütfen yapmak istediğiniz işlemi seçiniz veya 'yardım' yazınız."
                return cevap




    @app.route("/siparis/<int:id>/durum", methods=["POST"])
    def siparis_durum_guncelle(id):
        yeni_durum = request.form.get("durum")
        return SiparisYonetimi.durum_guncelle(id, yeni_durum)


    @app.route('/admin/siparis/<int:id>/takip', methods=['POST'])
    def takip_no_guncelle(id):
        takip_no = request.form['takip_no']
        return SiparisYonetimi.takip_no_guncelle(id, takip_no)


    @app.route('/asistan', methods=['POST'])
    def asistn():
        print("asistan içi")
        message = request.json.get("message")
        print(message)
        if not message:
            print("mesaj yok")
            return jsonify({"error": "Mesaj eksik."}), 400

        cevap = Asistan.yorumla_ve_cevapla(message)
        print(cevap)
        return jsonify({"response": cevap})




                    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
