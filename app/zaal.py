"""De vergaderkamer: korte filmpjes van de robots voor het wachtscherm (eenmalig gemaakt met Kling)."""
import json

import requests

from . import kling as KL
from .models import Media, ZaalClip

BASIS = ("Keep the exact same meeting room, camera position, lighting and the exact same five cartoon robots "
         "(left: green robot with a cap and binoculars; orange robot with a beret and a camera lens as head; "
         "middle back: small yellow robot with a bell on its head; blue robot with a magnifying glass and clipboard; "
         "right: golden robot with a turquoise bow tie and a pencil). Friendly Pixar-like animation, smooth, cheerful. ")
SCENES = [
    ("overleg", "The robots chat lively with each other around the table, gesturing with their hands and nodding, as in a friendly team meeting."),
    ("speurder", "The green robot on the left raises its binoculars and looks out of the window, then turns back to the table with a happy discovery."),
    ("regisseur", "The orange robot with the camera head turns its lens across the table as if filming, and gestures like a film director giving directions."),
    ("pling", "The small yellow robot in the middle rings the bell on its head with a little bounce and waves cheerfully."),
    ("analist", "The blue robot studies the clipboard through its magnifying glass, nods slowly and points at something on the paper."),
    ("boekhouder", "The golden robot with the bow tie writes notes with its pencil, then looks up and smiles contentedly."),
    ("koffie", "The robots pick up their coffee mugs and take a sip together; steam rises gently from the mugs. Relaxed, cozy moment."),
    ("klaar", "All five robots turn toward the camera, smile and give a small nod together, as if saying: done!"),
]


def start_alles(db, image_url: str):
    for scene, tekst in SCENES:
        prompt = BASIS + tekst
        try:
            job = KL.start(KL.ECHT_MODEL, image_url, prompt)
            db.add(ZaalClip(scene=scene, prompt=prompt, kling=json.dumps(job), status="bezig"))
        except Exception as ex:
            db.add(ZaalClip(scene=scene, prompt=prompt, status="mislukt", kling=json.dumps({"fout": str(ex)[:300]})))
    db.commit()


def bijwerken(db, company_id: int):
    """Kijkt bij fal.ai of de filmpjes klaar zijn; zo ja, haalt ze op en bewaart ze zelf."""
    for c in db.query(ZaalClip).filter(ZaalClip.status == "bezig").all():
        try:
            job = json.loads(c.kling or "{}")
        except ValueError:
            job = {}
        KL.stand(job)
        c.kling = json.dumps(job)
        if job.get("status") == "klaar":
            try:
                r = requests.get(job["url"], timeout=120)
                r.raise_for_status()
                m = Media(company_id=company_id, mime="video/mp4", data=r.content)
                db.add(m)
                db.flush()
                c.token, c.status = m.token, "klaar"
            except Exception as ex:
                print("Zaalfilmpje ophalen mislukt:", ex)
        elif job.get("status") == "mislukt":
            c.status = "mislukt"
    db.commit()


def clips(db) -> list:
    return [c.token for c in db.query(ZaalClip).filter(ZaalClip.status == "klaar", ZaalClip.actief == True)
            .order_by(ZaalClip.id).all() if c.token]
