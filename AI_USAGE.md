\# Food Lens — AI Usage



\## 1. AI Kullanım Amacı



Food Lens geliştirilirken AI araçları geliştirme sürecini hızlandırmak, teknik konuları açıklamak, hata ayıklamak ve alternatif tasarım yaklaşımlarını değerlendirmek amacıyla kullanılmıştır.



AI, projenin tamamını bağımsız olarak geliştiren bir sistem olarak değil, geliştiriciye yardımcı olan bir araç olarak kullanılmıştır.



Son kararlar, kodun çalıştırılması ve test sonuçlarının değerlendirilmesi geliştirici tarafından yapılmıştır.



\## 2. Kullanılan AI Araçları



Projede temel olarak:



\- ChatGPT

\- Claude

\- Google Gemini API



kullanılmıştır.



\### ChatGPT



ChatGPT aşağıdaki konularda kullanılmıştır:



\- Proje mimarisinin planlanması

\- Python kodlarının açıklanması

\- Hata mesajlarının analiz edilmesi

\- Gemini API entegrasyonu

\- Pydantic veri modellerinin tasarlanması

\- Nutrition matching mantığının geliştirilmesi

\- Evaluation scriptinin oluşturulması

\- README ve teknik dokümantasyonun hazırlanması

\- Test sonuçlarının yorumlanması



\### Claude



Claude özellikle kod geliştirme ve refactoring aşamalarında yardımcı araç olarak kullanılmıştır.



Kullanım alanları:



\- Kod yapısının iyileştirilmesi

\- Fonksiyonların ayrıştırılması

\- Hata yönetimi

\- Dokümantasyon önerileri

\- Proje yapısının gözden geçirilmesi



\### Gemini



Gemini, Food Lens'in asıl görüntü analiz bileşeni olarak kullanılmıştır.



Gemini'den beklenen görev:



```text

Fotoğraf → yiyecek adı + tahmini gramaj + confidence

```



Gemini'den nutrition değerleri istenmemiştir.



Kalori ve makro hesaplamaları uygulamanın kendi nutrition tablosundan yapılmıştır.



\## 3. AI Destekli Geliştirme Yaklaşımı



Geliştirme süreci küçük adımlara bölünmüştür.



Örneğin:



```text

1\. Gemini bağlantısını kur

2\. Görüntü gönder

3\. JSON çıktısı al

4\. Pydantic ile doğrula

5\. Nutrition tablosunu oluştur

6\. Food matching ekle

7\. Kalori hesapla

8\. UI'a bağla

9\. SQLite kaydı ekle

10\. Evaluation oluştur

```



Her aşamadan sonra kod çalıştırılarak çıktı kontrol edilmiştir.



Bu yaklaşım, AI tarafından önerilen kodun doğrudan doğru kabul edilmesini engellemiştir.



\## 4. Kullanılan Prompt Yaklaşımı



Vision modelinde yapılandırılmış çıktı istenmiştir.



Temel prompt yaklaşımı:



```text

Bu fotoğrafı analiz et.



Fotoğrafta görünen yiyecekleri tespit et.



Her yiyecek için:

\- name

\- grams

\- confidence



alanlarını döndür.



Yalnızca istenen JSON yapısını üret.

```



Amaç, model çıktısını uygulamanın Pydantic modellerine uygun hale getirmektir.



\## 5. AI ile Çözülen Teknik Problemler



\### Gemini JSON çıktısı



Modelin bazen boş veya beklenmeyen formatta cevap verebilmesi nedeniyle JSON validation ve retry mekanizması oluşturulmuştur.



\### Nutrition matching



Model tarafından döndürülen yemek isimleri ile nutrition tablosundaki isimler her zaman birebir aynı olmadığı için Türkçe-aware normalization ve candidate matching geliştirilmiştir.



Örneğin:



```text

Haşlanmış Yumurta

```



ve:



```text

Yumurta haşlanmış

```



aynı nutrition kaydına bağlanabilir.



\### Yanlış eşleşme problemi



İlk matching yaklaşımında zayıf kelimeler yanlış eşleşmelere neden olmuştur.



Örneğin:



```text

Kuru Nane

```



ifadesinin:



```text

Kuru Fasulye

```



ile eşleşme riski ortaya çıkmıştır.



Bu problemden sonra matching sistemi daha kontrollü hale getirilmiş ve belirsiz durumlarda kullanıcıya aday seçim imkanı verilmiştir.



\## 6. Evaluation Sürecinde AI Kullanımı



Evaluation seti 15 görüntüden oluşturulmuştur.



AI-assisted değerlendirme sürecinde:



\- Model tahminleri kaydedildi.

\- Ground-truth yemek etiketleri oluşturuldu.

\- Recognition rate hesaplandı.

\- Kalori error hesaplandı.

\- En yüksek hata veren örnekler incelendi.



Son evaluation:



```text

Recognition rate: 93.3% (14/15)

Calorie error: 130.8% (9 images)

```



Calorie error sonucunun yorumlanmasında özellikle modelin gramaj tahmininin etkisi dikkate alınmıştır.



Örneğin bütün fırın tavuk görüntüsünde model yaklaşık 1200 g tahmin etmiş, evaluation referansı yaklaşık 150 g yenebilir pişmiş tavuk porsiyonu olarak belirlenmiştir.



Bu nedenle calorie error değerinin önemli bir bölümü porsiyon/gramaj tahminindeki hatadan kaynaklanmaktadır.



\## 7. AI'nin Kullanılmadığı Bölümler



Nutrition hesaplama mantığı Gemini'ye bırakılmamıştır.



Aşağıdaki işlemler uygulamanın kendi kodu tarafından yapılır:



\- kcal hesaplama

\- protein hesaplama

\- karbonhidrat hesaplama

\- yağ hesaplama

\- nutrition tablosu matching

\- SQLite kayıtları

\- günlük toplamlar



Bu ayrım, modelin uydurma nutrition değerleri üretmesini önlemek için yapılmıştır.



\## 8. Human-in-the-loop



Model çıktısı kesin kabul edilmemiştir.



Kullanıcı:



\- yiyecek eşleşmesini

\- gramajı

\- nutrition adayını



düzeltebilir.



Bu özellikle görüntüden gramaj tahmininin belirsiz olduğu durumlarda önemlidir.



\## 9. AI Kullanımında Güvenlik



AI araçlarına:



\- API anahtarları

\- şifreler

\- kişisel erişim bilgileri

\- gerçek kullanıcı kişisel verileri



gönderilmemelidir.



Gemini API anahtarı `.env` içerisinde tutulmaktadır.



`.env` Git repository'sine dahil edilmemektedir.



\## 10. Öğrenilenler



AI destekli geliştirme sırasında aşağıdaki konularda pratik kazanılmıştır:



\- Gemini Vision API kullanımı

\- Structured JSON output

\- Pydantic validation

\- Retry ve error handling

\- Türkçe metin normalization

\- Fuzzy/candidate matching yaklaşımı

\- Nutrition calculation

\- SQLite

\- Streamlit state yönetimi

\- Evaluation metricleri

\- Git ile kontrollü geliştirme



En önemli öğrenme, AI tarafından üretilen kodun çalıştırılmadan ve test edilmeden doğru kabul edilmemesi gerektiğidir.



Bu projede önerilen çözümler küçük adımlarla uygulanmış ve her aşama gerçek çıktılarla doğrulanmıştır.

