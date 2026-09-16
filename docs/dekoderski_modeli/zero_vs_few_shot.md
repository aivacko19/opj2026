# Dekoderski modeli: Efekat primera u upitu
---

## 1. Postavka

Dva modela, po četiri konfiguracije upita: jezik upita (srpski / engleski) ×
broj primera (nula / osam). Oznake su u svim upitima `OBJ` i `SUBJ`, tako da se
između uslova menja samo jedna stvar. Osam primera je fiksirano (4 OBJ, 4 SUBJ),
birano da pokrije pravila kod kojih granica nije očigledna (P1–P7, P13); tih
osam rečenica je isključeno iz ocene. Zlatne oznake potvrđuju sve oznake
primera (8/8).

| model | tačan identifikator | nivo | neuspelih grupa |
|---|---|---|---|
| ChatGPT | `gpt-4.1` | OpenAI API (Anica) | 0 / 209 u sve četiri konfiguracije |
| Gemini | `gemini-3.8-flash` | Gemini API, uključena naplata | 0 / 209 u sve četiri konfiguracije |

Rečenice su slate u grupama od 15, `temperature = 0`; ukupno 3.122 rečenice po
konfiguraciji, 209 poziva po konfiguraciji. Ni jedan odgovor nije završio kao
`PARSE_FAIL`: ni jedan model ni na srpskom ni na engleskom upitu nije odbio
format.

Tok rada za Gemini, radi ponovljivosti. Prvi pokušaj sa `gemini-3.1-pro`
vraćao je 404 (model nije dostupan preko API-ja); Pro model koji je bio
dostupan radio je, ali prespor za naš obim (procena 16 sati) i skup, pa je
posle 31 grupe odbačen (`cache_llm/gemini-sr-zero_old.jsonl`) i sve četiri
konfiguracije su pokrenute ispočetka sa `gemini-3.8-flash`. Konfiguracije
`sr-zero` i `sr-few` završene su preko noći sa jednom niti; u `en-zero` je 10
grupa dobilo 429 (prekoračen mesečni limit potrošnje projekta), limit je
podignut, a te grupe su automatski ponovljene pri sledećem pokretanju. Ostatak
je završen sa 8 paralelnih niti za nekoliko minuta. Ukupno 893.763 ulaznih i
85.492 izlaznih tokena za sve četiri konfiguracije; cena reda nekoliko dolara.

Ocena je rađena na **3.120 rečenica** koje imaju zlatnu oznaku i predikciju u
svih osam konfiguracija (3.128 zlatnih, minus 8 few-shot primera). Sve
konfiguracije se porede sa `sr-zero`. Pošto se konfiguracije porede na *istim*
rečenicama, koristi se **Meknemarov test** (tačan binomni test nad rečenicama na
kojima je samo jedna od dve konfiguracije tačna), a za Δ makro F1 upareni
bootstrap po rečenicama (2.000 uzoraka, 95% interval).

---

## 2. Rezultati

| model | upit | makro F1 | F1 SUBJ | F1 OBJ | tačnost | κ vs zlato | predviđeno SUBJ |
|---|---|---|---|---|---|---|---|
| gpt-4.1 | `sr-zero` (ref) | 0,822 | 0,788 | 0,857 | 0,829 | 0,645 | 38,2% |
| gpt-4.1 | `sr-few` | 0,814 | 0,778 | 0,849 | 0,821 | 0,628 | 38,4% |
| gpt-4.1 | `en-zero` | 0,832 | 0,798 | 0,865 | 0,838 | 0,664 | 37,8% |
| gpt-4.1 | `en-few` | 0,826 | 0,790 | 0,862 | 0,833 | 0,653 | 37,1% |
| gemini-3.8-flash | `sr-zero` (ref) | 0,858 | 0,836 | 0,880 | 0,862 | 0,716 | 42,3% |
| gemini-3.8-flash | `sr-few` | 0,862 | 0,841 | 0,883 | 0,865 | 0,724 | 42,5% |
| gemini-3.8-flash | `en-zero` | 0,851 | 0,831 | 0,871 | 0,854 | 0,702 | 44,1% |
| gemini-3.8-flash | `en-few` | 0,855 | 0,834 | 0,876 | 0,858 | 0,710 | 43,0% |

