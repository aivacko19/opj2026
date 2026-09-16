# Dekoderski modeli: srpski vs engleski

Model za svaku rečenicu daje jednu od dve oznake, OBJ ili SUBJ. Za svaku klasu posebno se računa F1 — mera koliko dobro model pogađa BAŠ TU klasu, koja u sebi kombinuje dve stvari:

precision (preciznost): od svih rečenica koje je model označio kao SUBJ, koliki procenat je zaista SUBJ (koliko puta je model "lažno uzbunio")
recall (odziv): od svih rečenica koje su zaista SUBJ, koliki procenat je model uspeo da prepozna (koliko je "propustio")
F1 je kombinacija ta dva broja — loš je ako model bilo previđa prave SUBJ rečenice, bilo pogrešno proglašava OBJ rečenice za SUBJ.

F1-OBJ = koliko dobro model pogađa objektivne rečenice
F1-SUBJ = koliko dobro pogađa subjektivne
macro-F1 = prosek ta dva broja, sa jednakom težinom
Zašto baš prosek, a ne običan procenat tačnih pogodaka (accuracy)? Zato što u korpusu ima više OBJ nego SUBJ rečenica (otprilike 1755 : 1327, tj. 57% : 43%). Da smo gledali samo accuracy, model koji uvek kaže "OBJ" bio bi "tačan" u 57% slučajeva a da nikad nije prepoznao nijednu subjektivnu rečenicu — accuracy bi to sakrio, macro-F1 ne bi, jer bi F1-SUBJ pao na 0 i prosek bi to pokazao.


Izveštaj: ChatGPT vs Gemini, srpski vs engleski upit


 Testirane su 4 konfiguracije po modelu: jezik upita (srpski/engleski) × broj primera u upitu (nula/osam), nad 3120 označenih rečenica (8 few-shot primera isključeno iz ocenjivanja). Nijedan poziv nije propao ili dao nevažeću oznaku, ni na srpskom ni na engleskom — obe stvari su potpuno čiste.


Rezultati (macro-F1):

| model | sr-zero (referenca) | en-zero | sr-few | en-few |
|---|---|---|---|---|
| ChatGPT (gpt-4.1) | 0.822 | 0.832 | 0.814 | 0.826 |
| Gemini (gemini-3.8-flash) | 0.858 | 0.851 | 0.862 | 0.855 |



Glavni nalaz — efekat jezika upita zavisi od modela:

Kod ChatGPT-a, engleski upit daje malo bolje rezultate (+0.009 do +0.012 macro-F1).
Kod Gemini-ja, srpski upit daje malo bolje rezultate (–0.007 kod oba).
Efekat je suprotnog smera kod dva modela, i u oba slučaja mali (oko 1 poen macro-F1) - da je testiran samo jedan model, zaključak bi bio pogrešno uopšten na "jezik upita". Ovim je potvrđeno da razlika nije osobina zadatka nego osobina konkretnog modela, tačno ono što je uputstvo tražilo da se proveri.

Sporedan nalaz: Gemini je dosledno bolji od ChatGPT-a na ovom zadatku, nezavisno od jezika ili broja primera (macro-F1 ~0.85–0.86 naspram ~0.81–0.83).