# Stemovanje i analiza naučenih odlika

---

## 1. Uvod

Korišćen je stemer Ljubešića i Pandžića, predložen na konsultacijama. U radovima o analizi
sentimenta na srpskom davao je bolje rezultate od lematizacije, uz napomenu da
mu prednost raste sa n-gramima višeg reda. Ta interakcija je i razlog
zašto se stemovanje kod nas ukršta sa opsegom n-grama.

### Ograničenje

Stemer ne saživa nepostojano a:

| oblici | koreni |
|---|---|
| sramotan, sramotna, sramotni, sramotno, sramotnog | `sramotan`, `sramotn` |
| zavidan, zavidna, zavidni, zavidnom | `zavidan`, `zavidn` |
| besraman, besramna, besramno | `besraman`, `besramn` |

Muški rod jednine ostaje odvojen od ostalih oblika. Posledica je da se očekivani
dobitak smanjuje kod evaluativnih prideva, koji su nosioci pravila P1
i time najvažniji za prepoznavanje subjektivnosti.

---

## 2. Rezultati

Sve vrednosti su makro F1 iz desetoslojne unakrsne validacije sa grupisanjem po
članku (`StratifiedGroupKFold`), uz ugnežđenu petostruku validaciju za izbor
hiperparametra. Značajnost je Vilkoksonov upareni test po slojevima, u odnosu na
referentnu konfiguraciju `w1-tfidf-lower`.

### Logistička regresija

| konfiguracija | makro F1 | F1 SUBJ | odlika | p |
|---|---|---|---|---|
| `w1-tfidf-lower` (ref.) | 0,681 ± 0,032 | 0,622 | 5.751 | — |
| `w1-tfidf-lower-stem` | 0,680 ± 0,036 | 0,623 | 4.788 | 1,000 |
| `w12-tfidf-lower-stem` | 0,684 ± 0,033 | 0,626 | 9.865 | 0,734 |
| `w13-tfidf-lower-stem` | 0,690 ± 0,041 | 0,633 | 11.339 | 0,492 |
| `w13-tf-lower-stem` | 0,684 ± 0,034 | 0,627 | 11.339 | 0,695 |

Kod logističke regresije stemovanje ne pomaže. Nijedna razlika nije
značajna, a najbolja vrednost je za 0,009 iznad referentne, što je ispod
standardne devijacije od 0,03–0,04.

### Bajesov klasifikator

| konfiguracija | makro F1 | F1 SUBJ | odlika | p |
|---|---|---|---|---|
| `w1-tfidf-lower` (ref.) | 0,679 ± 0,026 | 0,623 | 5.751 | — |
| `w1-tfidf-lower-stem` | 0,690 ± 0,036 | 0,627 | 4.788 | 0,232 |
| `w12-tfidf-lower-stem` | 0,699 ± 0,042 | 0,646 | 9.865 | 0,131 |
| `w13-tfidf-lower-stem` | 0,707 ± 0,041 | 0,655 | 11.339 | **0,049** |
| `w13-tf-lower-stem` | **0,709 ± 0,040** | **0,658** | 11.339 | **0,027** |

Kod Bajesa stemovanje pomaže, i to značajno uz n-grame višeg reda.
Najbolja konfiguracija u celom eksperimentu je `w13-tf-lower-stem` sa Bajesom,
makro F1 = 0,709.

### Interakcija sa n-gramima

Interakcija se potvrđuje, ali samo kod Bajesa:

| | unigrami | + bigrami | + trigrami |
|---|---|---|---|
| bez stemovanja | 0,679 | 0,690 | 0,691 |
| sa stemovanjem | 0,690 | 0,699 | 0,707 |

Dobitak od stemovanja raste sa opsegom n-grama (+0,011 → +0,009 → +0,016), a
dobitak od n-grama je veći kada je tekst stemovan.

### Broj odlika

Na celom korpusu stemovanje smanjuje broj različitih tokena 1,49 puta (9.108 →
6.106). Očekivali smo sličnu kompresiju i u prostoru odlika, ali je stvarni
efekat mnogo manji, a kod trigrama i obrnut:

| | bez stemovanja | sa stemovanjem |
|---|---|---|
| unigrami | 5.751 | 4.788 (−17%) |
| trigrami | 11.118 | 11.339 (+2%) |

Uzrok je prag `min_df=2`. Stemovanje spaja oblike, čime smanjuje rečnik, ali
istovremeno spasava odlike koje se javljaju samo jednom: dva oblika sa po
jednim pojavljivanjem postaju jedan koren sa dva, pa prolaze prag. Kod retkih
trigrama taj efekat nadjačava sažimanje. Stemovanje daje retkim
konstrukcijama dovoljno pojavljivanja da uđu u model što pomaže uz trigrame.

