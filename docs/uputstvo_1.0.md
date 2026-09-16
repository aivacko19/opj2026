# Uputstvo za anotaciju: subjektivnost na nivou rečenice

**Projekat:** Klasifikacija subjektivnosti u srpskim novinskim tekstovima
**Verzija:** 1.0 (nacrt pre kalibracije)

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

### P2 — Nepreciznost i ograda nisu subjektivnost → OBJ

Dve pojave koje se često mešaju sa stavom:

- **Približnost:** `skoro`, `oko`, `manje-više`, `blizu`.
- **Nesigurnost:** `verovatno`, `deluje`, `čini se`, `izgleda`, `moguće je`.

Obe se odnose na činjenicu koju autor ne zna tačno. To je i dalje tvrdnja o stvarnosti.

> „Vajfertova pivara sada je **skoro** razrušena..." (`vre-4977044-018`) → **OBJ**
> „...njihovo održavanje **vjerojatnije** je krajem ove, nego u rano proljeće naredne godine." (`vre-4999756-012`) → **OBJ**

**Ali:** ograda ne poništava ocenu. Ako je ono što se ograđuje evaluativno, rečenica ostaje `SUBJ`. U rečenici `vre-5008147-018` oznaka `SUBJ` dolazi od `kriminalnu prednost` (P1), a ne od reči `deluje`.

### P3 — Stil nije subjektivnost → OBJ

Književni ritam, nabrajanje, metafora upotrebljena opisno. Pitajte se šta se tvrdi, ne kako zvuči.

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

Izuzetak: ako je unutrašnje stanje **preneto** („Rekao je da je razočaran") → `OBJ`, po P6.

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

### P8 — Diskursni konektori vs. evaluativni prilozi

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

## 7. Kalibracija

Sve troje anotiramo **isti** skup od oko 350 rečenica (10% korpusa), **nezavisno i bez međusobnih konsultacija**. Rečenice iz probne runde su iz kalibracionog skupa isključene.

Posle toga se računa:

- Koenova kapa za svaki par anotatora (tri para),
- prosek te tri vrednosti,
- Fajsova kapa za celu grupu,
- matrica konfuzije po parovima, da bismo videli **koje** razlike prave problem, a ne samo koliko ih ima.

Ciljna vrednost je kapa iznad 0.6. Ako je niža, uputstvo se dopunjuje i kalibracija ponavlja na novom uzorku. Obe vrednosti, pre i posle dopune, idu u izveštaj.

---

## 8. Podsetnica

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

**Zapamtiti:** kolumna sadrži i objektivne rečenice. Tema ne odlučuje. Tačnost ne odlučuje. Vaše slaganje sa autorom ne odlučuje.
