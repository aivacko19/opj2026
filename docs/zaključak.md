# Zaključak

---

## 1. Odgovori na postavljena pitanja

### Može li se subjektivnost pouzdano anotirati na srpskom?

Delimično. Saglasnost pre razgovora bila je **0,666** (prosek parnih Koenovih
kapa; Fajsova kapa 0,665, Kripendorfova alfa 0,666 — sve tri mere daju istu
vrednost). To je iznad 0,51 koliko je na istom koraku prijavljeno za engleski
korpus po čijem smo uputstvu radili, ali daleko od pune saglasnosti: na 24,3%
rečenica nismo se složili.

Uputstvo pokriva 97,6% spornih slučajeva — od 85 neslaganja, samo dva nije
rešilo nijedno pravilo. Najteža pravila su ona bez površinskog znaka:
mišljenje u tvrdnoj formi (P4) i rečenica bez sopstvenog stava (P7) zajedno čine
36% svih neslaganja.

### Da li je uzorkovanje izbeglo tematski konfaund?

Jeste, na nivou korpusa. Tema i oznaka povezane su sa **Cramerovim V = 0,116**,
što je ispod praga slabe povezanosti. Postupak koji je do toga doveo — prvo se
uzorkuju kolumne, izmeri se raspodela tema, pa se vesti uzorkuju tako da je
preslikaju — pokazao se kao dovoljan.

Ali analiza naučenih odlika pokazuje da to **ne sprečava model da nađe prečicu
na nivou pojedinačnih reči**. Dve najjače odlike najboljeg osnovnog modela su
`naprednjačk` i `naprednjak`, a među odlikama koje vuku ka objektivnosti su goli
brojevi i nazivi meseci. Tema kao kategorija ne predviđa oznaku, ali pojedinačni
leksički markeri tema i dalje jesu povezani sa njom.

### Koliko pomaže morfološka normalizacija?

Stemovanje pomaže, ali **samo Bajesovom klasifikatoru i samo uz n-grame višeg
reda** (0,709 naspram 0,679, p = 0,027). Kod logističke regresije nema efekta.

Dobitak je manji nego što bi morfološka složenost srpskog sugerisala, i razlog je
izmeren unapred: stemer ne saživa nepostojano *a*, pa `sramotan` ostaje odvojeno
od `sramotna`, `sramotni`, `sramotno` — dakle upravo kod evaluativnih prideva,
koji su glavni nosioci subjektivnosti.

Nalaz o broju odlika bio je suprotan očekivanju. Stemovanje smanjuje rečnik 1,49
puta, ali broj odlika posle praga `min_df=2` opada samo 17% kod unigrama, a kod
trigrama čak **raste 2%**. Uzrok je to što stemovanje ne samo da spaja oblike
nego i spasava odlike koje bi se inače javile samo jednom. To je i objašnjenje
zašto najviše pomaže baš uz trigrame.

### Da li n-grami pomažu?

Zavisi od modela. Kod Bajesa bigrami donose dobitak uz TF ponderisanje
(+0,017, p = 0,010 na običnoj shemi), kod logističke regresije ne donose ništa.
Prelaz sa bigrama na trigrame ne donosi ništa ni kod koga.

Uzrok je retkost. Najčešći informativni bigram (`kao da`) javlja se u 13 od
3.128 rečenica. Konstrukcije jesu nosioci subjektivnosti — primeri grešaka to
potvrđuju — ali su previše raznolike da bi se ijedna dovoljno ponovila.

### Šta je sa dekoderskim modelima?

Znatno su bolji: **0,862** naspram 0,709. Oba modela postižu saglasnost sa
zlatnim oznakama (κ 0,63–0,72) uporedivu sa saglasnošću među anotatorima (0,67).

Ni jezik upita ni primeri u upitu nemaju veliki efekat. Osam primera ne pomaže
nijednom modelu ni na jednom jeziku; jedina značajna razlika je *negativna*.
Jezik upita ima efekat reda 0,01, **suprotnog smera kod dva modela** — ChatGPT
je bolji sa engleskim, Gemini sa srpskim upitom. Da je ispitan samo jedan model,
zaključak bi bio pogrešno uopšten.

Razlika između modela (0,03–0,05) veća je od razlike između bilo koja dva upita,
i gotovo je isključivo u odzivu na klasi SUBJ: ChatGPT propušta četvrtinu
subjektivnih rečenica, Gemini šestinu, uz gotovo istu preciznost.

---

## 2. Šta je korpus doneo

Dekoderski model bez ijednog primera nadmašuje linearni model obučen na 2.808
označenih rečenica. Postavlja se pitanje čemu je onda poslužila anotacija.

Tri odgovora.

**Bez zlatnih oznaka se ne bi znalo koliko su modeli dobri.** Vrednost 0,862 je
merljiva samo naspram ručno označenog skupa.

