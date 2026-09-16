# Klasifikacija subjektivnosti na nivou rečenice u srpskim novinskim tekstovima

Projekat iz predmeta Obrada prirodnih jezika, školska 2025/2026.
Anica Arsić, Dimitrije Stanišić, Aleksa Ivačko.

---

## 1. Zadatak

Za svaku rečenicu iz novinskog teksta treba odrediti da li iznosi **stav autora**
ili **tvrdnju o stvarnosti**:

| oznaka | značenje |
|---|---|
| `SUBJ` | rečenica iznosi stav, ocenu, doživljaj ili pretpostavku autora teksta |
| `OBJ` | rečenica iznosi tvrdnju o stvarnosti, prenosi tuđi iskaz, ili ne sadrži autorov stav |

Oznaka se odnosi na **glas autora**, ne na sadržaj rečenice. Rečenica može biti
puna oštrih ocena i svejedno biti objektivna, ako te ocene pripadaju nekome koga
autor citira. Ta razlika — između toga *šta se tvrdi* i *ko to tvrdi* — pokazala
se kao najteži deo zadatka i za anotatore i za sve ispitane modele.

Zadatak nije analiza sentimenta. Rečenica „Zakon je štetan" je subjektivna bez
obzira na to što je stav negativan; rečenica „Ministar je pohvalio zakon" je
objektivna bez obzira na to što prenosi pozitivnu ocenu.

---

## 2. Zašto ovaj zadatak i zašto ovaj domen

Detekcija subjektivnosti na nivou rečenice ustaljen je zadatak sa merljivim
rezultatima u literaturi — u okviru CLEF CheckThat! takmičenja obrađivan je za
arapski, bugarski, engleski, nemački i italijanski jezik. **Za srpski jezik u
novinskom domenu nije rađen.**

Novinski tekstovi su izabrani zato što u istom domenu postoje dva jasno
razdvojena žanra — izveštajni tekstovi i autorski tekstovi — pa se očekuje
dovoljan broj rečenica obe klase bez izlaska iz domena.

---

## 3. Šta je urađeno

**Faza 1.** Prikupljeno je 3.130 rečenica iz 406 članaka sa šest izvora:
`politika.rs`, `vreme.com`, `n1info.rs`, `rts.rs`, `danas.rs`, `blic.rs`.
Prikupljanje je vođeno tako da tema ne bude povezana sa žanrom, jer bi inače
klasifikator mogao da nauči temu umesto subjektivnosti.

**Faza 2.** Napisano je uputstvo za anotaciju sa 14 pravila, razvijeno kroz tri
verzije na osnovu probne anotacije, poređenja sa literaturom i probne runde sva
tri člana tima. Kalibracija na 350 rečenica dala je saglasnost od 0,666
(prosek parnih Koenovih kapa), posle čega je 85 spornih rečenica usaglašeno uz
navođenje pravila koje odlučuje. Konačni skup ima **3.128 označenih rečenica,
42,4% subjektivnih**.

**Faza 3.** Ispitana su dva tipa modela:

- **osnovni** — logistička regresija i multinomijalni Bajesov klasifikator, uz
  dvanaest konfiguracija odlika (n-gramski opseg, TF naspram TF-IDF, mala slova,
  stemovanje), desetoslojna unakrsna validacija sa ugnežđenim izborom
  hiperparametra;
- **dekoderski** — `gpt-4.1` i `gemini-3.8-flash`, po četiri konfiguracije upita
  (jezik upita × broj primera), nad celim skupom.

---

## 4. Glavni nalazi

**Uzorkovanje je izbeglo tematski konfaund.** Posle anotacije, povezanost teme i
oznake iznosi Cramerovo V = 0,116 — praktično zanemarljivo. Žanr očekivano
predviđa oznaku (V = 0,530), a povezanost izvora sa oznakom (V = 0,256) gotovo
nestaje kada se posmatra unutar žanra (0,148 i 0,084), dakle bila je posredovana
žanrom.

**Obična unakrsna validacija precenjuje rezultat.** Na sintetičkim podacima, gde
je oznaka slučajna po članku a tekst ne nosi nikakav signal, obična
stratifikovana podela prijavljuje 0,826 makro F1 za model koji nije naučio
ništa. Grupisanje po članku vraća očekivanih 0,546. Na stvarnim podacima je
razlika manja — 0,011 do 0,033 — ali sistematska, pa se svi rezultati
prijavljuju iz grupisane sheme.

**Stemovanje pomaže, ali samo Bajesu i uz n-grame višeg reda** (0,709 naspram
0,679, p = 0,027). Najbolji osnovni model postiže makro F1 **0,709**.

**Dekoderski modeli su znatno bolji: 0,862** (`gemini-3.8-flash`, srpski upit,
osam primera). Ni jezik upita ni primeri u upitu nemaju veliki efekat, a smer
efekta jezika zavisi od modela.

**Ali sistemi su komplementarni.** Osnovni model jedini pogađa 110 rečenica koje
oba dekoderska modela promaše — više nego što bilo koji od njih pogađa sam.

**Sva tri sistema padaju na istim mestima**: na prenetom tuđem iskazu, na
subjektivnosti u izveštajnom tekstu i na rečenicama oko kojih se ni anotatori
nisu složili.

---

## 5. Struktura izveštaja

| poglavlje | sadržaj |
|---|---|
| prikupljanje | izvori, prikupljanje, uzorkovanje, čišćenje, provera izbalansiranosti |
| anotacija | šema oznaka, razvoj uputstva, kalibracija, saglasnost, usaglašavanje |
| osnovni_modeli | n-gramske odlike, ponderisanje i mala slova, stemovanje |
| dekoderski_modeli | jezik upita, primeri u upitu, poređenje modela |
| zaključak | odgovori na postavljena pitanja i ograničenja |

Uputstvo za anotaciju, kod i podaci nalaze se u prilozima.
