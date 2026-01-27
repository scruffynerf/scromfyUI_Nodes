import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// CSS for the browser
const style = `
.cg-browser { display:flex; flex-direction:column; height:100%; font-family:sans-serif; background:var(--comfy-menu-bg); color:var(--comfy-text-color); overflow:hidden; }
.cg-head { padding:8px; display:flex; gap:8px; align-items:center; background:rgba(0,0,0,0.2); flex-wrap:wrap; }
.cg-search { flex:1; padding:6px; border-radius:4px; border:1px solid var(--border-color); background:var(--comfy-input-bg); color:var(--comfy-input-text); }
.cg-btn { padding:6px 12px; cursor:pointer; background:var(--comfy-input-bg); border:1px solid var(--border-color); border-radius:4px; color:var(--comfy-input-text); }
.cg-btn:hover { background:var(--comfy-input-bg-hover); }
.cg-btn.active { background:var(--primary-hover-bg); color:white; border-color:var(--primary-hover-bg); }
.cg-scroll { flex:1; overflow-y:auto; padding:8px; position:relative; }
.cg-grid { column-count:var(--cols, 4); column-gap:8px; display:block; }
.cg-card { position:relative; border-radius:4px; overflow:hidden; background:rgba(0,0,0,0.2); margin-bottom:8px; break-inside:avoid; cursor:pointer; transition:transform 0.1s; border:1px solid transparent; }
.cg-card:hover { transform:scale(1.02); border-color:var(--primary-bg); z-index:10; }
.cg-card.selected { border-color:var(--error-text); box-shadow:0 0 0 2px var(--error-text); }
.cg-img { width:100%; height:auto; display:block; }
.cg-meta { position:absolute; bottom:0; left:0; right:0; background:rgba(0,0,0,0.7); padding:4px; font-size:12px; display:flex; justify-content:space-between; align-items:center; opacity:0; transition:opacity 0.2s; }
.cg-card:hover .cg-meta { opacity:1; }
.cg-chip { background:#333; padding:2px 6px; border-radius:4px; margin-right:4px; }
.cg-chip.nsfw { background:#822; }
.cg-star { background:none; border:none; color:#666; font-size:16px; cursor:pointer; padding:0 4px; }
.cg-star.fav { color:gold; }
.cg-open { color:#8af; text-decoration:none; margin-left:8px; }
.cg-foot { padding:8px; text-align:center; background:rgba(0,0,0,0.2); font-size:12px; color:#888; }
.cg-modal { position:fixed !important; top:0 !important; left:0 !important; right:0 !important; bottom:0 !important; background:rgba(0,0,0,0.85) !important; z-index:9999 !important; display:none; align-items:center !important; justify-content:center !important; padding:40px !important; }
.cg-modal.show { display:flex !important; }
.cg-modal-content { display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important; width:92% !important; height:82% !important; max-width:1400px !important; background:linear-gradient(135deg,rgba(30,30,40,.98),rgba(20,20,30,.98)) !important; border:1px solid var(--border-color); border-radius:14px !important; overflow:hidden !important; box-shadow:0 20px 60px rgba(0,0,0,.5); align-items:stretch !important; }
.cg-modal-img { flex:1 1 60% !important; min-width:0 !important; object-fit:contain !important; max-width:none !important; max-height:100% !important; background:#050508 !important; border-right:1px solid var(--border-color) !important; }
.cg-modal-info { flex:1 1 40% !important; min-width:350px !important; display:flex !important; flex-direction:column !important; overflow:hidden !important; background:rgba(0,0,0,0.2) !important; min-height:0 !important; }
.cg-modal-info-scroll { flex:1 1 0% !important; overflow-y:auto !important; padding:20px !important; min-height:0 !important; }
.cg-modal-actions { padding:16px !important; border-top:1px solid var(--border-color) !important; flex-shrink:0 !important; }
.cg-modal-close { position:absolute !important; top:20px !important; right:30px !important; font-size:32px !important; color:#fff !important; cursor:pointer !important; opacity:0.7 !important; transition:0.2s !important; z-index:10001 !important; }
.cg-modal-close:hover { opacity:1 !important; color:#ef4444 !important; transform:scale(1.1) !important; }
.cg-tag { display:inline-block; padding:2px 6px; background:#444; margin:2px; border-radius:4px; font-size:11px; color:#ddd; }
.cg-tag.copy { cursor:pointer; }
.cg-tag.copy:hover { background:#666; }
.cg-render-on { background: #2a2; color: #fff; }
.cg-render-off { background: #a22; color: #fff; }
.paused { opacity: 0.5; pointer-events: none; filter: grayscale(1); }
`;

