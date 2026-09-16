# Ponderisanje i mala slova

---

## 1. Šta je mereno i zašto

Ispitivane su dve površinske odluke u izgradnji odlika, svaka kao jedna izmena
u odnosu na referentnu konfiguraciju `w1-tfidf-lower` (unigrami, TF-IDF, mala
slova):

| konfiguracija | šta menja |
|---|---|
| `w1-tf-lower` | TF umesto TF-IDF |
| `w1-tfidf-nolower` | bez spuštanja na mala slova |
| `w13-tfidf-nolower` | bez malih slova, uz bigrame i trigrame |

**TF naspram TF-IDF.** Jedinica klasifikacije je jedna rečenica, medijalne
dužine 19 tokena. U tako kratkom „dokumentu" gotovo svaka reč se javlja tačno
jednom, pa je TF za skoro sve odlike jednak 1 i od TF-IDF-a se razlikuje samo po
skaliranju kolona. Na našem korpusu je to i izbrojano: od svih nenultih
ćelija matrice rečenica × unigram (min_df = 2), **92,5% ima vrednost 1**, a
svega 1,4% vrednost 3 ili veću. Očekivali smo, dakle, malu ili nikakvu razliku, i to je
nalaz sam po sebi: ponderisanje osmišljeno za dokumente ne radi ništa kada je
dokument jedna rečenica.

**Mala slova.** Velika slova nose vlastita imena, a vlastita imena nose temu.
Ako ukidanje spuštanja na mala slova pomogne, model bi delom prepoznavao o
*kome* se piše umesto *kako* se piše, što bi bilo u sukobu sa nalazom iz faze
anotacije da tema praktično ne predviđa oznaku (Cramerovo V = 0,116).

Svaka konfiguracija je pokrenuta sa oba modela (logistička regresija, Bajes) i
po obe sheme slojeva: obična stratifikovana (`plain`) i grupisana po članku
(`grouped`). Hiperparametar (C, odnosno α) biran je ugnežđenom petostrukom
validacijom unutar svakog spoljnog sloja. Značajnost je merena Vilkoksonovim
testom nad 10 uparenih slojeva, a ne t-testom, jer slojevi unakrsne validacije
dele trening podatke i nisu nezavisni.

Pre pravih oznaka pokrenuta je provera curenja (`--leak-test`): oznaka je
slučajna po članku, tekst ne nosi signal. Obična podela dala je makro F1
**0,826 ± 0,026**, grupisana **0,546 ± 0,077**. Obična desetoslojna validacija
na našem korpusu, dakle, može da prijavi 0,83 za model koji nije naučio ništa,
jer sedam od osam rečenica jednog članka završi u trening skupu.

---

## 2. Rezultati

Makro F1, prosek ± standardna devijacija po 10 slojeva. Poslednje dve kolone su
p-vrednosti Vilkoksonovog testa u odnosu na referentnu konfiguraciju, uz isti
model i istu shemu.

| konfiguracija | model | plain | grouped | plain − grouped | p vs ref (plain) | p vs ref (grouped) |
|---|---|---|---|---|---|---|
| `w1-tfidf-lower` (ref) | logreg | 0,694 ± 0,021 | 0,681 ± 0,032 | +0,013 | — | — |
| `w1-tfidf-lower` (ref) | nb | 0,698 ± 0,036 | 0,679 ± 0,026 | +0,019 | — | — |
| `w1-tf-lower` | logreg | 0,693 ± 0,024 | 0,680 ± 0,029 | +0,013 | 1,000 | 0,922 |
| `w1-tf-lower` | nb | 0,701 ± 0,027 | 0,677 ± 0,032 | +0,023 | 0,557 | 0,492 |
| `w1-tfidf-nolower` | logreg | 0,692 ± 0,025 | 0,663 ± 0,034 | +0,029 | 1,000 | **0,012** |
| `w1-tfidf-nolower` | nb | 0,698 ± 0,030 | 0,672 ± 0,025 | +0,026 | 0,557 | 0,275 |
| `w13-tfidf-nolower` | logreg | 0,686 ± 0,030 | 0,653 ± 0,029 | +0,033 | 0,275 | **0,006** |
| `w13-tfidf-nolower` | nb | 0,702 ± 0,034 | 0,679 ± 0,023 | +0,023 | 0,557 | 0,922 |

Razlika u odnosu na referentnu, grupisana shema, po klasama:

| konfiguracija | model | Δ makro F1 | Δ F1 SUBJ | Δ F1 OBJ | slojeva bolje / gore | p |
|---|---|---|---|---|---|---|
| `w1-tf-lower` | logreg | −0,001 | −0,005 | +0,003 | 5 / 5 | 0,922 |
| `w1-tf-lower` | nb | −0,002 | −0,006 | +0,003 | 3 / 7 | 0,492 |
| `w1-tfidf-nolower` | logreg | −0,018 | −0,022 | −0,014 | 2 / 8 | **0,012** |
| `w1-tfidf-nolower` | nb | −0,007 | −0,012 | −0,003 | 4 / 6 | 0,275 |
| `w13-tfidf-nolower` | logreg | −0,028 | −0,037 | −0,019 | 1 / 9 | **0,006** |
| `w13-tfidf-nolower` | nb | −0,000 | +0,003 | −0,004 | 6 / 4 | 0,922 |

