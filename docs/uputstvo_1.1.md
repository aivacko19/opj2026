# Uputstvo za anotaciju: subjektivnost na nivou rečenice

**Projekat:** Klasifikacija subjektivnosti u srpskim novinskim tekstovima
**Verzija:** 1.1 (usklađeno sa primarnim izvorom, pre kalibracije)

> **Osnov.** Definicija oznaka i podela na specifične slučajeve preuzete su iz rada
> Antici et al. (2024), *A Corpus for Sentence-Level Subjectivity Detection on English
> News Articles* (LREC-COLING 2024, korpus NewsSD-ENG). Ista uputstva korišćena su i
> u CheckThat! zadatku za detekciju subjektivnosti. Pravila P1–P12 su naša
> operacionalizacija tih smernica na srpskom materijalu; mesta na kojima odstupamo
> od izvora izričito su označena.

---

## 1. Zadatak i oznake

Svaka rečenica dobija tačno jednu od dve oznake:

| Oznaka | Značenje |
|---|---|
| `SUBJ` | Rečenica iznosi stav, ocenu, doživljaj ili pretpostavku **autora teksta**. |
| `OBJ` | Rečenica iznosi tvrdnju o stvarnosti, prenosi tuđi iskaz ili ne sadrži autorov stav. |

Oznaka se odnosi na **glas autora teksta**, ne na sadržaj rečenice. Rečenica može biti puna oštrih ocena i svejedno biti `OBJ`, ako te ocene pripadaju nekom koga autor citira.

---

## 2. Postupak odlučivanja

Za svaku rečenicu postavite dva pitanja, ovim redosledom.

### Pitanje 1: Ko tvrdi ono što piše u rečenici?

- Ako tvrdnja pripada autoru teksta → idi na Pitanje 2.
- Ako je tvrdnja preneta od nekog drugog (navod, parafraza sa atribucijom) → **OBJ**, bez obzira na to koliko je sam iskaz subjektivan.

### Pitanje 2: Mogu li se dve dobro obaveštene osobe ne složiti oko ovoga, a da nijedna ne greši u činjenicama?

- **Da** → `SUBJ`. Neslaganje je moguće jer je reč o oceni, doživljaju ili tumačenju.
- **Ne** → `OBJ`. Neslaganje bi značilo da neko pogrešno zna činjenicu.

> **Važno:** ne krećite od reči. Pojedine reči (`zavidan`, `zastrašujuće`) jesu dokaz za `SUBJ`, ali su dokaz, a ne test. Ako anotirate tako što tražite „subjektivne reči", svako od nas će tražiti različite reči i saglasnost će biti niska. Prvo odgovorite na dva pitanja, pa tek onda proverite da li vas reči u rečenici u tome potvrđuju.

---

## 3. Šta se pri odlučivanju NE uzima u obzir

Sve navedeno je nebitno za oznaku:

- **Tema rečenice.** Politika nije subjektivnija od sporta.
- **Da li je tvrdnja tačna.** Netačna činjenična tvrdnja je i dalje `OBJ`.
- **Da li se vi slažete sa autorom.** Anotira se prisustvo stava, ne njegova ispravnost.
- **Žanr članka.** Kolumna sadrži i objektivne rečenice, i to mnogo njih. Vest može sadržati subjektivnu rečenicu. Nikada ne pretpostavljajte oznaku na osnovu toga odakle je tekst.
- **Ko je autor** i kakav je njegov ugled.
- **Stil pisanja.** Književan, ritmičan ili slikovit izraz nije sam po sebi stav (vidi pravilo P3).

---

## 4. Pravila za karakteristične slučajeve

Primeri su stvarne rečenice iz našeg korpusa; u zagradi je `sentence_id`.

### P1 — Evaluativni epiteti → SUBJ

Pridev ili imenica koja **ocenjuje ili rangira**, a ne opisuje, čini rečenicu subjektivnom čak i kada je sve ostalo činjenično.

> „U tom pravcu 'Kobre' već imaju **zavidan** minuli rad." (`vre-4937773-010`) → **SUBJ**
> „...jeste **zastrašujuća** novina." (`pol-773254-006`) → **SUBJ**
> „...uz svu tu **kriminalnu** prednost koju režim pribavlja..." (`vre-5008147-018`) → **SUBJ**

Razlika: `visok` (merljivo) opisuje, `zavidan` (ocenjuje) ne opisuje. `Razrušen` opisuje, `sraman` ocenjuje.