Udeo SUBJ u zlatu je 42,4%. Poređenja radi, referentni osnovni model iz track A
(logistička regresija, `w1-tfidf-lower`) ima makro F1 0,681 u grupisanoj
validaciji, a saglasnost među anotatorima pre usaglašavanja bila je κ = 0,666.

### Razlika u odnosu na `sr-zero`

| model | upit | Δ makro F1 | 95% CI | samo ref tačno / samo cfg tačno | Meknemar p |
|---|---|---|---|---|---|
| gpt-4.1 | `sr-few` | −0,009 | [−0,016, −0,000] | 88 / 62 | **0,041** |
| gpt-4.1 | `en-zero` | +0,009 | [+0,000, +0,018] | 84 / 113 | **0,046** |
| gpt-4.1 | `en-few` | +0,004 | [−0,005, +0,013] | 87 / 101 | 0,343 |
| gemini-3.8-flash | `sr-few` | +0,004 | [−0,002, +0,010] | 41 / 52 | 0,300 |
| gemini-3.8-flash | `en-zero` | −0,007 | [−0,015, −0,001] | 75 / 50 | **0,031** |
| gemini-3.8-flash | `en-few` | −0,003 | [−0,010, +0,004] | 65 / 54 | 0,359 |

### Efekat primera (few − zero), unutar istog jezika

| model | jezik | Δ makro F1 | Δ F1 SUBJ | Δ F1 OBJ | promenjeno oznaka | SUBJ→OBJ / OBJ→SUBJ | Meknemar p |
|---|---|---|---|---|---|---|---|
| gpt-4.1 | sr | −0,009 | −0,010 | −0,007 | 150 (4,8%) | 72 / 78 | **0,041** |
| gpt-4.1 | en | −0,006 | −0,008 | −0,003 | 163 (5,2%) | 93 / 70 | 0,273 |
| gemini-3.8-flash | sr | +0,004 | +0,005 | +0,003 | 93 (3,0%) | 43 / 50 | 0,300 |
| gemini-3.8-flash | en | +0,004 | +0,003 | +0,005 | 88 (2,8%) | 61 / 27 | 0,165 |

---

## 3. Tumačenje

**Osam primera u upitu ne pomaže.** Efekat je kod oba modela i oba jezika u
opsegu od −0,009 do +0,004 makro F1, a jedina statistički značajna razlika je
*negativna* (ChatGPT, srpski upit, p = 0,041). Kod Geminija je promena pozitivna
ali nije značajna (p = 0,30 i 0,17), a 95% interval za srpski upit
[−0,002, +0,010] obuhvata nulu. Zaključak
važi za oba modela, pa nije osobina jednog modela nego upita: ovih osam
primera, sa opisima iz uputstva, ne prenosi modelu ništa što nije već dobio iz
definicije zadatka.

Način na koji primeri menjaju odluke je poučniji od samog proseka. Primeri
promene 3–5% oznaka. Na srpskom upitu promene idu **u oba smera podjednako**
(ChatGPT 72 rečenice iz SUBJ u OBJ naspram 78 obrnuto, Gemini 43 naspram 50),
pa se udeo predviđenih SUBJ ne pomera (+0,2 procentna poena kod oba). Na
engleskom upitu primeri blago guraju ka OBJ (ChatGPT 93 naspram 70, Gemini 61
naspram 27; udeo SUBJ −0,7 i −1,1 poena), ali ni to ne popravlja rezultat.
U oba slučaja je od promenjenih oznaka približno jednak broj ispravnih i
pogrešnih (ChatGPT sr: 62 popravljene naspram 88 pokvarenih; Gemini sr: 52
naspram 41). To je ponašanje koje bismo očekivali od šuma, ne od naučene
granice. Jedan mogući
razlog je što su primeri birani po *pravilu* koje ilustruju, a ne po tome
gde model greši; primeri koji bi ciljali stvarne greške modela (vidi ispod)
možda bi imali efekta, ali to je drugačiji eksperiment.

