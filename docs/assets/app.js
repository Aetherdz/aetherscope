(function () {
  "use strict";

  var lines = [
    "$ aetherscope -s scope.txt check api.example.com",
    "api.example.com: in-scope  [*.example.com]",
    "$ aetherscope -s scope.txt check secret.example.com",
    "secret.example.com: out-of-scope  [!secret.example.com]",
    "$ printf 'api.example.com\\nexternal.net\\n' | aetherscope -s scope.txt filter",
    "api.example.com",
    "$ aetherscope -s scope.txt check 10.0.0.9",
    "10.0.0.9: in-scope  [10.0.0.0/24]",
  ];

  var typedEl = document.getElementById("typed");
  var cursorEl = document.querySelector(".cursor");
  if (!typedEl || !cursorEl) {
    return;
  }

  var lineIndex = 0;
  var charIndex = 0;
  var deleting = false;

  function tick() {
    var line = lines[lineIndex];
    var text = typedEl.textContent;

    if (!deleting) {
      if (charIndex < line.length) {
        typedEl.textContent = text + line.charAt(charIndex);
        charIndex += 1;
        setTimeout(tick, 16);
      } else {
        deleting = true;
        setTimeout(tick, 900);
      }
    } else {
      if (text.length > 0) {
        typedEl.textContent = text.slice(0, -1);
        setTimeout(tick, 8);
      } else {
        deleting = false;
        charIndex = 0;
        lineIndex = (lineIndex + 1) % lines.length;
        setTimeout(tick, 300);
      }
    }
  }

  if (cursorEl) {
    cursorEl.style.display = "inline-block";
  }
  setTimeout(tick, 600);
})();