### P2 — Ograda i nepreciznost same po sebi nisu subjektivnost

Nije bitno da li se autor ograđuje, nego **da li spekulacija izvodi zaključak**.

| Slučaj | Oznaka |
|---|---|
| Spekulacija koja ostavlja pitanje otvorenim | `OBJ` |
| Zaključak potkrepljen nelično iznetom činjenicom ili pretpostavkom | `OBJ` |
| Približna vrednost (`skoro`, `oko`, `manje-više`) | `OBJ` |
| Spekulacija kojom autor izvodi sopstveni zaključak | `SUBJ` |

> „Vajfertova pivara sada je **skoro** razrušena..." (`vre-4977044-018`) → **OBJ**

> „Pošto mu mandat ističe 31. maja 2027, njihovo održavanje **vjerojatnije** je krajem
> ove godine." (`vre-4999756-012`) → **OBJ**. Zaključak počiva na navedenoj činjenici
> (istek mandata), a ne na autorovom tumačenju.

**Ali:** ograda ne poništava ocenu. U rečenici `vre-5008147-018` oznaka `SUBJ` dolazi
od `kriminalnu prednost` (P1), a ne od reči `deluje`.


### P3 — Stil nije subjektivnost → OBJ

Književni ritam, nabrajanje, metafora upotrebljena opisno. Pitajte se šta se tvrdi, ne kako zvuči.

**Izuzetak:** retorička figura, pre svega hiperbola, kojom autor prenosi svoj stav →
`SUBJ`. Razlika je u tome da li figura ukrašava tvrdnju ili je nosilac ocene.

> „Štede na svemu – hrani, obući, odjeći, sredstvima za higijenu." (`vre-4970392-008`) → **OBJ**
> „To je ambicija koja je započela pre više od decenije i sada je nadomak ostvarenja." (`vre-4969017-005`) → **OBJ**

Obe rečenice zvuče „literarno", ali obe tvrde nešto što se može proveriti.

### P4 — Mišljenje u tvrdnoj formi → SUBJ

Gramatički oblik obične tvrdnje ne znači da je sadržaj činjeničan. Ovde Pitanje 2 radi ceo posao.

> „...pa im je ilustrovanje onoga o čemu čitaju **nepotrebno**." (`vre-4965741-005`) → **SUBJ**
> „Šira slika (mada ni to nije cela) je sledeća..." (`vre-4918461-009`) → **SUBJ**

### P5 — Pripisivanje namera, osećanja i unutrašnjih stanja → SUBJ

Kada autor tvrdi šta neko oseća, namerava ili u čemu uživa, a ta osoba to nije rekla, reč je o autorovom tumačenju.

> „Njegov govor tijela odaje duboko frustriranog čovjeka koji uživa u patnji drugih..." (`vre-4936342-006`) → **SUBJ**

Dva izuzetka:

- unutrašnje stanje koje je **preneto** („Rekao je da je razočaran") → `OBJ`, po P6;
- **autorova sopstvena osećanja**, kada su ona sadržaj rečenice a ne ocena nečeg
  drugog („Iznenadilo me je koliko me je ceremonija dirnula") → `OBJ`. Deluje
  neintuitivno, ali autor je pouzdan izvor o sopstvenim osećanjima, pa takva rečenica
  iznosi činjenicu o autoru, a ne stav o temi. Ako uz osećanje ide i ocena teme,
  odlučuje ocena.

### P6 — Tuđi iskaz → OBJ

Navod ili parafraza sa atribucijom je `OBJ`, ma koliko sam iskaz bio subjektivan. Autor ga prenosi, ne iznosi.

> „'Niko u njemu ne vidi Petera Mađara, osim tebe, izgubljeni dragi Danasu', napisala je ona, uz emotikon." (`pol-782395-003`) → **OBJ**

Ako autor uz navod doda sopstvenu ocenu **u istoj rečenici**, rečenica postaje `SUBJ`. Ocena u susednoj rečenici ne utiče na ovu.

**Višerečenični navodi.** Kada navod traje više rečenica, podela na rečenice uklanja navodnike sa svih osim prve i poslednje. U pretprocesiranju su navodnici vraćeni, pa je svaka rečenica navoda prepoznatljiva i bez uvida u ceo tekst. Kolona `in_quote` dodatno označava takve rečenice.

### P7 — Rečenice bez sopstvenog sadržaja → OBJ

Ako rečenica sama po sebi ne izražava stav, označava se kao `OBJ`, čak i kada je iz konteksta jasno da autor nastavlja svoju argumentaciju.

> „Tako je bilo i sada." (`pol-759883-066`) → **OBJ**

**Obrazloženje, pročitati pažljivo.** Model vidi samo rečenicu. Ako oznaku izvedemo iz prethodne rečenice, dodeljujemo oznaku koja se iz ulaza ne može naučiti, i time unosimo šum koji nijedan model ne može da savlada. Kontekst koristimo da **razumemo** rečenicu, nikada da joj **dodamo** stav koji u njoj ne postoji.

Praktična posledica: u kolumnama će biti dosta `OBJ` rečenica. To je ispravno i očekivano.

### P8 — Diskursni konektori vs. evaluativni prilozi  `[dodato]`

| Ne računaju se kao dokaz | Računaju se kao dokaz za SUBJ |
|---|---|
| `naravno`, `dakle`, `uostalom`, `naime`, `zapravo`, `inače` | `nažalost`, `srećom`, `na sreću`, `neverovatno`, `apsurdno` |

Leva kolona povezuje rečenicu sa tokom teksta. Desna govori šta autor misli o onome što opisuje.

> „Psihologija, **naravno**, ima jasnu dijagnozu za osobe lišene emocija." (`vre-5012460-016`) → **OBJ**

Pravilo se primenjuje doslovno: konektor nikada nije dovoljan razlog za `SUBJ`. Ako u rečenici postoji drugi razlog, on odlučuje.

### P9 — Pitanja

Prepišite pitanje kao tvrdnju i pogledajte šta autor podrazumeva pod odgovorom.

- Podrazumevani odgovor postoji i **evaluativan je** → `SUBJ`.
- Podrazumevanog odgovora nema, ili je činjeničan → `OBJ`.

> „Da, ali zašto ga je onda druga strana prihvatila?" (`pol-768048-006`)
> Prepisano: „Nema dobrog razloga da ga druga strana prihvati." → **SUBJ**

> „Šta se zapravo dogodilo te noći?" kao najava činjeničnog opisa → **OBJ** (pitanje strukturira tekst).
> „Kada očekujete rezultate?" u intervjuu → **OBJ**.
> Pitanje unutar tuđeg navoda → `OBJ`, po P6.

### P10 — Ironija i sarkazam → SUBJ

Ako je doslovno značenje suprotno od onoga što autor misli, rečenica izražava stav. Vidi `vre-4937773-010`, gde je `zavidan` upotrebljen ironično.

### P11 — Poziv na delanje → SUBJ

Rečenica u kojoj autor iznosi šta bi **trebalo** da se uradi, ili čemu se nada.

> „Zapad bi morao brže da naoruža Ukrajinu." → **SUBJ**
> „Vreme je da se konačno raspiše konkurs." → **SUBJ**

### P12 — Nadimci, titule, poslovice → OBJ

Ustaljen nadimak ili titula (`orlovi`, `beli`, `prvi čovek stranke`) i poslovica ili
ustaljen izraz ne čine rečenicu subjektivnom, čak i kada zvuče vrednosno.


---

## 5. Nedoumice

Uvek upišite oznaku, i onda kada niste sigurni. Ne ostavljajte prazno polje.

Ako ste oklevali duže od nekoliko sekundi, u kolonu `nedoumica` upišite `Y`, a u kolonu `napomena` napišite **šta je bilo teško**, ne šta ste odlučili.

- Korisno: „prenosi tuđi stav, ali autor dodaje ocenu"
- Beskorisno: „nejasno"

Rečenice sa `Y` se ne rešavaju u hodu. Skupljaju se i razmatraju zajedno, posle svake runde. Ako se isti razlog javi tri puta, u uputstvo ide novo pravilo.

---

## 6. Format zapisa

Anotira se u alatu koji uz rečenicu prikazuje i tekst članka. Izlaz je TSV, UTF-8, sa kolonama:

```
sentence_id    label    nedoumica    napomena    annotator
```

`label` je isključivo `SUBJ` ili `OBJ`. `annotator` je vaše ime, radi razdvajanja kalibracionih fajlova.

---

## 7. Kalibracija i postupak anotacije

### Anotira se bez konteksta

Rečenica se ocenjuje **sama za sebe**. Alat prikazuje i ceo članak, ali se on otvara
samo kada rečenica bez njega nije razumljiva (nejasna zamenica, nedostaje referent),
nikada da bi se odlučila oznaka.

Ovo nije stvar ukusa. U izvornom radu je to izmereno: grupa koja je anotirala uz
kontekst postigla je saglasnost 0.38, a grupa koja je gledala samo rečenicu 0.53.
Objašnjenje je da anotatori češće označe nejasnu rečenicu kao subjektivnu kada je
okružena očigledno subjektivnima. Finalni korpus u tom radu anotiran je bez konteksta.

### Očekivane vrednosti saglasnosti

Zadatak je težak i niska sirova saglasnost je normalna. U izvornom radu saglasnost
na celom korpusu bila je **0.51** posle nezavisne anotacije i **0.83** posle
razgovora o spornim rečenicama, pri čemu je treći anotator bio potreban u manje od
10% slučajeva.

Zato ne merimo samo jednu vrednost, nego dve, i obe idu u izveštaj.

### Postupak

1. **Kalibracioni skup.** Sve troje anotiramo isti skup od oko 350 rečenica (10%
   korpusa), nezavisno i bez međusobnih konsultacija. Rečenice iz probne runde su
   isključene.
2. **Merenje pre razgovora.** Koenova kapa za svaki par (tri para), prosek te tri
   vrednosti, Fajsova kapa za grupu, i matrica konfuzije po parovima — da bismo
   videli *koje* razlike prave problem, a ne samo koliko ih ima.
3. **Razgovor.** Prolazimo kroz sve rečenice oko kojih postoji neslaganje i kroz sve
   označene sa `nedoumica`. Ako se isti razlog javi tri puta, u uputstvo ide novo
   pravilo i verzija se podiže.
4. **Merenje posle razgovora**, na istom skupu.
5. **Glavna runda.** Korpus se deli na tri jednaka dela. Sporne rečenice se i dalje
   označavaju sa `nedoumica` i rešavaju zajednički.


## 8. Odstupanja od izvornih smernica

Pravila P1–P7 i P9–P12 odgovaraju slučajevima iz izvornog rada (SUBJ 1–5 i Case 1–7),
prilagođenim srpskom materijalu i ilustrovanim primerima iz našeg korpusa.

**P8 je naš dodatak.** Izvorne smernice ne razmatraju diskursne konektore. Uvodimo ga
jer se `naravno`, `dakle` i `uostalom` u srpskom novinarstvu javljaju vrlo često, a
anotatori bez izričitog pravila reaguju na njih nedosledno. Pravilo je namerno strogo
(konektor nikada nije dovoljan razlog za `SUBJ`), jer je doslednost u anotaciji
važnija od pokrivanja retkih slučajeva u kojima `naravno` zaista nosi stav.

Posle kalibracije proveravamo da li je dodatak pomogao: računamo saglasnost zasebno
na rečenicama koje sadrže neki od konektora iz P8 i poredimo je sa saglasnošću na
ostatku skupa. Rezultat te provere, kakav god bio, ide u izveštaj.

---

## 9. Podsetnica

**Dva pitanja:** Ko tvrdi? → Može li se neko ne složiti bez greške u činjenicama?

| | |
|---|---|
| Evaluativni epitet (`zavidan`, `sraman`) | **SUBJ** |
| Približnost i ograda (`skoro`, `verovatno`, `deluje`) | **OBJ** |
| Književan stil, nabrajanje, ritam | **OBJ** |
| Mišljenje u obliku obične tvrdnje | **SUBJ** |
| Pripisane namere i osećanja | **SUBJ** |
| Navod ili parafraza sa atribucijom | **OBJ** |
| Rečenica bez sopstvenog stava | **OBJ** |
| `naravno`, `dakle`, `uostalom` | nije dokaz |
| `nažalost`, `srećom` | **SUBJ** |
| Pitanje sa evaluativnim podrazumevanim odgovorom | **SUBJ** |
| Ironija, sarkazam | **SUBJ** |
| Poziv na delanje (*trebalo bi, mora se*) | **SUBJ** |
| Autorova sopstvena osećanja kao sadržaj | **OBJ** |
| Nadimak, titula, poslovica | **OBJ** |

**Zapamtiti:** ocenjuje se rečenica sama za sebe, bez konteksta. Kolumna sadrži i objektivne rečenice. Tema ne odlučuje. Tačnost ne odlučuje. Vaše slaganje sa autorom ne odlučuje.