**TF naspram TF-IDF: razlike nema.** Kod oba modela i obe sheme razlika je
unutar ±0,002, daleko ispod standardne devijacije (0,02–0,03), a slojevi se dele
5 : 5, odnosno 3 : 7. To je očekivani rezultat iz odeljka 1 — izmeren, ne
pretpostavljen. Za izveštaj to znači da izbor između TF i TF-IDF na nivou
rečenice nije odluka koja išta menja i ne treba je dalje ispitivati.

**Mala slova: spuštanje na mala slova pomaže, i to statistički značajno kod
logističke regresije.** Bez spuštanja, logistička regresija gubi 0,018 makro F1
sa unigramima (p = 0,012, 8 od 10 slojeva gore) i 0,028 sa trigramima
(p = 0,006, 9 od 10 slojeva gore). Gubitak je veći na klasi SUBJ (−0,022 i
−0,037) nego na OBJ. Kod Bajesa je razlika sa unigramima u istom smeru ali
nije značajna (−0,007, p = 0,275), a sa trigramima je nema (−0,000, slojevi
6 : 4). Model, dakle, **nije** imao koristi od velikih slova — ni od
vlastitih imena ni od početka rečenice — nego mu je dodatna podela rečnika
(`Vučić`/`vučić`, `Zato`/`zato`) samo razredila odlike. Broj odlika raste sa
5.751 na 5.919 (unigrami, medijana po slojevima), ali su nove odlike ređe
verzije postojećih, pa liblinear sa istim C ima manje primera po odlici. Šta
su te nove odlike: od 8.468 pojavljivanja tokena velikim slovom u korpusu,
63% je usred rečenice (`Srbije`, `Vučić`, `Beogradu`, `SNS`, `SAD`, `BiH`…),
dakle vlastita imena, a 37% na početku rečenice, dakle obične reči udvojene
velikim slovom. Ni jedna od te dve grupe modelu nije pomogla. To je u skladu sa nalazom iz
faze anotacije da tema ne predviđa oznaku: da su vlastita imena bila korisna,
očekivali bismo poboljšanje, a ne pogoršanje, kada ih model vidi odvojeno od
opštih reči.

Zašto Bajes trpi manje: multinomijalni Bajes sa α = 0,1 računa verovatnoće po
odlici nezavisno, pa retka odlika sa istom raspodelom klasa kao njena
mala-slova verzija ne unosi novu informaciju ali ni ne šteti; logistička
regresija deli težinu između dve verzije iste reči i svaka dobija manje
podataka za procenu.

---

## 3. Razlika između shema slojeva

| konfiguracija | model | plain − grouped | p (upareno) |
|---|---|---|---|
| `w1-tfidf-lower` | logreg | +0,013 | 0,492 |
| `w1-tfidf-lower` | nb | +0,019 | 0,232 |
| `w1-tf-lower` | logreg | +0,013 | 0,432 |
| `w1-tf-lower` | nb | +0,023 | 0,131 |
| `w1-tfidf-nolower` | logreg | +0,029 | 0,064 |
| `w1-tfidf-nolower` | nb | +0,026 | 0,064 |
| `w13-tfidf-nolower` | logreg | +0,033 | 0,084 |
| `w13-tfidf-nolower` | nb | +0,023 | 0,232 |

Obična podela prijavljuje sistematski viši rezultat od grupisane, u svih osam
kombinacija, za 0,013 do 0,033 makro F1. Razlika nije značajna ni za jednu
pojedinačnu kombinaciju (p od 0,06 do 0,49; slojevi dve sheme nisu upareni po
sadržaju, pa je test ovde samo orijentacija), ali je smer dosledan, a na
sintetičkom testu ista razlika iznosi 0,28. Na stvarnim podacima je curenje
mnogo manje nego što bi moglo biti, jer model uči subjektivnost, a ne identitet
članka — ali nije nula.

Vredi primetiti da se **razlika povećava upravo kod konfiguracija bez malih
slova** (0,026–0,033 naspram 0,013–0,023). Velika slova, tj. vlastita imena,
jesu ono po čemu se članak najlakše prepoznaje: kada su rečenice istog članka i
u trening i u test skupu, ime aktera koje se ponavlja kroz osam rečenica
postaje odlika koja „radi" u običnoj podeli i prestaje da radi u grupisanoj.
Konfiguracija bez malih slova je u običnoj podeli gotovo jednaka referentnoj
(0,692 naspram 0,694), a u grupisanoj značajno lošija (0,663 naspram 0,681).
Da smo prijavili samo običnu desetoslojnu validaciju, zaključak o malim slovima
bi bio „nema razlike". To je konkretan primer zašto prijavljujemo obe sheme.

---

## 4. Sažetak za izveštaj

- TF i TF-IDF daju isti rezultat na nivou rečenice (Δ ≤ 0,002, p > 0,49). Nalaz
  je očekivan: u rečenici od 19 tokena TF je gotovo uvek 1 (92,5% ćelija).
- Spuštanje na mala slova pomaže: bez njega logistička regresija gubi 0,018
  (unigrami, p = 0,012) do 0,028 (trigrami, p = 0,006) makro F1 u grupisanoj
  validaciji. Velika slova ne nose korisnu informaciju o subjektivnosti; samo
  razređuju rečnik.
- Obična podela precenjuje rezultat za 0,013–0,033 u odnosu na grupisanu, i
  najviše upravo tamo gde su vlastita imena zadržana kao zasebne odlike. Sve
  vrednosti koje se porede između konfiguracija treba uzimati iz grupisane
  sheme.
