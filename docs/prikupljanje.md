# Skup podataka

---

## 1. Izvori podataka

Skup podataka čine rečenice iz tekstova šest srpskih novinskih izvora: `rts.rs`, `n1info.rs`, `vreme.com`, `danas.rs`, `blic.rs` i `politika.rs`. Izbor je pravljen tako da obuhvati različite tipove izdanja: javni servis, informativnu televiziju, nedeljnik i dnevne listove.

Iz svakog izvora prikupljane su dve vrste tekstova:

- **izveštajni tekstovi** (vesti), kao pretežno objektivan materijal;
- **autorski tekstovi** (kolumne, komentari, uvodnici, polemike, kritike), kao materijal u kome se očekuje veći udeo subjektivnih rečenica.

Anotacija se, u skladu sa propozicijama projekta, ne deli po izvorima nego ravnomerno po svim članovima tima nad spojenim skupom.

---

## 2. Prikupljanje podataka

### 2.1 Postupak i poštovanje pravila sajtova

Pre prikupljanja je za svaki sajt pročitan `robots.txt` i postupak je usklađen sa navedenim ograničenjima. U svim zahtevima korišćen je `User-Agent` koji identifikuje projekat i sadrži kontakt adresu. Sirov HTML svakog članka keširan je lokalno, tako da ponovna obrada nije zahtevala nova preuzimanja.

Prikupljanje je izvedeno u dva odvojena koraka. U prvom koraku prikupljani su samo metapodaci (URL, datum, naslov, rubrika), bez teksta članaka. Tek nakon uzorkovanja (odeljak 3) preuzimani su celi tekstovi izabranih članaka. Time je broj zahteva prema sajtovima sveden na najmanju meru.

---

## 3. Uzorkovanje

### 3.1 Motivacija

Pri izboru članaka posebna pažnja posvećena je tome da tema teksta ne bude povezana sa žanrom. Ako bi, na primer, većina autorskih tekstova bila o politici, a većina izveštajnih o crnoj hronici, klasifikator bi mogao da nauči razliku između tema umesto razlike u subjektivnosti, uz visoke rezultate u validaciji koji ne bi govorili ništa o traženom zadatku.

### 3.2 Postupak

Da bi se to izbeglo, uzorkovanje je izvedeno u dva koraka:

1. Prvo su uzorkovani **autorski tekstovi** i njima je ručno dodeljena tema. Uzorkovano je 108 kandidata, od kojih je 14 pri ručnoj proveri prepoznato kao izveštajni tekst i isključeno, pa je ostalo **94 kolumne**.
2. Zatim su uzorkovane **vesti** tako da preslikavaju tematsku raspodelu dobijenu u prvom koraku. Izabrano je **54 izveštajna teksta**.

Unutar svake teme uzorkovanje je dodatno raspoređeno na oba izvora, kako izvor ne bi postao zamena za oznaku žanra. Uzorkovanje je vremenski raslojeno: kandidati su podeljeni na četiri jednaka vremenska intervala i iz svakog je uzet jednak broj članaka, čime je izbegnuto da korpus bude uzorak jednog kratkog perioda i jednog vesti-ciklusa.

Uzorkovanje je izvedeno sa fiksiranim generatorom slučajnih brojeva, pa je postupak u potpunosti ponovljiv.

### 3.3 Izbor rečenica unutar članka

Iz svakog članka nije uzet ceo tekst, već blok od **8 uzastopnih rečenica**, sa slučajno izabranom početnom pozicijom.

Ograničenje na 8 rečenica uvedeno je zato što se dužine članaka bitno razlikuju (medijana 49 rečenica za kolumne i 23 za vesti, uz najduži tekst od 136 rečenica). Bez ograničenja bi nekoliko najdužih kolumni dominiralo korpusom.

Uzastopne rečenice su izabrane zato što se subjektivnost često ne može oceniti iz izolovane rečenice, pa anotator mora da vidi okolinu; uz to je uz skup sačuvan i pun tekst svakog članka, dostupan anotatoru na uvid.

Slučajan početak prozora uveden je zato što se subjektivnost ne raspoređuje ravnomerno kroz tekst: autorski tekstovi po pravilu počinju činjeničnim uvodom, a stav se javlja i pojačava kasnije, dok izveštajni tekstovi prate obrnutu piramidu. Uzimanje prvih 8 rečenica bi sistematski favorizovalo objektivne delove teksta.

---

## 4. Format zapisa

Skup je sačuvan kao UTF-8 tekstualni fajl sa tabulatorom kao separatorom, sa kolonama: `sentence_id`, `source`, `article_id`, `genre`, `topic`, `category`, `sent_idx`, `n_clean`, `url`, `text`. Identifikator rečenice ima oblik `<izvor>-<id_clanka>-<redni_broj>`, čime je jedinstven u celom skupu. Uz skup se čuva i datoteka sa punim tekstovima svih članaka, kako bi anotatori imali uvid u kontekst.
