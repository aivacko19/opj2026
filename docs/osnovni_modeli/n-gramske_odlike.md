**N-gramske odlike** 

**Pitanje:** Da li višerečne odlike (bigrami, trigrami) pomažu u prepoznavanju subjektivnosti?

## Leakage test

Pre merenja bilo čega stvarnog, provereno je da li sam postupak merenja radi ispravno.
Curenje podataka (*data leakage*) znači da informacija iz skupa za proveru posredno
dospe u skup za učenje, pa rezultat ispadne bolji nego na stvarno novim podacima.
Svakom članku je dodeljena nasumična oznaka, ista za svih osam njegovih rečenica, pa
u tekstu nema ničega što bi se mogla naučiti. Ispravan postupak bi tu morao
dati oko 0,5.

| šema | macro-F1 |
|---|---|
| plain (obična stratifikovana podela, *stratified split*) | 0,826 ± 0,026 |
| grouped (grupisano po članku, *grouped split*) | 0,546 ± 0,077 |

*Stratifikovana podela - pri deljenju na rečenice za učenje i rečenice za proveru, pazi se da odnos klasa (odnos SUBJ i OBJ) kod njih bude isti

Obična podela daje 0,826 za model koji objektivno nije mogao ništa da nauči — jer sedam
od osam rečenica jednog članka završi u trening skupu, pa model prepoznaje članak umesto
da procenjuje subjektivnost. Grupisana podela to sprečava i vraća očekivanih ~0,5.
Time je potvrđeno da postupak merenja radi ispravno — grupisana podela tačno prijavljuje da nema šta da se nauči, dok obična prijavljuje uspeh kojeg nema.

---

## Broj odlika (*features*) posle `min_df=2`

| konfiguracija | opseg n-grama | odlike | promena u odnosu na referentnu |
|---|---|---|---|
| `w1-tfidf-lower` | (1,1) — samo reči | 5.742 | referentna |
| `w12-tfidf-lower` / `w12-tf-lower` | (1,2) — + bigrami | 9.903 | +72% |
| `w13-tfidf-lower` / `w13-tf-lower` | (1,3) — + trigrami | 11.074 | +93% |

Bigrami su dodali ~4.160 kolona (sa 5.742 na 9.903), jer u korpusu postoji toliko različitih parova reči koji se javljaju bar dvaput.
Trigrami su dodali samo ~1.171 (sa 9.903 na 11.074), jer se ogromna većina različitih trojki javlja tačno jednom — pa otpadnu, i nikad ne postanu kolona. 
Dakle, bigrami skoro udvostruče prostor odlika (*feature space*). Trigrami preko toga dodaju svega +12% odlika.
Trigrama ima mnogo, ali skoro svaki samo po jednom, tako da otpadaju na
pragu `min_df=2`.


 *min_df - minimum document frequency (broj pojavljivanja u podacima)

---

## Rezultati

Svaka vrednost je prosek iz 10 krugova unakrsne validacije (*cross-validation*; jedan
krug = *fold*), uz standardnu devijaciju
koja pokazuje koliko su se ti krugovi međusobno razlikovali. Podebljano = razlika u
odnosu na referentnu konfiguraciju je statistički značajna (upareni Vilkoksonov test,
*paired Wilcoxon signed-rank test*,
krug po krug, p < 0,05).

### Logistička regresija

| konfiguracija | plain | grouped | plain − grouped |
|---|---|---|---|
| `w1-tfidf-lower` (ref.) | 0,694 ± 0,022 | 0,681 ± 0,034 | +0,013 |
| `w12-tfidf-lower` | 0,694 ± 0,029 (p=0,867) | 0,674 ± 0,030 (p=0,065) | +0,020 |
| `w13-tfidf-lower` | 0,695 ± 0,030 (p=1,000) | 0,674 ± 0,037 (p=0,193) | +0,021 |
| `w12-tf-lower` | 0,694 ± 0,030 (p=0,922) | **0,672 ± 0,034 (p=0,020)** | +0,023 |
| `w13-tf-lower` | 0,693 ± 0,029 (p=1,000) | 0,678 ± 0,034 (p=0,359) | +0,016 |

### Naivni Bajes