**Bez njih se ne bi znalo gde greše.** Nalaz da sva tri sistema padaju na
prenetom tuđem iskazu proizlazi iz toga što uputstvo pravilom P6 razdvaja *ko
tvrdi* od *šta se tvrdi* — razlika koju modeli ne prave, i koja se bez anotacije
ne bi ni primetila.

**Osnovni model i dalje doprinosi.** Jedini pogađa 110 rečenica koje oba
dekoderska modela promaše, više nego što bilo koji od njih pogađa sam. Bar jedan
sistem je tačan na 94,2% rečenica, naspram 86,5% za najbolji pojedinačni. Ta
razlika od 7,7 procentnih poena je informacija koju nose leksički markeri
naučeni baš iz ovog korpusa.

---

## 3. Granice zadatka

Od 3.120 rečenica, **182 (5,8%)** ne pogađa nijedan sistem. Njihova raspodela
pokazuje gde je zadatak zaista težak:

- 74% su rečenice koje **odudaraju od registra svog žanra** — objektivne
  rečenice u kolumnama i subjektivne rečenice u vestima;
- objektivne rečenice u vestima, dakle očekivan slučaj, gotovo da se ne greše
  (5 od 182).

Sva tri sistema se u teškim slučajevima oslanjaju na žanrovski registar. Kada
rečenica odudara, promaše je. Isti obrazac važi i za ljude: saglasnost anotatora
bila je najniža upravo na tim rečenicama, a sva tri sistema padaju sa ~0,93 na
0,49–0,71 na spornim rečenicama.

To je, dakle, granica zadatka, a ne granica pojedinačnog modela.

---

## 4. Ograničenja

**Jednostruka anotacija glavnog skupa.** Za 2.778 od 3.128 rečenica postoji samo
jedna oznaka. Udeo subjektivnih oznaka kretao se od 36,4% do 49,4% po anotatoru,
na delovima uravnoteženim po izvoru i žanru, pa oznaka delom zavisi od toga ko je
anotirao. Razlika je uočena na kalibraciji i razgovorom smanjena, ali nije
uklonjena.

**Saglasnost posle razgovora nije izmerena.** Zbog vremenskog ograničenja druga
runda kalibracije na svežem uzorku nije sprovedena, pa se prijavljuje samo
vrednost pre usaglašavanja.

**Ponovljivost dekoderskih modela nije proverena.** Nije izmereno koliko se
rezultat menja između dva pokretanja iste konfiguracije pri temperaturi 0, pa se
ne može isključiti da razlike reda 0,01 — koliko iznosi efekat jezika upita —
leže unutar tog šuma. Razlika između modela (0,03–0,05) je dovoljno velika da na
nju ovo ne utiče.

**Povezanost izvora i žanra.** Udeo kolumni po izvoru kreće se od 10% (`blic.rs`)
do 78% (`n1info.rs`). Pokušano je da se izjednači, ali samo delimično uspešno.
Posle anotacije se pokazalo da to nije proizvelo povezanost izvora i oznake
(V = 0,148 i 0,084 unutar žanra), pa ograničenje nije imalo posledice — ali je
ostalo.

**Koncentracija kolumnista nije potpuno merljiva.** Ograničena je na 20 članaka
po autoru, ali samo za 126 od 256 kolumni kod kojih se autor vidi iz URL-a.
Rubrike `pogledi`, `komentar` i `Smatracnica` ne otkrivaju autora.

**Podskupovi premali za merenje.** Saglasnost anotatora na rečenicama unutar
navoda, na pitanjima i na rečenicama sa diskursnim konektorima nije pouzdano
merljiva na 350 rečenica. Provera pravila P8, predviđena uputstvom, nije
sprovedena jer je takvih rečenica u kalibracionom skupu bilo svega 8.

**Grupisanje rečenica u upitima.** Dekoderskim modelima su rečenice slate u
grupama od 15 iz uzastopnih prozora, pa model unutar grupe vidi susedne rečenice
istog članka — kontekst koji anotatori po uputstvu nisu koristili. Isto je za sve
konfiguracije, pa ne utiče na poređenja između njih, ali utiče na apsolutne
vrednosti.

---

## 5. Šta bi bilo sledeće

**Enkoderski modeli.** BERTić i multilingvalni modeli nisu razmatrani zbog
veličine grupe i obima ostalih delova. To je najočiglednija praznina između
linearnih modela na 0,709 i dekoderskih na 0,862.

**Pravilo o tuđem iskazu kao odlika.** Kolona `in_quote` postoji u korpusu, ali
nije korišćena kao odlika. Pošto je preneti iskaz najteži podskup za sve
sisteme, eksplicitno obeležavanje navoda verovatno bi pomoglo — i osnovnom
modelu i u upitu dekoderskom.