// Inject CSS
const styleEl = document.createElement("style");
styleEl.textContent = style;
document.head.appendChild(styleEl);

// Utils
const $ = (t, p = document) => p.querySelector(t);
const debounce = (f, d) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => f(...a), d); }; };
const keyId = (id) => `danbooru_${id}`;

app.registerExtension({
    name: "Comfy.DanbooruImageBrowser",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "DanbooruImageBrowser") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            const node = this;
            const widget = node.widgets.find((w) => w.name === "url");
            if (widget) widget.hidden = true;

            const widgetSel = node.widgets.find((w) => w.name === "selection_data");
            if (widgetSel) widgetSel.hidden = true;

            // Sites and Auth State
            let SITES = {};
            let SITE_AUTH = {};

            // Fetch Sites Config
            const loadSites = async () => {
                try {
                    const res = await api.fetchApi("/danbooru_images/sites");
                    if (res.ok) {
                        const data = await res.json();
                        // Normalize data: transform to desired internal structure if needed
                        // sites.json structure from example: { "yande.re": { domain: "...", ... } }
                        // We need key-value.
                        Object.keys(data).forEach(k => {

                            const s = data[k];
                            // Clean Name
                            if (s.name) s.name = s.name.replace("www.", "");
                            else if (s.domain) s.name = s.domain.replace("www.", "");

                            // Ensure params defaults to avoid undefined errors
                            if (!s.params) s.params = { limit: 20 };

                            if (!s.url && s.domain && s.api && s.api.search) {
                                s.url = `https://${s.domain}${s.api.search}`;
                            }
                            // Type inference forGelbooru check logic?
                            if (s.domain && s.domain.includes("gelbooru")) s.type = "gelbooru";
                        });
                        SITES = data;
                        console.log("[GenericBrowser] Loaded sites:", Object.keys(SITES).length);
                        populateSiteSelector();
                    } else {
                        console.warn("[GenericBrowser] Failed to load sites.json, using defaults.");
                        useDefaultSites();
                        populateSiteSelector();
                    }
                } catch (e) {
                    console.error("[GenericBrowser] Error loading sites:", e);
                    useDefaultSites();
                    populateSiteSelector();
                }
            };

            const useDefaultSites = () => {
                SITES = {
                    danbooru: {
                        name: "Danbooru",
                        url: "https://danbooru.donmai.us/posts.json",
                        type: "danbooru",
                        params: { limit: 50 },
                    },
                    safebooru: {
                        name: "Safebooru",
                        url: "https://safebooru.donmai.us/posts.json",
                        type: "danbooru",
                        params: { limit: 50 },
                    },
                    konachan: {
                        name: "Konachan",
                        url: "https://konachan.net/post.json",
                        type: "moebooru",
                        params: { limit: 50 },
                    },
                    yandere: {
                        name: "Yande.re",
                        url: "https://yande.re/post.json",
                        type: "moebooru",
                        params: { limit: 50 },
                    },
                    gelbooru: {
                        name: "Gelbooru",
                        url: "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1",
                        type: "gelbooru",
                        params: { limit: 50 },
                    }
                };
            };

            // Initial load of Auth (domains only)
            const loadAuthDomains = async () => {
                try {
                    const res = await api.fetchApi("/danbooru_images/auth");
                    if (res.ok) {
                        const data = await res.json();
                        // data.domains is list of domains
                        // We can flag sites in UI that have auth configured?
                        console.log("[GenericBrowser] Auth domains:", data.domains);
                    }
                } catch (e) { }
            };


            // State
            let items = [];
            let currentPage = 1;
            let hasMore = true;
            let loading = false;
            let favoritesMap = {};
            let favoritesArray = [];
            let favOffset = 0;
            // Persistence
            const cg = node.cg_state || (node.cg_state = { display_on: true, has_loaded_once: false, site: "danbooru" });

            let currentSiteKey = cg.site || "danbooru";
            // Wait for sites to load to validate? Or do late validation.

            // Settings
            let showNsfw = false;
            let favoritesOnly = false;
            let renderEnabled = cg.display_on;
            let inView = false;


            // UI Elements
            const root = document.createElement("div");
            root.className = "cg-browser";

            // Header
            const elHead = document.createElement("div"); elHead.className = "cg-head";

            // Site Selector
            const elSiteSelect = document.createElement("select");
            elSiteSelect.className = "cg-btn";
            elSiteSelect.style.background = "var(--comfy-input-bg)";
            elSiteSelect.style.maxWidth = "120px";

            const populateSiteSelector = () => {
                elSiteSelect.innerHTML = "";
                // Sort sites by key or name?
                const keys = Object.keys(SITES).sort();

                // If current key not in sites, picking first
                if (!SITES[currentSiteKey]) {
                    if (SITES["danbooru.donmai.us"]) currentSiteKey = "danbooru.donmai.us";
                    else if (keys.length > 0) currentSiteKey = keys[0];
                }

                keys.forEach(k => {
                    const opt = document.createElement("option");
                    opt.value = k;
                    const s = SITES[k];
                    // Name might be just the key if no explicit name
                    opt.textContent = s.name || k;
                    if (k === currentSiteKey) opt.selected = true;
                    elSiteSelect.appendChild(opt);
                });
                // Trigger reload if we just populated?
                // reload(true);
            };

            elSiteSelect.addEventListener("change", (e) => {
                currentSiteKey = e.target.value;
                cg.site = currentSiteKey;
                console.log("[GenericBrowser] Switched site to:", currentSiteKey);
                reload(true);
            });

            const elSearchInput = document.createElement("input"); elSearchInput.className = "cg-search"; elSearchInput.placeholder = "Search tags...";

            const elBtnSearch = document.createElement("button"); elBtnSearch.className = "cg-btn"; elBtnSearch.textContent = "Search";

            // Sort Dropdown
            const elSort = document.createElement("select"); elSort.className = "cg-btn"; elSort.style.maxWidth = "100px";
            const sorts = { "": "Newest", "score": "Top Score", "rank:daily": "Dailey", "rank:weekly": "Weekly", "rank:monthly": "Monthly" };
            Object.entries(sorts).forEach(([v, l]) => {
                const o = document.createElement("option"); o.value = v; o.textContent = l; elSort.appendChild(o);
            });
            elSort.addEventListener("change", () => reload(true));

            // Rating Dropdown (Replaces simple NSFW toggle)
            const elRating = document.createElement("select"); elRating.className = "cg-btn"; elRating.style.maxWidth = "90px";
            const ratings = { "": "All", "g": "General", "s": "Sensitive", "q": "Questionable", "e": "Explicit" };
            // Note: Danbooru uses g/s/q/e. Moebooru uses s/q/e. Gelbooru uses rating:safe etc.
            // We need to map these in buildApiUrl.

            Object.entries(ratings).forEach(([v, l]) => {
                const o = document.createElement("option"); o.value = v; o.textContent = l; elRating.appendChild(o);
            });
            // Default to Safe/General? User usually wants NSFW off by default or All.
            // Let's default to "All" (empty) but respecting the "Show NSFW" boolean logic we had?
            // User requested granular. Let's strictly use this dropdown.
            elRating.value = ""; // All
            elRating.addEventListener("change", () => reload(true));

            const elBtnFavOnly = document.createElement("button"); elBtnFavOnly.className = "cg-btn"; elBtnFavOnly.textContent = "Favs";
            elBtnFavOnly.title = "Show Favorites Only";

            const elBtnSettings = document.createElement("button"); elBtnSettings.className = "cg-btn"; elBtnSettings.textContent = "⚙";
            elBtnSettings.title = "Settings (Auth)";

            const elBtnRender = document.createElement("button"); elBtnRender.className = "cg-btn"; elBtnRender.textContent = "ON";

            const elBtnRefresh = document.createElement("button"); elBtnRefresh.className = "cg-btn"; elBtnRefresh.textContent = "↻"; elBtnRefresh.title = "Refresh";

            elHead.append(elSiteSelect, elSearchInput, elBtnSearch, elSort, elRating, elBtnFavOnly, elBtnSettings, elBtnRefresh, elBtnRender);

            // Settings Modal
            const createSettingsModal = () => {
                const m = document.createElement("div"); m.className = "cg-modal";
                m.style.zIndex = "10000"; // Higher than image modal

                const c = document.createElement("div"); c.className = "cg-modal-content";
                c.style.flexDirection = "column"; c.style.maxWidth = "500px"; c.style.maxHeight = "80vh";
                c.style.background = "var(--comfy-menu-bg)"; c.style.padding = "20px"; c.style.overflowY = "auto";
                c.style.margin = "auto"; // Center

                const h2 = document.createElement("h2"); h2.textContent = "Settings & Authentication";
                h2.style.marginTop = "0";

                const desc = document.createElement("p");
                desc.textContent = "Enter API credentials for the SELECTED site below.";
                desc.style.color = "#888";

                const form = document.createElement("div");
                form.style.display = "flex"; form.style.flexDirection = "column"; form.style.gap = "10px";

                const lLabel = document.createElement("label"); lLabel.textContent = `Current Site: ${currentSiteKey}`;
                lLabel.style.fontWeight = "bold";

                const iUser = document.createElement("input"); iUser.className = "cg-search"; iUser.placeholder = "Username";
                const iKey = document.createElement("input"); iKey.className = "cg-search"; iKey.placeholder = "API Key / Hash";
                iKey.type = "password";

                const btnSave = document.createElement("button"); btnSave.className = "cg-btn"; btnSave.textContent = "Save Credentials";
                btnSave.style.marginTop = "10px";

                const status = document.createElement("div"); status.style.color = "#aaa"; status.style.fontSize = "0.8em";

                btnSave.onclick = async () => {
                    const u = iUser.value.trim();
                    const k = iKey.value.trim();
                    // Use 'url' or 'domain' from current site config as key
                    const site = SITES[currentSiteKey];
                    let domain = currentSiteKey;
                    if (site) {
                        if (site.domain) domain = site.domain;
                        else if (site.url) {
                            try { domain = new URL(site.url).host; } catch (e) { }
                        }
                    }

                    status.textContent = "Saving...";
                    try {
                        const res = await api.fetchApi("/danbooru_images/auth", {
                            method: "POST",
                            body: JSON.stringify({ domain: domain, username: u, api_key: k })
                        });
                        const d = await res.json();
                        if (d.status === "ok") {
                            status.textContent = "Saved! Reloading page to apply...";
                            setTimeout(() => {
                                m.classList.remove("show");
                                reload(true);
                            }, 1000);
                        } else {
                            status.textContent = "Error: " + d.error;
                        }
                    } catch (e) { status.textContent = "Error: " + e.message; }
                };

                const btnClose = document.createElement("button"); btnClose.className = "cg-modal-close"; btnClose.textContent = "×";
                btnClose.onclick = () => m.classList.remove("show");

                c.append(btnClose, h2, desc, lLabel, iUser, iKey, btnSave, status);
                m.append(c);
                document.body.appendChild(m);
                return { m, iUser, iKey, lLabel };
            };

            const settingsUI = createSettingsModal();
            elBtnSettings.onclick = () => {
                settingsUI.lLabel.textContent = `Current Site: ${SITES[currentSiteKey]?.name || currentSiteKey}`;
                settingsUI.iUser.value = "";
                settingsUI.iKey.value = ""; // Don't show existing for security? or generic
                settingsUI.m.classList.add("show");
            };

            // Container
            const elScroll = document.createElement("div"); elScroll.className = "cg-scroll";
            const elGrid = document.createElement("div"); elGrid.className = "cg-grid";
            const elSentinel = document.createElement("div"); elSentinel.style.height = "20px";
            const elStatus = document.createElement("div"); elStatus.className = "cg-foot";

            elScroll.append(elGrid, elSentinel);
            root.append(elHead, elScroll, elStatus);

            // Add to widget
            const w = node.addDOMWidget("browser", "Browser", root, {
                serialize: false,
                hideOnZoom: false,
                getValue() { return items.length; },
                setValue(v) { },
            });
            w.computedHeight = 600;

            // ... Modal ... (unchanged logic mostly, keep existing)
            // Modal
            const elModal = document.createElement("div"); elModal.className = "cg-modal";
            const elModalClose = document.createElement("div"); elModalClose.className = "cg-modal-close"; elModalClose.textContent = "×";
            const elModalContent = document.createElement("div"); elModalContent.className = "cg-modal-content";
            const elModalImg = document.createElement("img"); elModalImg.className = "cg-modal-img";
            const elModalInfo = document.createElement("div"); elModalInfo.className = "cg-modal-info";
            const elModalInfoScroll = document.createElement("div"); elModalInfoScroll.className = "cg-modal-info-scroll";
            const elModalActions = document.createElement("div"); elModalActions.className = "cg-modal-actions";
            const elModalSelect = document.createElement("button"); elModalSelect.className = "cg-btn"; elModalSelect.textContent = "Select Image"; elModalSelect.style.width = "100%";

            elModalActions.append(elModalSelect);
            elModalInfo.append(elModalInfoScroll, elModalActions);
            elModalContent.append(elModalImg, elModalInfo);
            elModal.append(elModalClose, elModalContent);
            document.body.appendChild(elModal);

            let modalItem = null;
            let modalCard = null;

            // Logic
            const setStatus = (s) => elStatus.textContent = s;
            const toggleBtn = (btn, on) => btn.classList.toggle("active", on);

            const isNodeOnScreen = (n) => {
                if (!n.graph || !n.graph.canvas) return false;
                const s = n.graph.canvas.ds.scale;
                const pos = n.getBounding();
                const v = n.graph.canvas.ds.offset;
                const w = window.innerWidth, h = window.innerHeight;
                return (pos[0] + pos[2]) * s + v[0] > 0 && pos[0] * s + v[0] < w && (pos[1] + pos[3]) * s + v[1] > 0 && pos[1] * s + v[1] < h;
            };
            const nearBottom = (el) => el.scrollTop + el.clientHeight >= el.scrollHeight - 600;

            const isNsfw = (it) => {
                return it.rating === 'q' || it.rating === 'e' || it.rating === 'questionable' || it.rating === 'explicit';
            };

            const getJSON = async (url) => {
                // Use Proxy
                const proxyUrl = `/danbooru_images/proxy?url=${encodeURIComponent(url)}`;
                console.groupCollapsed("[GenericBrowser] Fetching Proxy", url);
                try {
                    const res = await api.fetchApi(proxyUrl);
                    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
                    const data = await res.json();
                    if (data.error) throw new Error(data.error);
                    console.log("Response:", data);
                    console.groupEnd();
                    return data;
                } catch (e) {
                    console.error("Fetch failed:", e);
                    console.groupEnd();
                    throw e;
                }
            };

            const getFavorites = async () => {
                try {
                    const r = await api.fetchApi("/danbooru_images/favorites");
                    return await r.json();
                } catch (e) { return []; }
            };

            const loadFavs = async () => {
                try {
                    // console.log("[Danbooru] Loading favorites...");
                    const favs = await getFavorites();
                    // favs should be an array of objects
                    favoritesMap = {};
                    if (Array.isArray(favs)) {
                        favs.forEach(f => { if (f.id) favoritesMap[keyId(f.id)] = f; });
                    }
                } catch (e) { favoritesMap = {}; }
            };


            const buildApiUrl = () => {
                const site = SITES[currentSiteKey];
                // Handle cases where site is not ready
                if (!site) return "";

                let u = new URL(site.url);
                u.searchParams.set("page", currentPage);

                // Merge default params
                if (site.params) Object.keys(site.params).forEach(k => u.searchParams.set(k, site.params[k]));

                const rawSearch = elSearchInput.value.trim();
                let tags = rawSearch ? rawSearch.split(" ") : [];

                // Sort
                if (elSort.value) {
                    // Danbooru/Moebooru typically use 'order:score' or 'order:rank' in tags
                    tags.push(`order:${elSort.value}`);
                }

                // Rating
                if (elRating.value) {
                    // Danbooru: rating:g, rating:s, rating:q, rating:e
                    // Moebooru: rating:s, rating:q, rating:e (no g usually)
                    // Gelbooru: rating:safe, rating:questionable, rating:explicit

                    const r = elRating.value;
                    if (site.type === 'gelbooru' || site.url.includes('gelbooru')) {
                        const map = { 'g': 'general', 's': 'sensitive', 'q': 'questionable', 'e': 'explicit' };
                        tags.push(`rating:${map[r] || r}`);
                    } else {
                        tags.push(`rating:${r}`);
                    }
                }

                const finalTags = tags.join(" ");

                if (finalTags) {
                    if (site.tagQuery) {
                        u.searchParams.set(site.tagQuery, finalTags);
                    } else if (site.type === 'gelbooru' || site.url.includes('gelbooru')) {
                        u.searchParams.set("tags", finalTags);
                    } else {
                        // Default 'tags'
                        u.searchParams.set("tags", finalTags);
                    }
                }

                return u.toString();
            };

            // Removed isNsfw function usage for filtering since we rely on tags now. 
            // kept for UI chip only.

            const parseItems = (data) => {
                const site = SITES[currentSiteKey];
                if (!site) return [];

                let list = [];

                if (Array.isArray(data)) {
                    list = data;
                } else if (data.post && Array.isArray(data.post)) {
                    // Konachan/Yandere style sometimes
                    list = data.post;
                } else if (data.posts && Array.isArray(data.posts)) {
                    list = data.posts;
                } else {
                    // console.warn("Unknown data format", data);
                    return [];
                }

                return list.map(it => {
                    // Normalize
                    let mapped = {
                        id: it.id,
                        rating: it.rating,
                        score: it.score && it.score.total ? it.score.total : it.score, // e621 uses score.total
                        image_width: (it.file && it.file.width) ? it.file.width : (it.image_width || it.width),
                        image_height: (it.file && it.file.height) ? it.file.height : (it.image_height || it.height),
                        tag_string: it.tag_string || it.tags,
                    };

                    // e621 tag handling (it.tags is object with arrays)
                    if (it.tags && typeof it.tags === 'object' && !Array.isArray(it.tags) && it.tags.general) {
                        try {
                            // Combine interesting tag categories
                            const cats = ['general', 'character', 'species', 'artist', 'copyright', 'meta'];
                            let allTags = [];
                            cats.forEach(c => { if (it.tags[c]) allTags.push(...it.tags[c]); });
                            mapped.tag_string = allTags.join(" ");
                        } catch (e) { }
                    }

                    // Standard URL mapping
                    if (it.file_url) mapped.url = it.file_url;
                    else if (it.large_file_url) mapped.url = it.large_file_url;
                    else if (it.sample_url) mapped.url = it.sample_url;
                    else if (it.jpeg_url) mapped.url = it.jpeg_url;

                    // e621 URL mapping
                    if (it.file && it.file.url) mapped.url = it.file.url;

                    // Preview mapping
                    if (it.sample_url) mapped.preview_url = it.sample_url;
                    else if (it.preview_url) mapped.preview_url = it.preview_url;
                    else if (it.preview_file_url) mapped.preview_url = it.preview_file_url;

                    // e621 Preview mapping (priority: sample > preview)
                    if (it.sample && it.sample.has && it.sample.url) mapped.preview_url = it.sample.url;
                    else if (it.preview && it.preview.url) mapped.preview_url = it.preview.url;

                    // Fallback
                    if (!mapped.preview_url) mapped.preview_url = mapped.url;

                    // Fallbacks
                    if (!mapped.url && (site.type === 'moebooru' || site.domain?.includes('konachan') || site.domain?.includes('yande'))) {
                        if (it.file_url) mapped.url = it.file_url;
                    }

                    return mapped;
                }).filter(x => {
                    if (!x.url) {
                        console.warn("[GenericBrowser] Item missing URL, skipping:", x.id, x);
                        return false;
                    }
                    // Debug broken images?
                    if (x.url && x.url.includes("undefined")) {
                        console.warn("[GenericBrowser] Item has undefined URL:", x.id, x);
                        return false;
                    }
                    return true;
                });
            };

            const selectItem = (it, cardEl) => {
                console.log("[Danbooru] Selected item:", it.id, it.url);
                if (widget) {
                    widget.value = it.url;
                    if (node.widgets_values) node.widgets_values[0] = it.url;
                }

                const selWidget = node.widgets ? node.widgets.find(w => w.name === "selection_data") : null;
                if (selWidget) {
                    selWidget.value = JSON.stringify(it);
                }

                node.setDirtyCanvas(true);

                elGrid.querySelectorAll(".cg-card").forEach(c => c.classList.remove("selected"));
                if (cardEl) cardEl.classList.add("selected");
            };

            const showModal = (it, cardEl) => {
                modalItem = it; modalCard = cardEl;
                elModalImg.src = it.url;
                elModal.classList.add("show");

                elModalInfoScroll.innerHTML = `
                    <h3>Post #${it.id}</h3>
                    <p>Rating: ${it.rating}</p>
                    <p>Score: ${it.score}</p>
                    <p>Size: ${it.image_width}x${it.image_height}</p>
                    <h4>Tags:</h4>
                    <div style="line-height:1.5">
                        ${(it.tag_string || "").split(" ").map(t => `<span class="cg-tag copy">${t}</span>`).join(" ")}
                    </div>
                `;

                elModalInfoScroll.querySelectorAll(".cg-tag").forEach(t => {
                    t.addEventListener("click", () => {
                        const tag = t.textContent;
                        elSearchInput.value = (elSearchInput.value ? elSearchInput.value + " " : "") + tag;
                        reload(true);
                        hideModal(); // Close modal on search
                    });
                });

                elModalSelect.onclick = () => { selectItem(it, cardEl); hideModal(); };
            };

            const hideModal = () => { elModal.classList.remove("show"); elModalImg.src = ""; };
            elModalClose.addEventListener("click", hideModal);
            elModal.addEventListener("click", (e) => { if (e.target === elModal) hideModal(); });

            const makeCard = (it) => {
                const d = document.createElement("div"); d.className = "cg-card"; d.dataset.id = keyId(it.id);

                // Check if URL is video
                const isVid = it.url && (it.url.toLowerCase().endsWith('.mp4') || it.url.toLowerCase().endsWith('.webm'));

                if (isVid) {
                    const vid = document.createElement("video");
                    vid.className = "cg-img"; // Reuse img class for styling
                    vid.controls = true;
                    vid.muted = true;
                    vid.playsInline = true;
                    vid.preload = "metadata";
                    vid.src = it.preview_url || it.url;
                    d.appendChild(vid);
                } else {
                    const img = document.createElement("img");
                    img.className = "cg-img";
                    img.loading = "lazy";
                    img.src = it.preview_url || it.url || "about:blank";
                    d.appendChild(img);
                }

                const meta = document.createElement("div"); meta.className = "cg-meta";
                const left = document.createElement("div"); left.className = "cg-meta-left";

                if (isNsfw(it)) {
                    const chip = document.createElement("span"); chip.className = "cg-chip nsfw";
                    chip.textContent = (it.rating || "?").toUpperCase();
                    left.appendChild(chip);
                }

                const star = document.createElement("button"); star.className = "cg-star"; star.title = "Favorite";
                const setStar = (on) => { star.classList.toggle("fav", on); star.textContent = on ? "★" : "☆"; };
                setStar(Boolean(favoritesMap[keyId(it.id)]));

                star.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    const isFav = !!favoritesMap[keyId(it.id)];
                    const action = isFav ? "remove" : "add";

                    try {
                        const resp = await api.fetchApi("/danbooru_images/favorites", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ item: it, action: action })
                        });
                        const data = await resp.json();
                        if (data.status === "added") { favoritesMap[keyId(it.id)] = it; setStar(true); }
                        else if (data.status === "removed") { delete favoritesMap[keyId(it.id)]; setStar(false); if (favoritesOnly) reload(true); }
                    } catch (err) { console.error(err); }
                });

                const open = document.createElement("a"); open.className = "cg-open";
                open.href = `https://danbooru.donmai.us/posts/${it.id}`;
                open.target = "_blank"; open.textContent = "Open ↗";
                open.addEventListener("click", (e) => e.stopPropagation());

                const right = document.createElement("div"); right.style.cssText = "display:flex;align-items:center;gap:8px";
                right.appendChild(star);
                right.appendChild(open);
                meta.appendChild(left); meta.appendChild(right); d.appendChild(meta);

                d.addEventListener("click", () => showModal(it, d));
                requestAnimationFrame(() => d.classList.add("show"));
                return d;
            };

            const appendGrid = (items) => {
                const seen = new Set([...elGrid.querySelectorAll(".cg-card")].map((c) => c.dataset.id));
                let added = 0;
                for (const it of items) {
                    const id = keyId(it.id);
                    if (!seen.has(id)) {
                        elGrid.appendChild(makeCard(it));
                        seen.add(id);
                        added++;
                    }
                }
                console.log(`[GenericBrowser] Appended ${added} new cards`);
            };

            const loadMore = async (force = false) => {
                console.log("[Danbooru] loadMore check:", { force, renderEnabled, inView, loading, hasMore });
                if (!renderEnabled || (!inView && !force) || loading || !hasMore) {
                    console.log("[Danbooru] loadMore skipped");
                    return;
                }
                loading = true; setStatus(`Loading page ${currentPage}...`);
                console.group("[GenericBrowser] loadMore page", currentPage);
                try {
                    if (favoritesOnly) {
                        if (!favoritesArray.length) { await loadFavs(); favoritesArray = Object.values(favoritesMap); }
                        let filtered = favoritesArray.slice();

                        // Client-side filtration for favorites based on Rating dropdown using elRating.value
                        // Map dropdown values to rating strings
                        const rVal = elRating.value; // "", "g", "s", "q", "e"
                        if (rVal) {
                            filtered = filtered.filter(i => {
                                // item rating usually 'g', 's', 'q', 'e'
                                // if rVal is 's', checking for 's'.
                                // Some sites use 'safe', 'questionable'.
                                // This is basic matching.
                                return (i.rating && i.rating.startsWith(rVal));
                            });
                        }

                        const termVal = elSearchInput.value.trim();
                        if (termVal) {
                            const terms = termVal.toLowerCase().split(" ");
                            filtered = filtered.filter(i => {
                                const t = (i.tag_string || "").toLowerCase();
                                return terms.every(term => t.includes(term));
                            });
                        }

                        const slice = filtered.slice(favOffset, favOffset + 50);
                        appendGrid(slice); favOffset += 50; hasMore = favOffset < filtered.length;
                        setStatus(hasMore ? `Loaded ${slice.length}` : "End");
                    } else {
                        const url = buildApiUrl();

                        // Fetch via proxy
                        const rawData = await getJSON(url);

                        // Parse
                        let items = parseItems(rawData);
                        console.log(`Parsed ${items.length} items`);

                        appendGrid(items);

                        // Check hasMore - primitive check if we got roughly the limit
                        const limit = SITES[currentSiteKey].params.limit || 20;
                        hasMore = items.length > 0; // If we got 0 items, likely end

                        // Some APIs give metadata, but it varies wildly. 
                        // Simple "empty list = done" is safest for generic support.

                        if (hasMore) currentPage++;
                        setStatus(hasMore ? `Loaded ${items.length} (page ${currentPage - 1})` : "End");
                    }
                } catch (e) {
                    hasMore = false;
                    setStatus(`Error: ${e.message}`);
                    console.error(e);
                }
                finally {
                    loading = false;
                    console.groupEnd();
                }
            };

            const reload = async (resetScroll) => {
                console.log("[Danbooru] reload() called, resetScroll:", resetScroll);
                // logic: if we are trying to reload but not in view, maybe we should skip?
                // But if user just typed search, they want results.
                // Let's force renderEnabled verification but maybe relax inView if it's manual trigger?

                if (!renderEnabled) {
                    console.warn("[Danbooru] Reload skipped because render disabled");
                    return;
                }

                loading = true; setStatus("Reloading...");
                elGrid.replaceChildren(); currentPage = 1; favOffset = 0; favoritesArray = []; hasMore = true;
                if (resetScroll) elScroll.scrollTop = 0;
                await loadFavs(); favoritesArray = Object.values(favoritesMap);
                loading = false;

                // Allow one forced load even if not strictly "inView" by the intersection observer yet
                // because the observer might be slow on init.
                await loadMore(true);
            };

            const setRenderState = (on) => {
                renderEnabled = on; cg.display_on = on;
                elBtnRender.classList.toggle("cg-render-on", on); elBtnRender.classList.toggle("cg-render-off", !on);
                elBtnRender.textContent = on ? "Display: ON" : "Display: OFF";
                elScroll.classList.toggle("paused", !on); root.querySelector(".cg-foot").classList.toggle("paused", !on);
                if (on) reload(true);
            };

            // Viewport watcher
            let _viewRAF = 0;
            const watchView = () => {
                const now = isNodeOnScreen(node);
                if (now !== inView) {
                    inView = now;
                    console.log("[Danbooru] Visibility change:", inView);
                    if (inView && renderEnabled && !cg.has_loaded_once) {
                        cg.has_loaded_once = true;
                        reload(true);
                    }
                }
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

            // Event listeners
            elBtnSearch.addEventListener("click", () => reload(true));
            elBtnRefresh.addEventListener("click", () => reload(true));
            elSearchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") reload(true); });
            // elBtnNsfw removed
            elBtnFavOnly.addEventListener("click", () => { favoritesOnly = !favoritesOnly; toggleBtn(elBtnFavOnly, favoritesOnly); reload(true); });
            elBtnRender.addEventListener("click", () => setRenderState(!renderEnabled));

            // Resize
            const ro = new ResizeObserver(() => {
                const w = elScroll.clientWidth || 900;
                const cols = Math.max(2, Math.floor(w / 200));
                elGrid.style.setProperty("--cols", cols);
            });
            ro.observe(elScroll);

            node.onRemoved = function () { try { cancelAnimationFrame(_viewRAF); io.disconnect(); ro.disconnect(); } catch { } };

            // Initialize
            toggleBtn(elBtnFavOnly, favoritesOnly);

            // Set initial sort/rating if needed from state?
            // For now default.

            setRenderState(cg.display_on !== false);

            // Force initial load check shortly after creation
            setTimeout(() => {
                // Load info
                loadSites().then(() => {
                    if (renderEnabled && !cg.has_loaded_once) {
                        console.log("[GenericBrowser] Force initial load...");
                        cg.has_loaded_once = true;
                        reload(true);
                    }
                });
            }, 100);

            return w; // RETURN WIDGET
        };
    },
});
