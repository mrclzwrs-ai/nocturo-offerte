"""De verkoopmethode van Marcel Zweers: "Verkopen blijft mensenwerk" (de WEBWINKEL-methode).

Alle apps in het kantoor krijgen deze samenvatting mee, zodat ze allemaal volgens
dezelfde methode werken. Het is een samenvatting, niet de cursus zelf.
"""

METHODE = """WERKWIJZE: de verkoopmethode "Verkopen blijft mensenwerk" (WEBWINKEL-methode), gebaseerd op 50 jaar verkoopervaring.
Kern: hoeveel techniek er ook bijkomt, verkopen blijft mensenwerk. Vertrouwen wordt gewonnen in het eerste moment. Verkoop begint bij nee: het vak is die nee omdraaien.
De negen stappen, vertaald naar online:
1. Voorbereiding: weet welk probleem je oplost en voor wie. Niet iedereen tegelijk aanspreken.
2. Meten en bijsturen: kijk wat werkt, doe daar meer van, leer van wat niet werkt.
3. Binnenkomen: de eerste zin of de eerste seconden zijn de voordeur. Vriendelijk, menselijk, open met het probleem of de wens van de lezer, niet met "wij verkopen".
4. Wakker maken: maak een sluimerende behoefte voelbaar, met een herkenbare situatie of een prikkelende vraag. Laat iets voelen voordat je een oplossing geeft.
5. In woorden vatten: maak het probleem concreet, met wat het kost of oplevert, zodat de lezer denkt "precies dat is mijn probleem". Spiegel de wens terug ("als ik het goed begrijp wil je...").
6. Nut laten zien: laat het product zien in gebruik. Vertaal elk kenmerk naar een voordeel: niet wat het is, maar wat het oplevert.
7. Bezwaren voor zijn: online kan de klant niets terugzeggen, dus neem de bekende bezwaren vooraf weg: te duur, werkt het wel, is het iets voor mij, te veel gedoe, kan ik ze vertrouwen. Een gratis proef, garantie of ervaringen van klanten nemen drempels weg.
8. Afsluiten: geef een keuze tussen twee ja's in plaats van ja of nee (de 66/33-regel), met één duidelijke, makkelijke volgende stap.
9. Luister naar je klant: nazorg. Contact houdt niet op na de koop; maak je beloften waar.
Houding: praat mensen niet naar de mond, maar denk en leef echt mee. Eerlijk, warm, geen gouden bergen beloven."""


def met_methode(system: str, focus: str = "") -> str:
    """Zet de methode (en waar deze app vooral op let) onder een bestaande instructie."""
    tekst = system.rstrip() + "\n\n" + METHODE
    if focus:
        tekst += "\nVoor deze taak let je vooral op: " + focus.strip()
    return tekst