**Da li primeri više pomažu na engleskom nego na srpskom? Ne.** Kod ChatGPT-a
je efekat primera na engleskom (−0,006) približno isti kao na srpskom (−0,009),
kod Geminija identičan (+0,004 i +0,004). Nema interakcije jezika i primera:
model razume zadatak podjednako iz oba jezika upita, a primeri ni na jednom ne
dodaju granicu koja bi nedostajala.

**Jezik upita jeste imao mali ali dosledan efekat, suprotnog smera kod dva
modela.** ChatGPT je bolji sa engleskim upitom (+0,009 zero, +0,012 few; p = 0,046
i 0,005), Gemini sa srpskim (−0,007 u oba slučaja; p = 0,031 i 0,045). Razlike
su reda 0,01 makro F1 i menjaju 3,5–6,3% oznaka; nisu dovoljno velike da bi
išta menjale u praksi, ali pokazuju da jezik uputstva nije potpuno neutralan i
da smer zavisi od modela. Ni jedan model nije imao neuspelih odgovora na
srpskom upitu, pa bojazan da bi srpski upit češće izazivao lomljenje formata
nije potvrđena.

**Razlika između modela je veća od razlike između upita.** Gemini je bolji od
ChatGPT-a za 0,02–0,05 makro F1 u svakoj konfiguraciji, i to gotovo isključivo
na klasi SUBJ: ChatGPT propušta 332 od 1.323 subjektivnih rečenica (recall
0,75), Gemini 218 (0,84), dok su lažno pozitivni približno isti (202 naspram
214). ChatGPT je konzervativniji — predviđa SUBJ za 38% rečenica naspram 42%
u zlatu — i to je izvor njegovog zaostatka. Dva modela se međusobno slažu sa
κ = 0,72–0,76, više nego što su se slagali anotatori (0,67).

**Gde oba modela greše.** Makro F1 je kod oba modela i svih konfiguracija za
0,03–0,08 niži na vestima (0,70–0,76) nego na kolumnama (0,77–0,82). Vesti sa
subjektivnom rečenicom su ređe (10–17% po izvoru), pa je klasa SUBJ tamo
neuravnotežena, a subjektivnost u vesti je po pravilu diskretnija (ograda,
izbor reči) nego otvoreni stav u kolumni.

---

## 4. Sažetak za izveštaj

- Osam primera u upitu ne popravlja rezultat ni jednom modelu ni na jednom
  jeziku upita (Δ makro F1 od −0,009 do +0,004; jedina značajna razlika je
  negativna). Primeri promene 3–5% oznaka, ali u oba smera podjednako i bez
  pomeranja udela SUBJ.
- Ne postoji interakcija jezika i primera: efekat primera je isti na srpskom i
  engleskom.
- Jezik upita ima mali (≈0,01) ali značajan efekat, suprotnog smera kod dva
  modela: ChatGPT bolji na engleskom, Gemini na srpskom.
- Oba modela u nultom režimu nadmašuju referentni osnovni model za 0,14–0,18
  makro F1 (0,82–0,86 naspram 0,68) i postižu κ prema zlatu (0,63–0,72) uporediv sa
  saglasnošću anotatora (0,67). Gemini je bolji od ChatGPT-a za ≈0,03,
  zahvaljujući većem odzivu na klasi SUBJ.
- Tačni identifikatori: `gpt-4.1`, `gemini-3.8-flash`; 0 neuspelih grupa
  kod oba, na oba jezika upita.

## 5. Ograničenja

- Zlatne oznake su za 89% korpusa jednostruke (2.778 od 3.128 rečenica; samo
  350 kalibracionih ima tri anotacije), pa deo neslaganja modela sa zlatom
  pripada anotatoru, ne modelu. κ modela prema zlatu (0,72)
  iznad κ među anotatorima (0,67) treba čitati u tom svetlu.
- Ispitan je samo jedan skup od osam primera i jedan način njihovog izbora (po
  pravilu). Zaključak „primeri ne pomažu" važi za taj skup; nije isključeno da
  bi drugačije birani ili brojniji primeri imali efekta.
- Rečenice su slate u grupama od 15 iz uzastopnih prozora, pa model unutar
  grupe vidi susedne rečenice istog članka, tj. neki kontekst koji anotatori
  po uputstvu nisu koristili. To je isto za sve konfiguracije, pa ne utiče na
  poređenja, ali utiče na apsolutne vrednosti.
