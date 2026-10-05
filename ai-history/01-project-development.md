\# AI Development History



\## Proje



Food Lens — Nusthera Staj Teknik Değerlendirme Projesi



\## Amaç



Yemek fotoğrafından yiyecekleri tespit etmek, tahmini gramajlarını almak ve nutrition değerlerini uygulamanın kendi referans tablosundan hesaplamak.



\## Geliştirme Aşamaları



\### 1. Proje Planlama



AI yardımıyla proje gereksinimleri parçalara ayrıldı.



Ana bileşenler:



\- Streamlit UI

\- Gemini Vision

\- Pydantic

\- Nutrition CSV

\- SQLite

\- Evaluation



\### 2. Gemini Vision Entegrasyonu



Görüntünün Gemini API'ye gönderilmesi ve yapılandırılmış JSON cevap alınması geliştirildi.



Beklenen model çıktısı:



```json

{

&#x20; "items": \[

&#x20;   {

&#x20;     "name": "rice, white, cooked",

&#x20;     "grams": 180,

&#x20;     "confidence": 0.86

&#x20;   }

&#x20; ],

&#x20; "notes": "..."

}

```



\### 3. Validation



Model çıktısının Pydantic ile doğrulanması eklendi.



Boş veya geçersiz JSON cevaplarında retry ve hata yönetimi uygulandı.



\### 4. Nutrition Sistemi



Nutrition değerlerinin Gemini tarafından verilmemesine karar verildi.



Bunun yerine:



```text

Gemini

↓

food name + grams

↓

local foods.csv

↓

nutrition calculation

```



akışı oluşturuldu.



\### 5. Matching



Modelin ürettiği yemek isimleri ile CSV isimlerinin farklı olabileceği görüldü.



Türkçe karakter normalization ve candidate matching geliştirildi.



Test sırasında:



```text

Kuru Nane

```



ifadesinin yanlışlıkla:



```text

Kuru Fasulye

```



ile eşleşme riski tespit edildi.



Bu problem sonrasında matching daha kontrollü hale getirildi.



\### 6. Kullanıcı Düzeltmesi



Belirsiz nutrition eşleşmelerinde kullanıcıya adaylar gösterildi.



Ayrıca gramajın kullanıcı tarafından değiştirilmesi sağlandı.



\### 7. SQLite



Hesaplanan öğünlerin kaydedilmesi ve günlük toplamların hesaplanması için SQLite eklendi.



\### 8. Mock Mode



API anahtarı olmadan uygulamanın test edilebilmesi için:



```text

fixtures/mock\_analysis.json

```



oluşturuldu.



\### 9. Evaluation



15 görüntülük evaluation seti oluşturuldu.



Recognition sonucu:



```text

93.3% (14/15)

```



Calorie evaluation sonucu:



```text

130.8% average error (9 images)

```



olarak ölçüldü.



Calorie sonucunda özellikle gramaj tahmininin büyük etkisi olduğu görüldü.



\## AI Kullanım İlkesi



AI tarafından önerilen kod doğrudan doğru kabul edilmedi.



Her önemli değişiklik:



1\. Uygulandı.

2\. Çalıştırıldı.

3\. Çıktısı kontrol edildi.

4\. Gerekirse düzeltildi.



Bu yaklaşım özellikle encoding, matching ve evaluation aşamalarında kullanıldı.



\## Sonuç



AI, projede kodlama yardımcısı, hata ayıklama yardımcısı ve teknik danışman olarak kullanıldı.



Son uygulama kararları ve test sonuçları geliştirici tarafından doğrulandı.

