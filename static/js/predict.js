(function () {
  "use strict";

  const fields = ["life_exp", "expected_schooling", "mean_schooling", "gni"];

  // --- "load a real country" autofill --------------------------------------
  const countrySelect = document.getElementById("countrySelect");
  countrySelect.addEventListener("change", () => {
    if (countrySelect.value === "") return;
    const country = window.HDI_COUNTRIES[Number(countrySelect.value)];
    if (!country) return;

    const map = {
      life_exp: country.life_exp.toFixed(1),
      expected_schooling: country.expected_schooling.toFixed(1),
      mean_schooling: country.mean_schooling.toFixed(1),
      gni: Math.round(country.gni),
    };
    fields.forEach((name) => {
      document.getElementById(name).value = map[name];
    });
    document.getElementById("label").value = country.country;
  });

  // --- gauge chart (half-doughnut) ------------------------------------------
  let gaugeChart = null;
  function renderGauge(value, color) {
    const ctx = document.getElementById("gaugeChart");
    const data = {
      datasets: [{
        data: [value, 1 - value],
        backgroundColor: [color, "#EEE7D3"],
        borderWidth: 0,
        circumference: 180,
        rotation: 270,
        cutout: "72%",
      }],
    };
    if (gaugeChart) {
      gaugeChart.data = data;
      gaugeChart.update();
    } else {
      gaugeChart = new Chart(ctx, {
        type: "doughnut",
        data,
        options: {
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          animation: { duration: 500 },
          events: [],
        },
      });
    }
  }

  const tierNotes = {
    "Very High": "This scenario matches nations with strong, well-rounded development outcomes.",
    "High": "Solid development overall, with room to close gaps against the top tier.",
    "Medium": "A developing profile &mdash; targeted gains in health, education, or income would lift this further.",
    "Low": "Indicates significant development challenges across one or more dimensions.",
  };

  // --- submit handler ---------------------------------------------------------
  const form = document.getElementById("predictForm");
  const btn = document.getElementById("predictBtn");
  const placeholder = document.getElementById("resultPlaceholder");
  const content = document.getElementById("resultContent");
  const errorBox = document.getElementById("resultError");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.innerHTML = "";
    btn.disabled = true;
    btn.textContent = "Predicting…";

    const payload = {
      life_exp: document.getElementById("life_exp").value,
      expected_schooling: document.getElementById("expected_schooling").value,
      mean_schooling: document.getElementById("mean_schooling").value,
      gni: document.getElementById("gni").value,
      label: document.getElementById("label").value,
    };

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (!res.ok) {
        errorBox.innerHTML = `<div class="error-banner">${data.error || "Something went wrong. Please check your inputs."}</div>`;
        placeholder.style.display = "block";
        content.style.display = "none";
        return;
      }

      placeholder.style.display = "none";
      content.style.display = "block";

      document.getElementById("gaugeValue").textContent = data.hdi.toFixed(3);
      const badge = document.getElementById("tierBadge");
      badge.textContent = data.tier;
      badge.style.background = data.tier_color;
      document.getElementById("tierNote").innerHTML = tierNotes[data.tier] || "";
      renderGauge(data.hdi, data.tier_color);
    } catch (err) {
      errorBox.innerHTML = `<div class="error-banner">Network error &mdash; could not reach the prediction service.</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Predict HDI";
    }
  });
})();
