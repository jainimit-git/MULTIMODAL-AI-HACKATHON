// frontend/app.js
// This script wires the HTML dashboard to the FastAPI backend.
// It loads the default Trishuli case study on page load, populates the Leaflet map
// with GeoJSON layers, updates KPI cards, handles the Copilot chat UI, Judge mode execution,
// settlement list rendering, situation report view, EMSR927 validation display, and DEM flow‑path tracing.

// ==== Global State ==== 
let analysisResult = null; // will hold the full JSON returned by the backend
let map = null;
let layerGroups = {};

// ==== Utility Functions ====
function fetchJson(url, options = {}) {
  return fetch(url, { headers: { "Content-Type": "application/json" }, ...options })
    .then((resp) => {
      if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      return resp.json();
    })
    .catch((err) => console.error("Fetch error:", err));
}

function addGeoJsonLayer(name, data, style) {
  if (!map) return;
  if (layerGroups[name]) {
    map.removeLayer(layerGroups[name]);
  }
  const layer = L.geoJSON(data, { style, onEachFeature: (f, l) => l.bindTooltip(f.properties?.name || "") });
  layerGroups[name] = layer;
  if (document.getElementById(`layer${name.charAt(0).toUpperCase() + name.slice(1)}`).checked) {
    layer.addTo(map);
  }
}

function updateKPIs() {
  if (!analysisResult) return;
  const infra = analysisResult.infrastructure_metrics || {};
  const net = analysisResult.network_metrics?.summary || {};

  document.getElementById("kpiCutoff").textContent = net.cut_off_settlements_count ?? "--";
  document.getElementById("kpiPopulation").textContent = net.isolated_population ?? "--";
  document.getElementById("kpiArea").textContent = (analysisResult.flood_metrics?.total_affected_area_km2 ?? "--") + " km²";
  document.getElementById("kpiPolygons").textContent = analysisResult.geojson_layers?.flood_polygons?.features?.length ?? "--";
  document.getElementById("kpiRoads").textContent = infra.affected_roads_km ?? "--";
  document.getElementById("kpiRoadPercent").textContent = (infra.percent_roads_affected ?? "--") + "%";
  document.getElementById("kpiBridges").textContent = infra.affected_bridges ?? "--";
  document.getElementById("kpiBuildings").textContent = infra.affected_buildings ?? "--";
}

function renderSettlements() {
  const listDiv = document.getElementById("settlementsList");
  listDiv.innerHTML = "";
  const settlements = analysisResult.network_metrics?.settlements ?? [];
  settlements.forEach((s) => {
    const el = document.createElement("div");
    el.className = "settlement-item";
    el.textContent = `${s.name} – ${s.is_cut_off ? "CUT OFF" : "CONNECTED"} (Pop: ${s.population || "-"})`;
    listDiv.appendChild(el);
  });
}

function loadSitrep() {
  const viewer = document.getElementById("sitrepViewer");
  viewer.textContent = analysisResult.situation_report_md || "No report available";
}

function loadValidation() {
  const div = document.getElementById("validationMetrics");
  if (!div) return; // optional placeholder in HTML
  const val = analysisResult.validation_benchmark?.metrics;
  if (!val) {
    div.textContent = "No validation benchmark available.";
    return;
  }
  div.innerHTML = `IoU: ${val.intersection_over_union_iou.toFixed(3)}<br>
    Dice/F1: ${val.dice_f1_score.toFixed(3)}<br>
    Precision: ${val.precision.toFixed(3)}<br>
    Recall: ${val.recall.toFixed(3)}`;
}

function initMap() {
  map = L.map("map").setView([28.0, 85.3], 9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  // click handler for flow‑path tracing
  map.on("click", (e) => {
    computeFlowPath(e.latlng.lat, e.latlng.lng);
  });
}

function computeFlowPath(lat, lon) {
  fetchJson("/api/dem/flow-path", {
    method: "POST",
    body: JSON.stringify({ lat, lon }),
  }).then((result) => {
    if (!result || !result.flow_path_geojson) return;
    addGeoJsonLayer("flowPath", result.flow_path_geojson, { color: "#00BFFF", weight: 3 });
    // optionally display exposed settlements count
    alert(`Flow path generated – ${result.exposed_settlements_count} settlements intersected.`);
  });
}

// ==== Copilot UI ==== 
function appendMessage(role, text) {
  const container = document.getElementById("copilotMessages");
  const div = document.createElement("div");
  div.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = text.replace(/\n/g, "<br>");
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function askCopilot(question) {
  appendMessage("user", question);
  fetchJson("/api/copilot/chat", {
    method: "POST",
    body: JSON.stringify({ message: question }),
  }).then((resp) => {
    const answer = resp?.answer || resp?.message || "[No response]";
    appendMessage("assistant", answer);
  });
}

function sendCopilotQuery() {
  const input = document.getElementById("copilotInput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";
  askCopilot(q);
}

// ==== Judge Mode ==== 
function handleJudgeSubmit(event) {
  event.preventDefault();
  const bbox = document.getElementById("judgeBbox").value.split(",").map(Number);
  const date = document.getElementById("judgeDate").value;
  const name = document.getElementById("judgeName").value;

  const progress = document.getElementById("executionProgress");
  progress.style.display = "block";

  fetchJson("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ bbox, event_date: date, event_name: name }),
  })
    .then((resp) => {
      analysisResult = resp.data || resp; // fallback for older schema
      loadAnalysis();
    })
    .finally(() => {
      progress.style.display = "none";
    });
}

function copySitrep() {
  const txt = analysisResult?.situation_report_md || "";
  navigator.clipboard.writeText(txt).then(() => alert("SitRep copied to clipboard"));
}

// ==== Layer Toggle Handlers ==== 
function setupLayerToggles() {
  const layers = ["Flood", "Roads", "Severed", "Settlements", "FlowPath"];
  layers.forEach((name) => {
    const cb = document.getElementById(`layer${name}`);
    if (!cb) return;
    cb.addEventListener("change", () => {
      if (cb.checked) {
        if (layerGroups[name.toLowerCase()]) layerGroups[name.toLowerCase()].addTo(map);
      } else {
        if (layerGroups[name.toLowerCase()]) map.removeLayer(layerGroups[name.toLowerCase()]);
      }
    });
  });
}

// ==== Main Loader ==== 
function loadAnalysis() {
  if (!analysisResult) return;
  // GeoJSON layers expect keys matching backend output names
  const layers = analysisResult.geojson_layers || {};
  addGeoJsonLayer("flood", layers.flood_polygons, { color: "#FF4500", fillOpacity: 0.4 });
  addGeoJsonLayer("roads", layers.annotated_roads, { color: "#2E8B57" });
  addGeoJsonLayer("severed", layers.annotated_roads, { color: "#B22222", dashArray: "5,5" }); // same source, style differs
  addGeoJsonLayer("settlements", layers.settlements, { color: "#006400", radius: 5 });
  if (layers.flow_path) addGeoJsonLayer("flowPath", layers.flow_path, { color: "#00BFFF", weight: 3 });

  updateKPIs();
  renderSettlements();
  loadSitrep();
  loadValidation();
}

// ==== Initialization ==== 
window.addEventListener("load", () => {
  initMap();
  setupLayerToggles();
  // Load default Trishuli case study
  fetchJson("/api/case-study/trishuli").then((data) => {
    analysisResult = data;
    loadAnalysis();
  });
});

