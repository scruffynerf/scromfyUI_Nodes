/**
 * Civitai Image Browser - ComfyUI Custom Node Frontend
 * Self-contained version for reliable loading
 */

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// ----- SECTION: Constants -----
const EXT_NAME = "CivitaiImageBrowser.InfiniteScroll";
const DISPLAY_NAME = "🖼️ Civitai Image Browser";
const TARGET_CLASS = "CivitaiImageBrowser";
const COLORS = { neon: "#39d0ff", neon2: "#6a5cff" };

const USER_TAG_GROUPS = [
    { label: "👤 People", items: [{ name: "👩 Woman", id: "5133" }, { name: "👨 Man", id: "5232" }] },
    { label: "🐾 Animals & Creatures", items: [{ name: "🐾 Animal", id: "111768" }, { name: "🐱 Cat", id: "5132" }, { name: "🐶 Dog", id: "5499" }] },
    { label: "🎨 Styles & Media", items: [{ name: "📷 Photography", id: "5241" }, { name: "🖼️ PhotoRealistic", id: "172" }, { name: "🎎 Anime", id: "4" }] },
    { label: "🏞️ Environments", items: [{ name: "🌲 Outdoors", id: "111763" }, { name: "🌄 Landscape", id: "8363" }, { name: "🏙️ City", id: "55" }] },
    { label: "🎮 Genres", items: [{ name: "🐲 Fantasy", id: "5207" }, { name: "👾 Sci-Fi", id: "3060" }, { name: "🤖 Robot", id: "6594" }] },
];

