(function () {
  var state = { fw: "", ind: "", skill: "" };
  var q = document.getElementById("q"), cards = [].slice.call(document.querySelectorAll("#grid .card"));
  var count = document.getElementById("count");
  function apply() {
    var words = q.value.toLowerCase().split(/\s+/).filter(Boolean), shown = 0;
    cards.forEach(function (c) {
      var ok = (!state.fw || c.dataset.fw === state.fw) &&
        (!state.ind || c.dataset.ind.split(" ").indexOf(state.ind) >= 0) &&
        (!state.skill || c.dataset.skill.split("|").indexOf(state.skill) >= 0) &&
        words.every(function (w) { return c.dataset.text.indexOf(w) >= 0; });
      c.style.display = ok ? "" : "none"; if (ok) shown++;
    });
    count.textContent = shown + (shown === 1 ? " project" : " projects");
  }
  document.querySelectorAll(".chip").forEach(function (b) {
    b.addEventListener("click", function () {
      state[b.dataset.group] = b.dataset.val;
      document.querySelectorAll('.chip[data-group="' + b.dataset.group + '"]').forEach(function (x) { x.classList.toggle("on", x === b); });
      apply();
    });
  });
  q.addEventListener("input", apply);
})();
