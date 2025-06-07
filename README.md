# Yapay Zeka Destekli Bebek Giyim E-Ticaret Sitesi

Bu proje, bebek giyim ürünleri satan bir e-ticaret sitesine yapay zeka destekli bir chatbot entegre etmeyi amaçlamaktadır. Chatbot, kullanıcıların sipariş durumu, ürün bilgisi ve sipariş iptali gibi sorularına hızlı ve doğru yanıtlar vermek için geliştirilmiştir.

## Özellikler

- Ürün listeleme, sepet ve sipariş yönetimi
- Kullanıcı kayıt ve giriş sistemi
- Flask-Admin ile yönetim paneli
- PostgreSQL veritabanı kullanımı
- Yapay zeka destekli chatbot (Meta-LLaMA-3-8B-Instruct)
- Chatbot ile sipariş durumu sorgulama, ürün bilgisi alma, sipariş iptali gibi işlemler

## Kullanılan Teknolojiler

- Python (Flask)
- Flask-Login (kullanıcı yönetimi)
- Flask-Admin (yönetici paneli)
- Flask-SQLAlchemy (ORM)
- Flask-Migrate (veritabanı göçleri)
- PostgreSQL (veritabanı)
- Ollama + Meta-LLaMA-3-8B-Instruct (chatbot)
- scikit-learn (TfidfVectorizer, Logistic Regression)
- dotenv, json, pickle, requests (yardımcı kütüphaneler)

## Chatbot Özellikleri

Chatbot, Ollama platformunda çalışan Meta-LLaMA-3-8B-Instruct modeli ile desteklenmektedir. Model yerel olarak çalışır ve internet bağlantısı gerekmeden hizmet verebilir. Kullanıcıdan gelen mesajlar önce kural tabanlı yöntemle, daha sonra makine öğrenmesi (Logistic Regression) ile işlenerek anlamlı yanıtlar üretilir.