// ----- SECTION: Utilities -----
const qs = (o) => Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== "").map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
const getJSON = async (path) => { const r = await api.fetchApi(path); if (!r.ok) throw new Error(`${r.status}`); return r.json(); };
const keyId = (id) => String(id);
const toggleBtn = (btn, flag) => btn.classList.toggle("active", flag);
const nearBottom = (el, threshold = 900) => el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;

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
#${uid} .cg-controls{display:flex;flex-direction:column;gap:8px;margin-top:8px}
#${uid} .cg-row{display:flex;align-items:center;gap:8px;flex-wrap:nowrap}
#${uid} .cg-input,#${uid} .cg-select{padding:8px 10px;border:1px solid var(--cg-border);background:var(--cg-surface);color:var(--node-text-color);border-radius:10px;height:32px;backdrop-filter:blur(8px)}
#${uid} .cg-select{appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--cg-neon) 50%),linear-gradient(135deg,var(--cg-neon) 50%,transparent 50%);background-position:calc(100% - 16px) calc(50% + 3px),calc(100% - 12px) calc(50% + 3px);background-size:6px 6px;background-repeat:no-repeat;padding-right:26px}
#${uid} .cg-btn{padding:8px 12px;border:1px solid var(--cg-border);background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border-radius:10px;cursor:pointer;transition:.18s;box-shadow:var(--cg-shadow);white-space:nowrap;color:var(--node-text-color)}
#${uid} .cg-btn:hover{filter:brightness(1.08)}
#${uid} .cg-btn.toggle.active{box-shadow:0 0 0 1px ${hexToRgba(neon, 0.35)} inset;outline:2px solid var(--cg-neon)}
#${uid} .cg-scroll{flex:1;min-height:0;overflow:auto;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,.01));border:1px solid var(--cg-border);padding:10px;box-shadow:var(--cg-shadow);overflow-anchor:none;overscroll-behavior:contain}
#${uid} .cg-scroll::-webkit-scrollbar{width:10px}
#${uid} .cg-scroll::-webkit-scrollbar-thumb{background:linear-gradient(var(--cg-neon),var(--cg-neon2));border-radius:10px}
#${uid} .cg-masonry{column-gap:12px;--colw:280px;column-width:var(--colw)}
#${uid} .cg-card{display:inline-block;width:100%;margin:0 0 12px;border:1px solid var(--cg-border);border-radius:14px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02));position:relative;break-inside:avoid;opacity:0;transform:translateY(6px);transition:opacity .18s,transform .18s;box-shadow:var(--cg-shadow)}
#${uid} .cg-card.show{opacity:1;transform:translateY(0)}
#${uid} .cg-card:hover{box-shadow:0 0 24px ${hexToRgba(neon, 0.13)},var(--cg-shadow)}
#${uid} .cg-card.selected{outline:2px solid var(--cg-neon);outline-offset:-2px}
#${uid} .cg-img,#${uid} .cg-vid{width:100%;height:auto;display:block;background:#0e0f13}
#${uid} .cg-vid{max-height:72vh}
#${uid} .cg-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 10px}
#${uid} .cg-meta-left{display:flex;align-items:center;gap:8px}
#${uid} .cg-chip{font-size:11px;background:var(--cg-chip-bg);border:1px solid var(--cg-border);padding:2px 8px;border-radius:999px}
#${uid} .cg-chip.nsfw{background:rgba(255,100,100,.2);border-color:rgba(255,100,100,.4);color:#ff9999}
#${uid} .cg-open{font-size:12px;text-decoration:none;border:1px solid var(--cg-border);padding:4px 8px;border-radius:8px;background:var(--cg-surface);color:var(--node-text-color);opacity:.95}
#${uid} .cg-open:hover{opacity:1}
#${uid} .cg-star{border:none;background:transparent;font-size:20px;cursor:pointer;color:#8b8b8b;transition:.15s}
#${uid} .cg-star:hover{transform:scale(1.06)}
#${uid} .cg-star.fav{color:#ffd970;text-shadow:0 0 8px rgba(255,217,112,.35)}
#${uid} .cg-foot{display:flex;align-items:center;gap:10px;flex-shrink:0;padding:10px;border:1px solid var(--cg-border);border-radius:14px;background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));box-shadow:var(--cg-shadow)}
#${uid} .cg-status{font-size:12px;opacity:.8}
#${uid} .cg-sentinel{width:100%;height:1px}
#${uid} .cg-toggle-render.cg-render-on{color:#22c55e;border-color:#22c55e66}
#${uid} .cg-toggle-render.cg-render-off{color:#ef4444;border-color:#ef444466}
#${uid} .cg-scroll.paused,#${uid} .cg-foot.paused{display:none!important}
#${uid} .cg-input.cg-username{width:100px}
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
const CONTROLS_HTML = `
<div class="cg-row">
  <label>NSFW</label><select class="cg-select cg-nsfw"><option>None</option><option>Soft</option><option>Mature</option><option>X</option></select>
  <label>Sort</label><select class="cg-select cg-sort"><option>Newest</option><option>Most Reactions</option><option>Most Comments</option></select>
  <label>Period</label><select class="cg-select cg-period"><option>AllTime</option><option>Year</option><option>Month</option><option>Week</option><option>Day</option></select>
</div>
<div class="cg-row">
  <label>BaseModel</label><select class="cg-select cg-basemodel"><option value="">Any</option></select>
  <label>Tags</label><select class="cg-select cg-tags"><option value="">None</option></select>
  <input class="cg-input cg-username" placeholder="Username">
  <button class="cg-btn cg-search">Apply</button>
</div>
<div class="cg-row">
  <label>Batch</label><select class="cg-select cg-limit"><option value="5">5</option><option value="10">10</option><option value="24" selected>24</option><option value="50">50</option><option value="100">100</option></select>
  <button class="cg-btn toggle cg-toggle-video">Videos only</button>
  <button class="cg-btn toggle cg-toggle-noprompt">Hide no-prompt</button>
  <button class="cg-btn toggle cg-toggle-favonly">Favorites only</button>
  <button class="cg-btn cg-refresh">Refresh</button>
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

            if (!cg.colored_once) { node.color = "#000000"; node.bgcolor = "#0b0b0b"; cg.colored_once = true; }

            removeSelectionPort(node);
            const wSel = ensureHiddenSelectionWidget(node, cg);

            const uid = `cg-${Math.random().toString(36).slice(2, 9)}`;
            const root = document.createElement("div");
            root.id = uid;
            root.innerHTML = `
<style>${generateCSS(uid)}</style>
<div class="cg-root">
  <div class="cg-header">
    <div class="cg-title"><span class="dot"></span><div>${DISPLAY_NAME}</div><div class="cg-sub">Infinite scroll</div></div>
    <div class="cg-controls">${CONTROLS_HTML}</div>
  </div>
  <div class="cg-scroll"><div class="cg-masonry"></div><div class="cg-sentinel"></div></div>
  <div class="cg-foot"><span class="cg-status" style="margin-left:auto"></span></div>
  ${MODAL_HTML}