| konfiguracija | plain | grouped | plain − grouped |
|---|---|---|---|
| `w1-tfidf-lower` (ref.) | 0,698 ± 0,038 | 0,679 ± 0,028 | +0,019 |
| `w12-tfidf-lower` | 0,702 ± 0,039 (p=0,361) | **0,690 ± 0,025 (p=0,037)** | +0,011 |
| `w13-tfidf-lower` | 0,704 ± 0,039 (p=0,375) | 0,691 ± 0,028 (p=0,084) | +0,014 |
| `w12-tf-lower` | **0,715 ± 0,033 (p=0,010)** | 0,689 ± 0,028 (p=0,106) | +0,026 |
| `w13-tf-lower` | **0,712 ± 0,032 (p=0,037)** | 0,688 ± 0,027 (p=0,160) | +0,024 |

---


## Provera u korpusu: koje fraze zapravo postoje

Pošto se zaključak o retkosti oslanja na pretpostavku da su informativne konstrukcije
preretke, provereno je direktno u `corpus_labeled.tsv` koliko se stvarno javljaju.

Bigrami koji se javljaju u bar osam rečenica i bar dvostruko češće u SUBJ nego u OBJ:

| bigram | SUBJ | OBJ | odnos |
|---|---|---|---|
| `je li` | 9 | 2 | 6,1× |
| `kao da` | 13 | 3 | 5,9× |
| `ali to` | 8 | 2 | 5,4× |
| `ali ne` | 10 | 3 | 4,5× |
| `za razliku od` | 8 | 3 | 4,1× |
| `ne zna` | 8 | 3 | 3,6× |
| `ne samo` | 10 | 5 | 2,7× |
| `ne bi` | 16 | 8 | 2,7× |

---

Bigram koji se najčešće javlja - javlja se u svega 13 od 3.128
rečenica. Pri toj učestalosti model nema dovoljno primera da nauči pravilo, ma koliko
konstrukcija bila informativna. To je konkretna potvrda da je uzrok izostanka dobitka
retkost odlika.

## Diskusija 

**Zaključak:** Odgovor zavisi od modela. Logistička regresija
ne izvlači nikakvu korist iz višerečnih odlika: sve četiri konfiguracije daju praktično
istu vrednost kao referentna (0,693–0,695 na plain šemi), a nijedna razlika nije
značajna osim jedne granične, i to u *negativnom* smeru (`w12-tf-lower` na grouped šemi,
−0,010, p=0,020). Naivni Bajes, nasuprot tome, od bigrama profitira — i to dosledno uz TF
ponderisanje: `w12-tf-lower` daje +0,017 (p=0,010) i `w13-tf-lower` +0,014 (p=0,037) na
plain šemi. Odgovarajuće TF-IDF varijante su slabije od svojih TF parnjaka (0,702 i 0,704
naspram 0,715 i 0,712), što potvrđuje pretpostavku da IDF prigušuje upravo one
konstrukcije koje razlikuju klase. IDF daje veću težinu retkim odlikama, ali
konstrukcije poput `kao da` ili `ali ne` sastavljene su od čestih reči i zato bivaju
kažnjene — iako su baš one informativne.

**Zasićenje** (*saturation*)**.** Prelaz sa bigrama na trigrame ne donosi ništa. Broj odlika raste svega 12%
(9.903 → 11.074), a rezultat kod Bajesa čak blago pada (0,715 → 0,712 uz TF; 0,702 → 0,704
uz TF-IDF, unutar šuma). Ceo dobitak dolazi od bigrama; trigrami samo dodaju retke odlike
iz kojih se pri ovoj veličini korpusa (3.128 rečenica, medijalno 19 tokena) nema šta
naučiti — reč je o retkosti odlika. Tu je reč o zasićenju, a ne o tome da duže konstrukcije nisu informativne.

**Razlika između dve šeme podele.** Obična podela daje viši rezultat od grupisane u
svih deset kombinacija, bez izuzetka — razlika iznosi od +0,011 do +0,026 macro-F1.
Dakle i u pravim rezultatima jedan deo uspeha dolazi od toga što model prepoznaje
članak, a ne subjektivnost.

To naduvavanje je ipak mnogo manje nego u testu curenja, gde je razlika bila +0,280.
Tamo su oznake bile nasumične, pa je sve što je obična podela „postigla" bio
prividan uspeh. Ovde tekst stvarno nosi informaciju, pa je najveći deo rezultata pravo učenje,
a samo mali deo dolazi od preklapanja članaka između skupa za učenje i skupa za proveru.

Zato rezultate sa grupisane podele treba uzeti kao realniju procenu, a razliku između
dve šeme kao meru koliko obična podela precenjuje rezultat.
