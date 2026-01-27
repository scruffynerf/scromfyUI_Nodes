/**
 * CivSearch Image Browser - ComfyUI Custom Node Frontend
 * Uses Civitai's multi-search API (Meilisearch)
 * Follows same pattern as Civitai and Genur browsers
 */

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// ----- SECTION: Constants -----
const EXT_NAME = "CivSearchImageBrowser.InfiniteScroll";
const DISPLAY_NAME = "🔍 CivSearch Image Browser";
const TARGET_CLASS = "CivSearchImageBrowser";
const COLORS = { neon: "#22d3ee", neon2: "#a78bfa" };

const SORT_OPTIONS = ["Relevancy", "Most Reactions", "Most Discussed", "Most Collected", "Most Buzz", "Newest"];
const NSFW_OPTIONS = ["None (SFW only)", "Soft", "Mature", "X"];
const ASPECT_RATIOS = ["Any", "Landscape", "Portrait", "Square"];
const MEDIA_TYPES = ["Any", "image", "video"];
// BASE_MODELS removed - fetching from API

// ----- SECTION: Utilities -----
const qs = (o) => Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
const getJSON = async (path) => { const r = await api.fetchApi(path); if (!r.ok) throw new Error(`${r.status}`); return r.json(); };
const keyId = (id) => String(id);
const toggleBtn = (btn, flag) => btn.classList.toggle("active", flag);

const hexToRgba = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
};

const formatJsonHtml = (obj, indent = 0) => {
    const pad = "  ".repeat(indent);
    if (obj === null) return `<span class="json-null">null</span>`;
    if (typeof obj === "boolean") return `<span class="json-bool">${obj}</span>`;
    if (typeof obj === "number") return `<span class="json-number">${obj}</span>`;
    if (typeof obj === "string") {
        const escaped = obj.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        const display = escaped.length > 500 ? escaped.slice(0, 500) + "..." : escaped;
        return `<span class="json-string">"${display}"</span>`;
    }
    if (Array.isArray(obj)) {
        if (obj.length === 0) return "[]";
        const items = obj.map(v => pad + "  " + formatJsonHtml(v, indent + 1)).join(",\n");
        return `[\n${items}\n${pad}]`;
    }
    if (typeof obj === "object") {
        const keys = Object.keys(obj);
        if (keys.length === 0) return "{}";
        const items = keys.map(k => `${pad}  <span class="json-key">"${k}"</span>: ${formatJsonHtml(obj[k], indent + 1)}`).join(",\n");
        return `{\n${items}\n${pad}}`;
    }
    return String(obj);
};

// ----- SECTION: Widget Helpers -----
function sanitizeProxyWidgets(props) {
    if (!props || typeof props !== "object" || Array.isArray(props)) return { proxyWidgets: [] };
    if ("proxyWidget" in props && !("proxyWidgets" in props)) { props.proxyWidgets = props.proxyWidget; delete props.proxyWidget; }
    if (!("proxyWidgets" in props)) { props.proxyWidgets = []; return props; }
    const v = props.proxyWidgets;
    if (Array.isArray(v)) return props;
    if (v == null) props.proxyWidgets = [];
    else if (typeof v === "string") {
        const s = v.trim();
        if (!s) props.proxyWidgets = [];
        else if (s.startsWith("[") && s.endsWith("]")) { try { props.proxyWidgets = JSON.parse(s); } catch { props.proxyWidgets = [s]; } }
        else props.proxyWidgets = [s];
    } else props.proxyWidgets = [];
    return props;
}

function removeSelectionPort(node) {
    try { if (!Array.isArray(node.inputs)) return; const idx = node.inputs.findIndex((i) => i && i.name === "selection_data"); if (idx >= 0) node.removeInput(idx); } catch { }
}

function hideWidgetDom(widget) {
    try {
        const el = widget?.element || widget?.inputEl || widget?.textarea || widget?.wrapper || widget?.dom;
        if (el && el.style) { el.style.display = "none"; el.style.visibility = "hidden"; el.style.height = "0px"; el.style.position = "absolute"; el.style.left = "-99999px"; }
    } catch { }
}