</div>`;

            node.addDOMWidget("civitai_images", "div", root, {});
            node.size = [1120, 820];

            const $ = (s) => root.querySelector(s);
            const elNSFW = $(".cg-nsfw"), elSort = $(".cg-sort"), elPeriod = $(".cg-period");
            const elBaseModel = $(".cg-basemodel"), elTags = $(".cg-tags"), elUser = $(".cg-username");
            const elSearchBtn = $(".cg-search"), elRefresh = $(".cg-refresh"), elStatus = $(".cg-status");
            const elScroll = $(".cg-scroll"), elGrid = $(".cg-masonry"), elSentinel = $(".cg-sentinel");
            const elBtnVideo = $(".cg-toggle-video"), elBtnNoPrompt = $(".cg-toggle-noprompt");
            const elBtnFavOnly = $(".cg-toggle-favonly"), elLimitSel = $(".cg-limit"), elBtnRender = $(".cg-toggle-render");
            const elModalOverlay = $(".cg-modal-overlay");
            const elModalJson = $(".cg-modal-json"), elModalClose = $(".cg-modal-close"), elModalSelect = $(".cg-modal-select");

            let loading = false, hasMore = true, renderEnabled = true;
            let favoritesOnly = false, videosOnly = false, hideNoPrompt = false;
            let favoritesMap = {}, favoritesArray = [], cursor = null, favOffset = 0;
            let modalItem = null, modalCard = null, inView = true;

            // Populate tags
            elTags.replaceChildren(new Option("None", ""));
            for (const g of USER_TAG_GROUPS) {
                const og = document.createElement("optgroup"); og.label = g.label;
                for (const t of g.items) og.appendChild(new Option(t.name, String(t.id)));
                elTags.appendChild(og);
            }

            const setStatus = (msg) => { elStatus.textContent = msg || ""; };
            const setPayload = (obj) => { const s = JSON.stringify(obj || {}); cg.selection_data = s; if (wSel) wSel.value = s; node.setDirtyCanvas(true, true); };
            const loadFavs = async () => { try { favoritesMap = await getJSON("/civitai_images/get_all_favorites_data"); } catch { favoritesMap = {}; } };
            const loadModels = async () => {
                try {
                    const models = await getJSON("/scromfy/base_models");
                    if (Array.isArray(models)) {
                        elBaseModel.replaceChildren(new Option("Any", ""));
                        models.forEach(m => {
                            if (m !== "Any") elBaseModel.appendChild(new Option(m, m));
                        });
                    }
                } catch (e) { console.error("Failed to load base models", e); }
            };
            const isVideo = (it) => { const u = (it?.url || "").toLowerCase(); return u.endsWith(".mp4") || u.endsWith(".webm"); };
            const hasPrompt = (it) => !!(it?.meta?.prompt || it?.meta?.Prompt || "").trim();
            const civitaiUrl = (it) => `https://civitai.com/images/${it.id}`;
            const batchSize = () => Math.min(200, Math.max(5, parseInt(elLimitSel.value || "24", 10)));

            const makeUrl = (cur) => {
                const p = { min_batch: batchSize(), cursor: cur || "", sort: elSort.value, period: elPeriod.value, username: elUser.value.trim(), nsfw: elNSFW.value || "None", include_videos: videosOnly ? "true" : "false", videos_only: videosOnly ? "true" : "false", hide_no_prompt: hideNoPrompt ? "true" : "false" };
                if (elTags.value) p.tags = elTags.value;
                if (elBaseModel.value) p.baseModel = elBaseModel.value;
                return `/civitai_images/images_stream?${qs(p)}`;
            };

            const selectItem = (item, cardEl) => {
                elGrid.querySelectorAll(".cg-card.selected").forEach((c) => c.classList.remove("selected"));
                cardEl.classList.add("selected");
                const meta = item.meta || {};
                const imageConnected = Array.isArray(node.outputs?.[2]?.links) && node.outputs[2].links.length > 0;
                setPayload({ item: { ...item, meta: { ...meta, prompt: meta.prompt || meta.Prompt || "", negativePrompt: meta.negativePrompt || "" } }, download_image: !!imageConnected });
            };

            const elModalImgContainer = $(".cg-modal-img-container");
            const showModal = (item, card) => {
                modalItem = item; modalCard = card;
                if (isVideo(item)) {
                    const v = document.createElement("video"); v.className = "cg-modal-preview"; v.controls = true; v.muted = true; v.src = item.url;
                    elModalImgContainer.replaceChildren(v);
                } else {
                    const img = document.createElement("img"); img.className = "cg-modal-preview"; img.src = item.url;
                    elModalImgContainer.replaceChildren(img);
                }
                elModalJson.innerHTML = formatJsonHtml(item);
                elModalOverlay.classList.add("show");
            };
            const hideModal = () => { elModalOverlay.classList.remove("show"); const v = elModalOverlay.querySelector("video"); if (v) v.pause(); };

            elModalClose.addEventListener("click", hideModal);
            elModalOverlay.addEventListener("click", (e) => { if (e.target === elModalOverlay) hideModal(); });
            elModalSelect.addEventListener("click", () => { if (modalItem && modalCard) { selectItem(modalItem, modalCard); hideModal(); } });

            const makeCard = (it) => {
                const d = document.createElement("div"); d.className = "cg-card"; d.dataset.id = keyId(it.id);
                if (isVideo(it)) {
                    const v = document.createElement("video"); v.className = "cg-vid"; v.controls = true; v.muted = true; v.playsInline = true; v.preload = "none"; v.dataset.src = it.url; d.appendChild(v);
                } else {
                    const img = document.createElement("img"); img.className = "cg-img"; img.loading = "lazy"; img.src = it.url; d.appendChild(img);
                }
                const meta = document.createElement("div"); meta.className = "cg-meta";
                const left = document.createElement("div"); left.className = "cg-meta-left";
                const nsfwChip = document.createElement("span"); nsfwChip.className = "cg-chip"; nsfwChip.textContent = it.nsfwLevel || "None"; left.appendChild(nsfwChip);
                const baseModel = it.base_model || it.baseModel;
                if (baseModel) { const modelChip = document.createElement("span"); modelChip.className = "cg-chip"; modelChip.textContent = baseModel; left.appendChild(modelChip); }

                const star = document.createElement("button"); star.className = "cg-star"; star.title = "Favorite";
                const setStar = (on) => { star.classList.toggle("fav", on); star.textContent = on ? "★" : "☆"; };
                setStar(Boolean(favoritesMap[keyId(it.id)]));
                star.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    try {
                        const resp = await api.fetchApi("/civitai_images/toggle_favorite", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ item: it }) });
                        const data = await resp.json();
                        if (data.status === "added") { favoritesMap[keyId(it.id)] = it; setStar(true); }
                        else if (data.status === "removed") { delete favoritesMap[keyId(it.id)]; setStar(false); if (favoritesOnly) reload(true); }
                    } catch (err) { console.error(err); }
                });

                const open = document.createElement("a"); open.className = "cg-open"; open.href = civitaiUrl(it); open.target = "_blank"; open.textContent = "Open ↗"; open.addEventListener("click", (e) => e.stopPropagation());

                const right = document.createElement("div"); right.style.cssText = "display:flex;align-items:center;gap:8px";
                right.appendChild(star); right.appendChild(open);
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
                loading = true; setStatus("Loading...");
                try {
                    if (favoritesOnly) {
                        if (!favoritesArray.length) { await loadFavs(); favoritesArray = Object.values(favoritesMap); }
                        let filtered = videosOnly ? favoritesArray.filter(isVideo) : favoritesArray.filter((i) => !isVideo(i));
                        if (hideNoPrompt) filtered = filtered.filter(hasPrompt);
                        const slice = filtered.slice(favOffset, favOffset + batchSize());
                        appendGrid(slice); favOffset += batchSize(); hasMore = favOffset < filtered.length;
                        setStatus(hasMore ? `Loaded ${slice.length}` : "End");
                    } else {
                        const data = await getJSON(makeUrl(cursor));
                        let items = data?.items || [];
                        if (videosOnly) items = items.filter(isVideo); else items = items.filter((i) => !isVideo(i));
                        appendGrid(items);
                        cursor = data?.metadata?.nextCursor || null; hasMore = !!cursor && items.length > 0;
                        setStatus(hasMore ? `Loaded ${items.length}` : "End");
                    }
                } catch (e) { hasMore = false; setStatus(`Error: ${e.message}`); }
                finally { loading = false; }
            };

            const reload = async (resetScroll) => {
                if (!renderEnabled || !inView || loading) return;
                loading = true; setStatus("Reloading...");
                elGrid.replaceChildren(); cursor = null; favOffset = 0; favoritesArray = []; hasMore = true;
                if (resetScroll) elScroll.scrollTop = 0;
                await loadFavs(); favoritesArray = Object.values(favoritesMap);
                loading = false; await loadMore();
            };

            const setRenderState = (on) => {
                renderEnabled = on; cg.display_on = on;
                elBtnRender.classList.toggle("cg-render-on", on); elBtnRender.classList.toggle("cg-render-off", !on);
                elBtnRender.textContent = on ? "Display: ON" : "Display: OFF";
                elScroll.classList.toggle("paused", !on); root.querySelector(".cg-foot").classList.toggle("paused", !on);
                if (on && !cg.has_loaded_once) { cg.has_loaded_once = true; reload(true); }
            };

            // Viewport watcher
            let _viewRAF = 0;
            const watchView = () => {
                const now = isNodeOnScreen(node);
                if (now !== inView) { inView = now; if (inView && renderEnabled && !cg.has_loaded_once) { cg.has_loaded_once = true; reload(true); } }
                _viewRAF = requestAnimationFrame(watchView);
            };
            _viewRAF = requestAnimationFrame(watchView);

            // Infinite scroll
            const io = new IntersectionObserver((entries) => {
                if (!renderEnabled || !inView) return;
                for (const e of entries) if (e.isIntersecting && !loading && hasMore) loadMore();
            }, { root: elScroll, rootMargin: "1200px" });
            io.observe(elSentinel);

            elScroll.addEventListener("scroll", () => { if (nearBottom(elScroll) && !loading && hasMore && renderEnabled && inView) loadMore(); }, { passive: true });

            // Lazy load videos
            const ioVid = new IntersectionObserver((entries) => {
                for (const e of entries) { const v = e.target; if (v?.tagName === "VIDEO" && e.isIntersecting && !v.src && v.dataset.src) { v.src = v.dataset.src; v.load(); } }
            }, { root: elScroll, rootMargin: "600px" });
            new MutationObserver(() => { elGrid.querySelectorAll("video[data-src]:not([src])").forEach((v) => ioVid.observe(v)); }).observe(elGrid, { childList: true });

            // Event listeners
            [elNSFW, elSort, elPeriod, elLimitSel, elBaseModel, elTags].forEach((x) => x.addEventListener("change", () => reload(true)));
            elRefresh.addEventListener("click", () => reload(true));
            elSearchBtn.addEventListener("click", () => reload(true));
            elUser.addEventListener("keydown", (e) => { if (e.key === "Enter") reload(true); });
            elBtnVideo.addEventListener("click", () => { videosOnly = !videosOnly; toggleBtn(elBtnVideo, videosOnly); reload(true); });
            elBtnNoPrompt.addEventListener("click", () => { hideNoPrompt = !hideNoPrompt; toggleBtn(elBtnNoPrompt, hideNoPrompt); reload(true); });
            elBtnFavOnly.addEventListener("click", () => { favoritesOnly = !favoritesOnly; toggleBtn(elBtnFavOnly, favoritesOnly); reload(true); });
            elBtnRender.addEventListener("click", () => setRenderState(!renderEnabled));

            // Resize
            const ro = new ResizeObserver(() => { const w = elScroll.clientWidth || 900; elGrid.style.setProperty("--colw", `${Math.max(240, Math.min(360, Math.floor(w / Math.ceil(w / 280))))}px`); });
            ro.observe(elScroll);

            node.onRemoved = function () { try { cancelAnimationFrame(_viewRAF); io.disconnect(); ioVid.disconnect(); ro.disconnect(); } catch { } };

            // Initialize
            toggleBtn(elBtnVideo, videosOnly); toggleBtn(elBtnNoPrompt, hideNoPrompt); toggleBtn(elBtnFavOnly, favoritesOnly);
            loadModels();
            setRenderState(cg.display_on !== false);

            return r;
        };
    },
});
