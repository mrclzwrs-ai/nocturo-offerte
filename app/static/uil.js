/* De Nocturo-uil: ogen die kijken, lezen, volgen en knipperen. */
(function () {
  var MAX_X = 6.5, MAX_Y = 4.5, DICHT = 33;

  function Uil(svg) {
    this.svg = svg;
    this.pupillen = svg.querySelectorAll('.pupil');
    this.leden = svg.querySelectorAll('.lid');
    this.x = 0; this.y = 0; this.doelX = 0; this.doelY = 0;
    this.lid = 0; this.timers = [];
    var self = this;
    (function tik() { self._stap(); requestAnimationFrame(tik); })();
  }

  Uil.prototype._stap = function () {
    this.x += (this.doelX - this.x) * 0.18;
    this.y += (this.doelY - this.y) * 0.18;
    var tx = 'translate(' + (this.x * MAX_X).toFixed(2) + ' ' + (this.y * MAX_Y).toFixed(2) + ')';
    for (var i = 0; i < this.pupillen.length; i++) this.pupillen[i].setAttribute('transform', tx);
    var lt = 'translate(0 ' + (this.lid * DICHT).toFixed(2) + ')';
    for (var j = 0; j < this.leden.length; j++) this.leden[j].setAttribute('transform', lt);
  };

  Uil.prototype.kijk = function (x, y) {
    this.doelX = Math.max(-1, Math.min(1, x));
    this.doelY = Math.max(-1, Math.min(1, y));
  };

  Uil.prototype.knipper = function (keer) {
    var self = this; keer = keer || 1;
    self.lid = 1;
    setTimeout(function () {
      self.lid = 0;
      if (keer > 1) setTimeout(function () { self.knipper(keer - 1); }, 170);
    }, 120);
  };

  Uil.prototype._later = function (fn, ms) { this.timers.push(setTimeout(fn, ms)); };
  Uil.prototype.stop = function () { this.timers.forEach(clearTimeout); this.timers = []; this.kijk(0, 0); this.lid = 0; };

  /* af en toe knipperen, soms twee keer snel */
  Uil.prototype.knipperAfEnToe = function () {
    var self = this;
    (function plan() {
      self._later(function () { self.knipper(Math.random() < 0.3 ? 2 : 1); plan(); }, 2000 + Math.random() * 3000);
    })();
  };

  /* lezen: regel voor regel van links naar rechts, af en toe even opkijken */
  Uil.prototype.lees = function () {
    var self = this, regel = 0;
    (function zin() {
      var y = -0.2 + (regel % 3) * 0.45;
      self.kijk(-0.9, y);
      self._later(function () { self.kijk(0.9, y); }, 380);
      regel++;
      var opkijken = Math.random() < 0.2;
      self._later(function () {
        if (opkijken) { self.kijk(0, -0.9); self._later(zin, 900); } else zin();
      }, 1300);
    })();
    this.knipperAfEnToe();
  };

  /* volgen: kijkt naar je vinger of muis */
  Uil.prototype.volg = function () {
    var self = this, rust;
    function naar(px, py) {
      var r = self.svg.getBoundingClientRect();
      var cx = r.left + r.width / 2, cy = r.top + r.height * 0.6;
      var dx = px - cx, dy = py - cy, afstand = Math.max(1, Math.hypot(dx, dy));
      var kracht = Math.min(1, afstand / 250);
      self.kijk(dx / afstand * kracht, dy / afstand * kracht);
      clearTimeout(rust);
      rust = setTimeout(function () { self.kijk(0, 0); }, 2500);
    }
    window.addEventListener('pointermove', function (e) { naar(e.clientX, e.clientY); }, { passive: true });
    window.addEventListener('pointerdown', function (e) { naar(e.clientX, e.clientY); }, { passive: true });
    window.addEventListener('touchstart', function (e) { var t = e.touches[0]; if (t) naar(t.clientX, t.clientY); }, { passive: true });
    this.knipperAfEnToe();
  };

  window.NocturoUil = Uil;
})();
