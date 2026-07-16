(function () {
  "use strict";

  // --- trend chart (chronological, oldest -> newest) --------------------------
  const rowsChronological = [...window.HDI_HISTORY_ROWS].reverse();
  const ctx = document.getElementById("trendChart");
  if (ctx && rowsChronological.length) {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: rowsChronological.map((r) => (r.label || `#${r.id}`)),
        datasets: [{
          label: "Predicted HDI",
          data: rowsChronological.map((r) => r.predicted_hdi),
          borderColor: "#C9A227",
          backgroundColor: "rgba(201,162,39,0.12)",
          pointBackgroundColor: rowsChronological.map(
            (r) => window.HDI_TIER_COLORS[r.predicted_tier] || "#333"
          ),
          pointRadius: 4,
          fill: true,
          tension: 0.25,
        }],
      },
      options: {
        scales: {
          y: { min: 0, max: 1, title: { display: true, text: "HDI" } },
          x: { ticks: { maxRotation: 45, minRotation: 0 } },
        },
        plugins: { legend: { display: false } },
      },
    });
  }

  // --- tier filtering -----------------------------------------------------------
  const filterBtns = document.querySelectorAll(".tier-filter-btn");
  const tableRows = document.querySelectorAll("#ledgerTable tbody tr");
  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tier = btn.dataset.tier;
      tableRows.forEach((row) => {
        row.style.display = tier === "all" || row.dataset.tier === tier ? "" : "none";
      });
    });
  });

  // --- delete single row ----------------------------------------------------------
  document.querySelectorAll(".row-delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      if (!confirm("Delete this prediction from history?")) return;
      const res = await fetch(`/api/history/${id}`, { method: "DELETE" });
      if (res.ok) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) row.remove();
      }
    });
  });

  // --- clear all ------------------------------------------------------------------
  const clearBtn = document.getElementById("clearHistoryBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", async () => {
      if (!confirm("Clear ALL prediction history? This cannot be undone.")) return;
      const res = await fetch("/api/history/clear", { method: "POST" });
      if (res.ok) window.location.reload();
    });
  }
})();