function getOrCreateCGState(node) {
    node.properties = sanitizeProxyWidgets(node.properties || {});
    node.properties.__cg = node.properties.__cg || {};
    return node.properties.__cg;
}

function ensureHiddenSelectionWidget(node, cg) {
    removeSelectionPort(node);
    let wSel = (node.widgets || []).find((w) => w?.name === "selection_data");
    if (!wSel) {
        wSel = node.addWidget("text", "selection_data", typeof cg.selection_data === "string" ? cg.selection_data : "{}", (v) => {
            cg.selection_data = typeof v === "string" ? v : String(v ?? "{}");
            try { app?.graph?.change?.(); } catch { }
            node.setDirtyCanvas(true, true);
        }, { multiline: true });
    }
    wSel.serializeValue = () => (typeof cg.selection_data === "string" ? cg.selection_data : "{}");
    wSel.draw = function () { };
    wSel.computeSize = () => [0, 0];
    hideWidgetDom(wSel);
    if (typeof wSel.value !== "string") wSel.value = typeof cg.selection_data === "string" ? cg.selection_data : "{}";
    return wSel;
}

// ----- SECTION: CSS Generation -----
const generateCSS = (uid) => {
    const neon = COLORS.neon, neon2 = COLORS.neon2;
    return `
#${uid}{height:100%;width:100%;box-sizing:border-box}
#${uid} .cg-root{height:100%;display:flex;flex-direction:column;gap:10px;color:var(--node-text-color);font-family:ui-sans-serif,system-ui;overflow:hidden;--cg-neon:${neon};--cg-neon2:${neon2};--cg-chip-bg:rgba(255,255,255,.06);--cg-surface:rgba(20,20,30,.55);--cg-border:rgba(255,255,255,.12);--cg-shadow:0 10px 30px rgba(0,0,0,.35);background:radial-gradient(1200px 400px at -10% -10%,${hexToRgba(neon, 0.10)},transparent 70%),radial-gradient(900px 300px at 120% -20%,${hexToRgba(neon2, 0.08)},transparent 60%);border-radius:14px}
#${uid} .cg-header{position:relative;padding:10px 12px;border-radius:14px;background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid var(--cg-border);box-shadow:var(--cg-shadow)}
#${uid} .cg-title{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-weight:700}
#${uid} .cg-title .dot{width:10px;height:10px;border-radius:50%;background:radial-gradient(closest-side,var(--cg-neon),transparent);box-shadow:0 0 12px var(--cg-neon)}
#${uid} .cg-sub{opacity:.7;font-size:12px}
#${uid} .cg-controls{display:flex;flex-direction:column;gap:6px;margin-top:8px}
#${uid} .cg-row{display:flex;align-items:center;gap:6px;flex-wrap:nowrap}
#${uid} .cg-input,#${uid} .cg-select{padding:6px 8px;border:1px solid var(--cg-border);background:var(--cg-surface);color:var(--node-text-color);border-radius:8px;height:28px;backdrop-filter:blur(8px);font-size:11px}
#${uid} .cg-input{flex:1;min-width:60px}
#${uid} .cg-select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--cg-neon) 50%),linear-gradient(135deg,var(--cg-neon) 50%,transparent 50%);background-position:calc(100% - 12px) calc(50% + 2px),calc(100% - 8px) calc(50% + 2px);background-size:5px 5px;background-repeat:no-repeat;padding-right:22px}
#${uid} .cg-btn{padding:6px 10px;border:1px solid var(--cg-border);background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border-radius:8px;cursor:pointer;transition:.18s;box-shadow:var(--cg-shadow);white-space:nowrap;color:var(--node-text-color);font-size:11px}
#${uid} .cg-btn:hover{filter:brightness(1.08)}
#${uid} .cg-btn.toggle.active{box-shadow:0 0 0 1px ${hexToRgba(neon, 0.35)} inset;outline:2px solid var(--cg-neon)}
#${uid} .cg-scroll{flex:1;min-height:0;overflow:auto;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,.01));border:1px solid var(--cg-border);padding:10px;box-shadow:var(--cg-shadow);overflow-anchor:none;overscroll-behavior:contain}
#${uid} .cg-scroll::-webkit-scrollbar{width:10px}
#${uid} .cg-scroll::-webkit-scrollbar-thumb{background:linear-gradient(var(--cg-neon),var(--cg-neon2));border-radius:10px}
#${uid} .cg-masonry{column-gap:12px;--colw:200px;column-width:var(--colw)}
#${uid} .cg-card{display:inline-block;width:100%;margin:0 0 12px;border:1px solid var(--cg-border);border-radius:14px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02));position:relative;break-inside:avoid;opacity:0;transform:translateY(6px);transition:opacity .18s,transform .18s;box-shadow:var(--cg-shadow)}
#${uid} .cg-card.show{opacity:1;transform:translateY(0)}
#${uid} .cg-card:hover{box-shadow:0 0 24px ${hexToRgba(neon, 0.13)},var(--cg-shadow)}
#${uid} .cg-card.selected{outline:2px solid var(--cg-neon);outline-offset:-2px}
#${uid} .cg-img,#${uid} .cg-vid{width:100%;height:auto;display:block;background:#0e0f13}
#${uid} .cg-vid{max-height:72vh}
#${uid} .cg-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 10px}
#${uid} .cg-meta-left{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
#${uid} .cg-chip{font-size:10px;background:var(--cg-chip-bg);border:1px solid var(--cg-border);padding:2px 6px;border-radius:999px}
#${uid} .cg-chip.nsfw{background:rgba(255,100,100,.2);border-color:rgba(255,100,100,.4);color:#ff9999}
#${uid} .cg-chip.video{background:rgba(220,38,38,.3);border-color:rgba(220,38,38,.5);color:#fca5a5}
#${uid} .cg-star{border:none;background:transparent;font-size:18px;cursor:pointer;color:#8b8b8b;transition:.15s}
#${uid} .cg-star:hover{transform:scale(1.06)}
#${uid} .cg-star.fav{color:#ffd970;text-shadow:0 0 8px rgba(255,217,112,.35)}
#${uid} .cg-foot{display:flex;align-items:center;gap:10px;flex-shrink:0;padding:8px 10px;border:1px solid var(--cg-border);border-radius:14px;background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));box-shadow:var(--cg-shadow)}
#${uid} .cg-status{font-size:11px;opacity:.8}
#${uid} .cg-sentinel{width:100%;height:1px}
#${uid} .cg-toggle-render.cg-render-on{color:#22c55e;border-color:#22c55e66}
#${uid} .cg-toggle-render.cg-render-off{color:#ef4444;border-color:#ef444466}
#${uid} .cg-scroll.paused,#${uid} .cg-foot.paused{display:none!important}
#${uid} .cg-modal-overlay{position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.75);display:none;z-index:1000;backdrop-filter:blur(4px)}
#${uid} .cg-modal-overlay.show{display:flex;align-items:center;justify-content:center;padding:20px}
#${uid} .cg-modal{background:linear-gradient(135deg,rgba(30,30,40,.98),rgba(20,20,30,.98));border:1px solid var(--cg-border);border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.5);width:92% !important;height:82% !important;max-width:1400px !important;display:flex !important;flex-flow:row nowrap !important;overflow:hidden !important;align-items:stretch !important}
#${uid} .cg-modal-img-container{flex:0 0 60% !important;width:60% !important;min-width:0 !important;background:#050508;display:flex !important;align-items:center !important;justify-content:center !important;overflow:hidden !important;border-right:1px solid var(--cg-border)}
#${uid} .cg-modal-img-container img,#${uid} .cg-modal-img-container video{max-width:100% !important;max-height:100% !important;object-fit:contain !important;display:block !important}
#${uid} .cg-modal-content{flex:0 0 40% !important;width:40% !important;min-width:350px !important;display:flex !important;flex-direction:column !important;overflow:hidden !important;background:rgba(0,0,0,0.2)}
#${uid} .cg-modal-header{padding:12px 16px;border-bottom:1px solid var(--cg-border);display:flex !important;align-items:center !important;justify-content:space-between !important;background:rgba(255,255,255,0.03);flex:0 0 auto !important}
#${uid} .cg-modal-title{font-weight:600;font-size:14px;color:var(--cg-neon)}
#${uid} .cg-modal-close{background:none !important;border:none !important;font-size:32px !important;cursor:pointer !important;color:var(--node-text-color) !important;opacity:.7 !important;transition:0.2s !important}
#${uid} .cg-modal-close:hover{opacity:1 !important;color:#ef4444 !important;transform:scale(1.1)}
#${uid} .cg-modal-body{padding:16px;overflow-y:auto !important;flex:1 1 0% !important;min-height:0 !important}
#${uid} .cg-modal-json{font-family:ui-monospace,monospace;font-size:11px;line-height:1.5;white-space:pre-wrap;word-break:break-word;color:#e0e0e0}
#${uid} .cg-modal-json .json-key{color:#9cdcfe}
#${uid} .cg-modal-json .json-string{color:#ce9178}
#${uid} .cg-modal-json .json-number{color:#b5cea8}
#${uid} .cg-modal-json .json-bool,#${uid} .cg-modal-json .json-null{color:#569cd6}
#${uid} .cg-modal-actions{padding:12px 16px;border-top:1px solid var(--cg-border);display:flex;gap:8px;flex-shrink:0 !important}
#${uid} .cg-modal-actions .cg-btn{flex:1}
`;
};

