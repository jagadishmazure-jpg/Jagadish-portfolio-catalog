(function () {
  var state = { fw: "", ind: "", skill: "", lvl: "" };
  var q = document.getElementById("q"), cards = [].slice.call(document.querySelectorAll("#grid .card, #enterprise-agents .card"));
  var count = document.getElementById("count");
  var projectTotal = document.querySelectorAll("#grid .card").length;
  var agentTotal = document.querySelectorAll("#enterprise-agents .card").length;
  function apply() {
    var words = q.value.toLowerCase().split(/\s+/).filter(Boolean), shown = 0, agents = 0;
    cards.forEach(function (c) {
      var ok = (!state.fw || c.dataset.fw === state.fw) &&
        (!state.ind || c.dataset.ind.split(" ").indexOf(state.ind) >= 0) &&
        (!state.skill || c.dataset.skill.split("|").indexOf(state.skill) >= 0) &&
        (!state.lvl || c.dataset.lvl === state.lvl) &&
        words.every(function (w) { return c.dataset.text.indexOf(w) >= 0; });
      c.style.display = ok ? "" : "none";
      if (ok) { if (c.classList.contains("agent")) agents++; else shown++; }
    });
    var a = agents + (agents === 1 ? " agent" : " agents"), p = shown + (shown === 1 ? " project" : " projects");
    count.textContent = projectTotal ? p + (agentTotal ? ", " + a : "") : a;
    var sec = document.getElementById("enterprise-agents");
    if (sec) sec.style.display = agents ? "" : "none";
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