---

## 3. Model

Najbolja konfiguracija je uklopljena na celom korpusu, a odlike su poređane po
razlici logaritama verovatnoća između klasa.

### Odlike koje vuku ka SUBJ

Deo jeste ono što uputstvo opisuje: `valjd`, `pošten`, `laž`, `tešk da`,
`spremn da`, `režimsk`, `bagr`, `umel`, `razumel`. To su ograde, ocene i
konstrukcije koje nose stav.

Ali dve najjače odlike u celom modelu su **`naprednjačk` i `naprednjak`**, a
odmah uz njih `kobr`, `kokez`, `miting`, `student su`, `lažn studentsk list`.

### Odlike koje vuku ka OBJ

Ovde je slika još jasnija: `požar`, `ratk mladić`, `kilometr`, `crkv`,
`bolnic`, `područj`, `oktobr`, kao i brojevi `21`, `24`, `27`. Uz njih i
glagoli prenošenja `rekl je`, `napisa je`, `nave je`, `doda je`, `navod da`
koji su signal za objektivnost.

### Zaključak

**Model delom prepoznaje temu, a ne subjektivnost.** Brojevi i nazivi meseci kao
dokaz za objektivnost nisu obeležje objektivnosti nego izveštajnog registra.
Imena stranaka kao dokaz za subjektivnost nisu obeležje stava nego toga o čemu
se u medijima piše sa stavom.

Ovo ne protivreči nalazu iz faze anotacije. Na nivou korpusa tema praktično ne
predviđa oznaku (Cramerovo V = 0,116, videti odeljak o anotaciji), i uzorkovanje
je taj konfaund izbeglo. Ali model radi na nivou pojedinačnih reči, gde i dalje
postoji prečica: pojedinačni leksički markeri tema ostaju povezani sa
oznakom čak i kada tema kao kategorija nije.

---

## 4. Gde model greši

Predikcije su izvan sloja (svaka rečenica predviđena modelom koji je nije video),
makro F1 = 0,709.

| | predviđeno OBJ | predviđeno SUBJ |
|---|---|---|
| **OBJ** | 1.398 | 403 |
| **SUBJ** | 479 | 848 |

Greške su gotovo simetrične (403 naspram 479), dakle nije reč o pomerenom pragu
nego o nedostatku signala.

### Po podskupovima

| podskup | n | makro F1 | F1 SUBJ |
|---|---|---|---|
| žanr = kolumna | 1.767 | 0,643 | 0,726 |
| žanr = vest | 1.361 | 0,580 | 0,282 |
| unutar navoda (P6, P13) | 281 | 0,504 | 0,218 |
| pitanja (P9) | 93 | 0,586 | 0,822 |
| puna saglasnost anotatora | 265 | 0,789 | 0,727 |
| bilo sporno | 85 | 0,482 | 0,488 |

Tri mesta gde model praktično ne radi:

**Rečenice unutar navoda** (0,504 makro, 0,218 za SUBJ). Pravilo P6 kaže da je
preneti tuđi iskaz objektivan; anotatori su ga primenili dosledno (10,0% SUBJ u
navodima naspram 42,4% u korpusu), model ga ne prepoznaje.

**Subjektivne rečenice u vestima** (F1 SUBJ 0,282). Takvih rečenica je malo
(10–17% po izvoru), a leksički se ne razlikuju od okolnog izveštavanja.

**Sporne rečenice** (0,482). Model je znatno lošiji tamo gde se ni
anotatori nisu složili. To znači da prati istu podelu na lako i teško kao ljudi.

---

## 5. Zaključak

Stemovanje pomaže, ali samo Bajesovom klasifikatoru i samo u kombinaciji sa
n-gramima višeg reda (0,709 naspram 0,679, p = 0,027). Dobitak je manji nego što
bi morfološka složenost srpskog sugerisala, a razlog je delimično izmeren
unapred: nepostojano a onemogućava saživanje kod evaluativnih prideva.

Analiza naučenih odlika pokazuje da model dobar deo uspešnosti duguje tematskim
markerima, a ne obeležjima stava. Najveći nedostatak je nemoć da prepozna
preneti tuđi iskaz i da uhvati subjektivnost koja živi u konstrukciji, a ne u
pojedinačnoj reči.

Najbolja postignuta vrednost u track A je **makro F1 = 0,709**.