# Anotacija podataka

## 1. Šema oznaka

Anotacija je binarna: svaka rečenica dobija oznaku `SUBJ` ili `OBJ`.

| Oznaka | Značenje |
|---|---|
| `SUBJ` | rečenica iznosi stav, ocenu, doživljaj ili pretpostavku autora teksta |
| `OBJ` | rečenica iznosi tvrdnju o stvarnosti, prenosi tuđi iskaz, ili ne sadrži autorov stav |

Oznaka se odnosi na glas autora, ne na sadržaj rečenice. Rečenica može biti puna
oštrih ocena i svejedno biti `OBJ`, ako te ocene pripadaju nekome koga autor
citira.

---

## 2. Razvoj uputstva

Uputstvo je prošlo kroz tri verzije. Iz korpusa je izvučeno 70 rečenica, raspoređenih srazmerno po žanru i temi, i anotirano bez uputstva od strane jednog anotatora. Teških je bilo 14 iz tih grupa su izvedena deset pravila. Pravila su zatim upoređena sa izvornim uputstvom pa su dodata još dva. Jedno pravilo (P8, diskursni konektori) je označeno kao naš dodatak jer nije bilo u izvoru. Preostala dva člana tima su anotirala po 30 rečenica sa svojih izvora, prema nacrtu
uputstva, i označavao mesta koja pravila ne pokrivaju. Iz toga su nastala dva
nova pravila.

Zasebno je obrađena kategorija pitanja. Svih 29 pitanja iz jednog dela korpusa
anotirala su nezavisno sva tri člana. Pravilo P9 je tada preformulisano.

---

## 3. Kalibracija

Iz spojenog korpusa izvučeno je 350 rečenica (oko 11%), srazmerno po izvoru i
žanru. Uzorak poštuje dva ograničenja:

- **najviše jedna rečenica po članku.** Korpus se sastoji od prozora od osam
  uzastopnih rečenica; slučajan uzorak dao bi grupe susednih rečenica iz istog
  teksta i, pošto se anotira bez konteksta, kroz mala vrata vratio kontekst.
- **isključene su rečenice koje je neko već video** u probnim rundama (134
  ukupno). Ko je rečenicu već ocenio, za nju nije nezavisan anotator.

Sva tri člana anotirala su isti skup, nezavisno i bez međusobnih konsultacija.

### Saglasnost pre razgovora

| par | slaganje | Koenova kapa |
|---|---|---|
| Aleksa — Anica | 85.1% | 0.686 |
| Aleksa — Dimitrije | 79.4% | 0.580 |
| Anica — Dimitrije | 86.9% | 0.733 |

| mera | vrednost |
|---|---|
| prosek parnih kapa | **0.666** |
| Fajsova kapa | 0.665 |
| Kripendorfova alfa | 0.666 |

Sve tri mere daju praktično istu vrednost, što znači da rezultat ne zavisi od
izbora mere. Izvorni rad prijavljuje 0.51 na istom koraku.

Neslaganja je bilo **85 od 350 (24.3%)**.

### Razlika u pragu

Udeo subjektivnih oznaka razlikovao se između anotatora (36.6%, 40.0% i 46.3%), a
matrice konfuzije pokazale su da neslaganje nije simetrično: između dva anotatora
sa najvećom razlikom bilo je 53 slučaja u jednom smeru naspram 19 u drugom. To
je rešavano razgovorom, a ne novim pravilom.

### Saglasnost po podskupovima

Saglasnost je merena i zasebno na podskupovima koje pojedina pravila uređuju. Na
rečenicama unutar navoda bila je izrazito niska (0.096 na 34 rečenice), ali je
taj podskup premali da bi vrednost bila pouzdana i navodi se samo kao naznaka.
Pitanja i rečenice sa diskursnim konektorima bili su ispod praga od 20 rečenica,
pa za njih mera nije računata.

---

## 4. Runda usaglašavanja

Svih 85 spornih rečenica pregledano je zajednički. Za svaku je upisana dogovorena
oznaka i pravilo koje je odlučuje; ako nijedno pravilo ne odgovara, to se beležilo.

| pravilo | broj | |
|---|---:|---|
| P4 — mišljenje u tvrdnoj formi | 17 | |
| P6 — tuđi iskaz | 16 | |
| P7 — bez sopstvenog stava | 14 | |
| P1 — evaluativni epitet | 13 | |
| P3 — književan stil | 6 | |
| P10 — ironija | 6 | |
| P5 — pripisane namere | 5 | |
| P13 — izmišljen navod | 3 | |
| P14 — autorovo sećanje | 2 | |
| P9 — pitanje | 1 | |
| bez pravila** | 2 | kandidati za dopunu |

**Uputstvo pokriva 97.6% spornih slučajeva.** Dve rečenice koje nijedno pravilo
ne rešava nisu bile dovoljan razlog za novu verziju uputstva.

---

## 5. Glavna runda

Preostalih 2.780 rečenica podeljeno je na tri jednaka dela, po oko 927 po
članu tima. Podela poštuje tri pravila:

- **deli se po članku, ne po rečenici** — svih osam rečenica jednog teksta ide
  istom anotatoru, da dvoje ne bi nezavisno označavali susedne rečenice istog
  članka;
- **uravnoteženo po izvoru i žanru**, da niko ne dobije deo koji je sav iz jednog
  lista ili sav vesti;
- **niko ne dobija rečenice koje je već video** u probnoj rundi.

---

## 6. Rezultat

Konačni skup ima 3.128 označenih rečenica iz 406 članaka. 

| oznaka | broj | udeo |
|---|---:|---:|
| SUBJ | 1.327 | 42,4% |
| OBJ | 1.801 | 57,6% |

Neravnoteža klasa je blaža nego u uporedivim korpusima (engleski 61:39,
italijanski 76:24), što je posledica svesnog uzorkovanja u korist kolumni.

### Udeo subjektivnih rečenica po izvoru i žanru

| izvor | kolumna | vest |
|---|---|---|
| blic | 88% (56) | 10% (443) |
| danas | 72% (363) | 10% (139) |
| n1info | 69% (479) | 17% (201) |
| politika | 58% (320) | 16% (200) |
| rts | 59% (117) | 12% (184) |
| vreme | 60% (432) | 13% (194) |

Žanr se pokazao kao pouzdan pokazatelj kod svih šest izvora.

---

## 7. Provera tematske izbalansiranosti

Provera je sprovedena posle anotacije, na stvarnim oznakama.

| provera | hi-kvadrat | Cramerovo V | tumačenje |
|---|---|---|---|
| žanr × oznaka | χ²(1) = 879,4 | 0,530 | očekivano visoko — to je sama pojava |
| izvor × oznaka | χ²(5) = 205,5 | 0,256 | |
| izvor × oznaka, unutar kolumni | χ²(5) = 38,5 | 0,148 | n = 1.767 |
| izvor × oznaka, unutar vesti | χ²(5) = 9,5 | 0,084 | n = 1.361 |
| **tema × oznaka** | χ²(5) = 42,3 | **0,116** | **tema ne predviđa oznaku** |

Vrednost 0,116 je ispod praga slabe povezanosti, što znači da klasifikator ne može da ostvari dobar rezultat tako što prepoznaje temu.