// ----- SECTION: HTML Templates -----
const makeSelect = (cls, opts) => `<select class="cg-select ${cls}">${opts.map(o => `<option value="${o}">${o}</option>`).join("")}</select>`;

const CONTROLS_HTML = `
<div class="cg-row">
  <input class="cg-input cg-query" placeholder="Search query...">
  ${makeSelect("cg-sort", SORT_OPTIONS)}
  <button class="cg-btn cg-search">Search</button>
</div>
<div class="cg-row">
  <select class="cg-select cg-basemodel"><option value="">Any</option></select>
  ${makeSelect("cg-mediatype", MEDIA_TYPES)}
  ${makeSelect("cg-aspect", ASPECT_RATIOS)}
  ${makeSelect("cg-nsfw", NSFW_OPTIONS)}
</div>
<div class="cg-row">
  <input class="cg-input cg-username" placeholder="Username">
  <input class="cg-input cg-tag" placeholder="Tag">
  <input class="cg-input cg-tool" placeholder="Tool">
  <input class="cg-input cg-technique" placeholder="Technique">
</div>
<div class="cg-row">
  <button class="cg-btn toggle cg-toggle-favonly">★ Favorites only</button>
  <button class="cg-btn cg-refresh">↻ Refresh</button>
  <button class="cg-btn cg-toggle-render cg-render-on">Display: ON</button>
</div>
`;

const MODAL_HTML = `
<div class="cg-modal-overlay">
  <div class="cg-modal">
    <div class="cg-modal-img-container"><img class="cg-modal-preview" src="" alt="Preview"></div>
    <div class="cg-modal-content">
      <div class="cg-modal-header"><span class="cg-modal-title">Image Details</span><button class="cg-modal-close">×</button></div>
      <div class="cg-modal-body"><div class="cg-modal-json"></div></div>
      <div class="cg-modal-actions"><button class="cg-btn cg-modal-select">Select This Image</button></div>
    </div>
  </div>
</div>
`;

// ----- SECTION: Viewport Detection -----
function isNodeOnScreen(node) {
    try {
        const va = app?.canvas?.visible_area || app?.canvas?.ds?.visible_area;
        if (!va || va.length < 4) return true;
        return node.pos[0] + node.size[0] > va[0] && node.pos[0] < va[0] + va[2] && node.pos[1] + node.size[1] > va[1] && node.pos[1] < va[1] + va[3];
    } catch { return true; }
}

// ----- SECTION: Register Extension -----
app.registerExtension({
    name: EXT_NAME,

    beforeRegisterNodeDef(nodeType, nodeData) {
        const comfyClass = (nodeType?.comfyClass || nodeData?.name || "").toString();
        if (comfyClass !== TARGET_CLASS) return;

        const _onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = _onNodeCreated?.apply(this, arguments);
            const node = this;

            node.properties = sanitizeProxyWidgets(node.properties || {});
            const cg = getOrCreateCGState(node);

            if (!cg.colored_once) { node.color = "#0a1a1a"; node.bgcolor = "#050d0d"; cg.colored_once = true; }

            removeSelectionPort(node);
            const wSel = ensureHiddenSelectionWidget(node, cg);

            const uid = `civsearch-${Math.random().toString(36).slice(2, 9)}`;
            const root = document.createElement("div");
            root.id = uid;
            root.innerHTML = `
<style>${generateCSS(uid)}</style>
<div class="cg-root">
  <div class="cg-header">
    <div class="cg-title"><span class="dot"></span><div>${DISPLAY_NAME}</div><div class="cg-sub">Meilisearch API</div></div>
    <div class="cg-controls">${CONTROLS_HTML}</div>
  </div>
  <div class="cg-scroll"><div class="cg-masonry"></div><div class="cg-sentinel"></div></div>
  <div class="cg-foot"><span class="cg-status" style="margin-left:auto"></span></div>
  ${MODAL_HTML}
</div>`;

            node.addDOMWidget("civsearch_images", "div", root, {});
            node.size = [900, 700];

            const $ = (s) => root.querySelector(s);
            const elQuery = $(".cg-query"), elSort = $(".cg-sort"), elBaseModel = $(".cg-basemodel");
            const elMediaType = $(".cg-mediatype"), elAspect = $(".cg-aspect"), elNsfw = $(".cg-nsfw");
            const elUsername = $(".cg-username"), elTag = $(".cg-tag"), elTool = $(".cg-tool"), elTechnique = $(".cg-technique");
            const elSearchBtn = $(".cg-search"), elRefresh = $(".cg-refresh"), elStatus = $(".cg-status");
            const elScroll = $(".cg-scroll"), elGrid = $(".cg-masonry"), elSentinel = $(".cg-sentinel");
            const elBtnFavOnly = $(".cg-toggle-favonly"), elBtnRender = $(".cg-toggle-render");
            const elModalOverlay = $(".cg-modal-overlay"), elModalPreview = $(".cg-modal-preview");
            const elModalJson = $(".cg-modal-json"), elModalClose = $(".cg-modal-close"), elModalSelect = $(".cg-modal-select");

            let loading = false, hasMore = true, renderEnabled = true, currentOffset = 0, totalHits = 0;
            let favoritesOnly = false;
            let favoritesMap = {}, favOffset = 0;
            let modalItem = null, modalCard = null, inView = true;

            const setStatus = (msg) => { elStatus.textContent = msg || ""; };
            const setPayload = (obj) => { const s = JSON.stringify(obj || {}); cg.selection_data = s; if (wSel) wSel.value = s; node.setDirtyCanvas(true, true); };
            const loadFavs = async () => { try { favoritesMap = await getJSON("/civsearch/get_all_favorites_data"); } catch { favoritesMap = {}; } };
            const loadModels = async () => {
                try {
                    const models = await getJSON("/scromfy/base_models");
                    if (Array.isArray(models)) {
                        elBaseModel.innerHTML = ""; // Clear existing
                        const opts = ["Any", ...models.filter(m => m !== "Any")];
                        opts.forEach(m => {
                            const opt = document.createElement("option");
                            opt.value = m === "Any" ? "" : m;
                            opt.textContent = m;
                            elBaseModel.appendChild(opt);
                        });
                    }
                } catch (e) { console.error("Failed to load base models", e); }
            };
            const isVideo = (it) => it.type === "video";

            const makeUrl = () => {
                const p = {
                    q: elQuery.value.trim(),
                    baseModel: elBaseModel.value,
                    mediaType: elMediaType.value,
                    aspectRatio: elAspect.value,
                    nsfw: elNsfw.value,
                    sort: elSort.value,
                    username: elUsername.value.trim(),
                    tag: elTag.value.trim(),
                    tool: elTool.value.trim(),
                    technique: elTechnique.value.trim(),
                    offset: currentOffset,
                };
                return `/civsearch/search?${qs(p)}`;
            };

            const selectItem = (item, cardEl) => {
                elGrid.querySelectorAll(".cg-card.selected").forEach((c) => c.classList.remove("selected"));
                cardEl.classList.add("selected");
                const imageConnected = Array.isArray(node.outputs?.[0]?.links) && node.outputs[0].links.length > 0;
                setPayload({
                    item: {
                        ...item,
                        url: item.fullUrl || item.url,
                        meta: { prompt: item.prompt || "", negativePrompt: item.negativePrompt || "" }
                    },
                    download_image: !!imageConnected
                });
                setStatus(`✓ Selected #${item.id}`);
            };

            const showModal = async (item, card) => {
                modalItem = item; modalCard = card;
                const previewUrl = item.fullUrl || item.url;
                const container = $(".cg-modal-img-container");
                if (isVideo(item)) {
                    container.innerHTML = `<video class="cg-modal-preview" src="${previewUrl}" controls autoplay loop></video>`;
                } else {
                    container.innerHTML = `<img class="cg-modal-preview" src="${previewUrl}" alt="Preview">`;
                }
                elModalJson.innerHTML = formatJsonHtml(item);
                elModalOverlay.classList.add("show");
            };
            const hideModal = () => { elModalOverlay.classList.remove("show"); };

            elModalClose.addEventListener("click", hideModal);
            elModalOverlay.addEventListener("click", (e) => { if (e.target === elModalOverlay) hideModal(); });
            elModalSelect.addEventListener("click", () => { if (modalItem && modalCard) { selectItem(modalItem, modalCard); hideModal(); } });

            const makeCard = (it) => {
                const d = document.createElement("div"); d.className = "cg-card"; d.dataset.id = keyId(it.id);

                if (isVideo(it)) {
                    const vid = document.createElement("video");
                    vid.className = "cg-vid"; vid.src = it.thumbUrl || it.url; vid.muted = true; vid.loop = true;
                    vid.addEventListener("mouseenter", () => vid.play());
                    vid.addEventListener("mouseleave", () => { vid.pause(); vid.currentTime = 0; });
                    d.appendChild(vid);
                } else {
                    const img = document.createElement("img");
                    img.className = "cg-img"; img.loading = "lazy"; img.src = it.thumbUrl || it.url;
                    d.appendChild(img);
                }

                const meta = document.createElement("div"); meta.className = "cg-meta";
                const left = document.createElement("div"); left.className = "cg-meta-left";

                if (isVideo(it)) { const chip = document.createElement("span"); chip.className = "cg-chip video"; chip.textContent = "VIDEO"; left.appendChild(chip); }
                if (it.baseModel) { const chip = document.createElement("span"); chip.className = "cg-chip"; chip.textContent = it.baseModel; left.appendChild(chip); }
                if (it.username) { const chip = document.createElement("span"); chip.className = "cg-chip"; chip.textContent = it.username; left.appendChild(chip); }

                const star = document.createElement("button"); star.className = "cg-star"; star.title = "Favorite";
                const setStar = (on) => { star.classList.toggle("fav", on); star.textContent = on ? "★" : "☆"; };
                setStar(Boolean(favoritesMap[keyId(it.id)]));
                star.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    try {
                        const resp = await api.fetchApi("/civsearch/toggle_favorite", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ item: it }) });
                        const data = await resp.json();
                        if (data.isFavorite) { favoritesMap[keyId(it.id)] = it; setStar(true); }
                        else { delete favoritesMap[keyId(it.id)]; setStar(false); if (favoritesOnly) reload(true); }
                    } catch (err) { console.error(err); }
                });

                const right = document.createElement("div"); right.style.cssText = "display:flex;align-items:center;gap:6px";
                right.appendChild(star);
                meta.appendChild(left); meta.appendChild(right); d.appendChild(meta);

                d.addEventListener("click", () => showModal(it, d));
                requestAnimationFrame(() => d.classList.add("show"));
                return d;
            };

            const appendGrid = (items) => {
                const seen = new Set([...elGrid.querySelectorAll(".cg-card")].map((c) => c.dataset.id));
                for (const it of items) { const id = keyId(it.id); if (!seen.has(id)) { elGrid.appendChild(makeCard(it)); seen.add(id); } }
            };

            const loadMore = async () => {
                if (!renderEnabled || !inView || loading || !hasMore) return;
                loading = true; setStatus(`Loading offset ${currentOffset}...`);

                if (favoritesOnly) {
                    const arr = Object.values(favoritesMap);
                    const slice = arr.slice(favOffset, favOffset + 50);
                    if (slice.length) { appendGrid(slice); favOffset += slice.length; }
                    hasMore = favOffset < arr.length;
                    setStatus(hasMore ? `${favOffset}/${arr.length} favorites` : `All ${arr.length} favorites shown`);
                    loading = false;
                    return;
                }

                try {
                    const data = await getJSON(makeUrl());
                    const items = data.items || [];
                    totalHits = data.total || 0;
                    if (items.length) { appendGrid(items); currentOffset += items.length; }
                    hasMore = currentOffset < totalHits && items.length > 0;
                    setStatus(`${currentOffset} / ${totalHits} results`);
                } catch (err) {
                    console.error("[CivSearch] Error:", err);
                    setStatus(`Error: ${err.message}`);
                    hasMore = false;
                }
                loading = false;
            };

            const reload = (clear = true) => {
                if (clear) { elGrid.innerHTML = ""; currentOffset = 0; favOffset = 0; hasMore = true; }
                loadMore();
            };

            // Event listeners
            elSearchBtn.addEventListener("click", () => reload(true));
            elQuery.addEventListener("keydown", (e) => { if (e.key === "Enter") reload(true); });
            elRefresh.addEventListener("click", () => reload(true));
            elBtnFavOnly.addEventListener("click", () => { favoritesOnly = !favoritesOnly; toggleBtn(elBtnFavOnly, favoritesOnly); reload(true); });
            elBtnRender.addEventListener("click", () => {
                renderEnabled = !renderEnabled;
                elBtnRender.textContent = renderEnabled ? "Display: ON" : "Display: OFF";
                elBtnRender.classList.toggle("cg-render-on", renderEnabled);
                elBtnRender.classList.toggle("cg-render-off", !renderEnabled);
                elScroll.classList.toggle("paused", !renderEnabled);
                root.querySelector(".cg-foot").classList.toggle("paused", !renderEnabled);
                if (renderEnabled) loadMore();
            });

            // Infinite scroll with IntersectionObserver
            const obs = new IntersectionObserver((entries) => { if (entries[0].isIntersecting) loadMore(); }, { root: elScroll, threshold: 0.1 });
            obs.observe(elSentinel);

            // Viewport tracking
            const checkView = () => { const nowInView = isNodeOnScreen(node); if (nowInView && !inView && renderEnabled) loadMore(); inView = nowInView; };
            const onDraw = node.onDrawForeground;
            node.onDrawForeground = function (ctx) { onDraw?.apply(this, arguments); checkView(); };

            // Initial load
            loadModels();
            loadFavs().then(() => reload(true));

            return r;
        };
    },
});
